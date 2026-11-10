import json
import sqlite3
from typing import Any, List

class ExperienceInjector:
    """
    Инжектор опыта контура самообучения A.E.G.I.S.
    Динамически извлекает сохраненные паттерны из SQLite и внедряет
    их в системный промпт ИИ перед запуском генерации.
    """
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def inject_experience(self, base_prompt: str, task_signature: str) -> str:
        """
        Ищет релевантный опыт по сигнатуре задачи и подмешивает его в промпт.
        """
        patterns: List[str] = []

        with self._get_connection() as conn:
            # Ищем все извлеченные правила для данной сигнатуры задачи
            rows = conn.execute(
                """
                SELECT pattern_json FROM learned_patterns 
                WHERE task_signature = ?
                """,
                (task_signature,)
            ).fetchall()

            for row in rows:
                data = json.loads(row["pattern_json"])
                rule = data.get("rule")
                if rule:
                    patterns.append(f"- {rule}")

        # Если опыта по этой теме еще нет — возвращаем базовый промпт без изменений
        if not patterns:
            return base_prompt

        # Формируем интеллектуальную инъекцию опыта
        experience_block = "\n\n## ИЗВЛЕЧЕННЫЙ ОПЫТ СИСТЕМЫ (ОБЯЗАТЕЛЬНО К ИСПОЛНЕНИЮ):\n" + "\n".join(patterns)
        
        # Склеиваем базовую инструкцию с накопленным опытом
        return base_prompt + experience_block
