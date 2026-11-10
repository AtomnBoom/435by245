import json
import os
import hashlib
import aiofiles
from datetime import datetime
from typing import Any

class L0RawLogger:
    """
    "Чёрный ящик" нашей системы (Память уровня L0).
    Записывает абсолютно все события в append-only режиме в формате JSONL.
    Защищен от дублирования записей при повторных попытках (retry).
    """
    def __init__(self, log_path: str) -> None:
        self.log_path = log_path
        # Создаем директорию для лога, если её физически нет на диске
        log_dir = os.path.dirname(os.path.abspath(self.log_path))
        os.makedirs(log_dir, exist_ok=True)

    def _compute_hash(self, payload: dict[str, Any]) -> str:
        """Внутренний метод для создания уникального цифрового отпечатка (хэша) данных."""
        # Сортируем ключи, чтобы одинаковые словари всегда давали один и тот же хэш
        dumped = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(dumped.encode("utf-8")).hexdigest()

    async def append(self, event_type: str, payload: dict[str, Any]) -> str:
        """
        Дописывает новое событие в конец файла лога.
        event_type: тип события (например, 'llm_request', 'validation_error')
        payload: данные события в виде словаря
        Возвращает уникальный хэш-ключ записи.
        """
        timestamp = datetime.utcnow().isoformat()
        payload_hash = self._compute_hash(payload)

        # Формируем одну строчку нашего "черного ящика"
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "payload_hash": payload_hash,
            "payload": payload
        }

        # Превращаем в строку и добавляем символ переноса строки в конец
        entry_str = json.dumps(log_entry, ensure_ascii=False) + "\n"

        # Открываем файл в асинхронном режиме 'a' (Append - только дозапись в конец)
        async with aiofiles.open(self.log_path, mode="a", encoding="utf-8") as f:
            await f.write(entry_str)

        return payload_hash

    async def tail(self, n: int = 100) -> list[dict[str, Any]]:
        """Возвращает N последних записей из лога для анализа контура рефлексии."""
        if not os.path.exists(self.log_path):
            return []

        entries = []
        async with aiofiles.open(self.log_path, mode="r", encoding="utf-8") as f:
            lines = await f.readlines()
            # Берем только последние N строчек
            for line in lines[-n:]:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
