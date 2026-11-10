import json
import sqlite3
from dataclasses import dataclass, asdict
from typing import Any, List, Optional

@dataclass
class Trajectory:
    """Структурированная траектория выполнения задачи для последующего анализа ИИ."""
    task_id: str
    prompt: str
    document_type: str
    final_ir: dict
    validation_errors: List[str]
    human_diffs: List[dict]

class TrajectoryCollector:
    """
    Компонент контура рефлексии.
    Извлекает из долгосрочной памяти SQLite и логов L0 полную историю выполнения задачи
    для формирования квантов опыта самообучения.
    """
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def collect(self, task_id: str, user_prompt: str, doc_type: str) -> Trajectory:
        """
        Собирает траекторию задачи по её уникальному идентификатору (doc_id / task_id).
        """
        final_ir = {}
        validation_errors = []
        human_diffs = []

        with self._get_connection() as conn:
            # 1. Извлекаем самое последнее (финальное) состояние JSON-IR документа
            row_version = conn.execute(
                """
                SELECT ir_json FROM document_versions 
                WHERE doc_id = ? 
                ORDER BY created_at DESC LIMIT 1
                """,
                (task_id,)
            ).fetchone()
            
            if row_version:
                final_ir = json.loads(row_version["ir_json"])

            # 2. Извлекаем все ручные правки пользователя (diff-логи) для этой задачи
            rows_diffs = conn.execute(
                """
                SELECT diff_json FROM modification_log 
                WHERE doc_id = ? AND source = 'human'
                ORDER BY created_at ASC
                """,
                (task_id,)
            ).fetchall()
            
            for row in rows_diffs:
                # Распаковываем массив операций патча (JSON Patch)
                diff_data = json.loads(row["diff_json"])
                if isinstance(diff_data, list):
                    human_diffs.extend(diff_data)
                else:
                    human_diffs.append(diff_data)

        # Возвращаем укомплектованный датакласс траектории
        return Trajectory(
            task_id=task_id,
            prompt=user_prompt,
            document_type=doc_type,
            final_ir=final_ir,
            validation_errors=validation_errors,  # Будет наполняться оркестратором при сбоях
            human_diffs=human_diffs
        )
