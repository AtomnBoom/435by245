import sqlite3
import json
import os
from datetime import datetime
from typing import Any, Literal
from src.aegis.contracts.memory import AbstractMemoryStore

class SqliteMemoryStore(AbstractMemoryStore):
    """
    Реализация структурированной памяти L1 на СУБД SQLite.
    Поддерживает автоматическое развертывание таблиц, хранение версий и аудит правок.
    """
    def __init__(self, db_path: str, migration_path: str) -> None:
        self.db_path = db_path
        self.migration_path = migration_path
        # Автоматически создаем таблицы при первом запуске
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Открывает безопасное соединение с файлом базы данных."""
        conn = sqlite3.connect(self.db_path)
        # Настраиваем базу так, чтобы строки возвращались в виде удобных Python-словарей
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Читает SQL-файл миграции и создает структуру базы данных на диске."""
        # Создаем физические папки для файла БД, если их еще нет на диске
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)
        
        # Читаем наш SQL-скрипт и выполняем его внутри базы
        if os.path.exists(self.migration_path):
            with open(self.migration_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            
            with self._get_connection() as conn:
                conn.executescript(sql_script)
                conn.commit()

    async def save_document_version(self, doc_id: str, ir: dict[str, Any], parent_version: str | None) -> str:
        """Сохраняет новую JSON-версию документа в базу данных."""
        # Генерируем уникальный ID версии на основе текущего времени
        import time
        version_id = f"ver_{int(time.time() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        ir_str = json.dumps(ir, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO document_versions (id, doc_id, parent_version, ir_json, created_at, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (version_id, doc_id, parent_version, ir_str, timestamp, "agent")
            )
            conn.commit()
        return version_id

    async def get_latest(self, doc_id: str) -> dict[str, Any] | None:
        """Возвращает самую свежую JSON-версию документа из истории."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT ir_json FROM document_versions 
                WHERE doc_id = ? 
                ORDER BY created_at DESC LIMIT 1
                """,
                (doc_id,)
            ).fetchone()
            
            if row:
                return json.loads(row["ir_json"])
        return None

    async def log_modification(
        self, 
        doc_id: str, 
        from_version: str, 
        to_version: str, 
        diff: list[dict[str, Any]], 
        source: Literal["agent", "human"]
    ) -> None:
        """Записывает точечные изменения (diff правок) между версиями документа."""
        timestamp = datetime.utcnow().isoformat()
        diff_str = json.dumps(diff, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO modification_log (doc_id, from_version, to_version, diff_json, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (doc_id, from_version, to_version, diff_str, source, timestamp)
            )
            conn.commit()
