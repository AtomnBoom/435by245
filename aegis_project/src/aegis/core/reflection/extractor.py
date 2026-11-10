import json
from datetime import datetime
from typing import Any, Dict, Optional
from src.aegis.contracts.llm import AbstractLLM
from src.aegis.core.reflection.trajectory import Trajectory
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

class PatternExtractor:
    """
    Экстрактор квантов опыта контура самообучения.
    Анализирует траекторию задачи через qwen3:8b, извлекает правила-паттерны
    и депонирует их в базу данных долгосрочной памяти.
    """
    def __init__(self, llm_router: Any, l1_store: SqliteMemoryStore) -> None:
        # Принимаем роутер моделей и базу данных L1
        self.router = llm_router
        self.l1_store = l1_store

    async def extract_and_save(self, trajectory: Trajectory) -> Optional[Dict[str, Any]]:
        """
        Анализирует ошибки и ручные правки человека в траектории,
        формирует квант опыта через ИИ и сохраняет его в SQLite.
        """
        # Если ручных правок человека не было — модель отработала идеально, извлекать опыт не из чего
        if not trajectory.human_diffs:
            return None

        # Формируем жесткий промпт рефлексии для извлечения опыта
        reflection_prompt = (
            f"Ты — контур рефлексии и самообучения ядра Aegis. Проанализируй траекторию задачи.\n"
            f"Исходный запрос пользователя: '{trajectory.prompt}'\n"
            f"Тип документа: '{trajectory.document_type}'\n"
            f"Ручные правки, которые человек внес за ИИ (JSON Patch): {json.dumps(trajectory.human_diffs, ensure_ascii=False)}\n\n"
            f"Сформулируй строго ОДНО правило в формате JSON, которое предотвратит эти правки человека в будущем. "
            f"Верни строго валидный JSON-объект со следующими текстовыми полями:\n"
            f"{{\n"
            f"  \"task_signature\": \"краткий текстовый маркер темы (например, docx.gost_style)\",\n"
            f"  \"error_analysis\": \"в чем ошибся робот, что именно переписывал человек\",\n"
            f"  \"rule\": \"четкое инженерное правило-инструкция на будущее\"\n"
            f"}}"
        )

        try:
            # Запрашиваем квант опыта у qwen3:8b в строгом json-режиме
            raw_pattern = await self.router.route_and_generate(reflection_prompt, task_type="light", json_mode=True)
            pattern_data = json.loads(raw_pattern)

            # Генерируем уникальный ID для кванта опыта
            import time
            pattern_id = f"pat_{int(time.time() * 1000)}"
            timestamp = datetime.utcnow().isoformat()
            
            # Атомарно записываем извлеченный опыт в реляционную таблицу SQLite
            with self.l1_store._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO learned_patterns (id, task_signature, pattern_json, success_count, last_used_at)
                    VALUES (?, ?, ?, 1, ?)
                    """,
                    (pattern_id, pattern_data.get("task_signature", "general"), json.dumps(pattern_data, ensure_ascii=False), timestamp)
                )
                conn.commit()

            return pattern_data
        except Exception as e:
            # Если ИИ выдал битый JSON — контур рефлексии безопасно изолирует ошибку
            print(f"⚠️ Сбой извлечения кванта опыта: {str(e)}")
            return None
