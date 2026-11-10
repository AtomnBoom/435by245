import pytest
import os
from src.aegis.core.l0_logger import L0RawLogger

@pytest.mark.asyncio
async def test_l0_logger_lifecycle():
    """Тест: проверяем дозапись в "черный ящик" L0 и чтение хвоста лога."""
    test_log_path = "./data/test_logs/l0_test.jsonl"
    
    # Если старый тестовый файл остался от прошлых запусков — удаляем его
    if os.path.exists(test_log_path):
        os.remove(test_log_path)

    # 1. Инициализируем наш логгер
    logger = L0RawLogger(log_path=test_log_path)

    # 2. Пишем первое событие (например, запрос к ИИ)
    event_1 = {"prompt": "Напиши введение для диплома", "model": "qwen2.5:7b"}
    hash_1 = await logger.append(event_type="llm_request", payload=event_1)

    # Проверяем, что файл создался физически
    assert os.path.exists(test_log_path)
    assert len(hash_1) == 64 # Хэш sha256 должен быть длиной ровно 64 символа

    # 3. Пишем второе событие (например, ошибку программной верстки)
    event_2 = {"line": 15, "error": "Line spacing is not 1.5"}
    hash_2 = await logger.append(event_type="gost_error", payload=event_2)

    # 4. Читаем лог с диска и проверяем структуру
    logs = await logger.tail(n=2)
    
    assert len(logs) == 2
    assert logs[0]["event_type"] == "llm_request"
    assert logs[0]["payload"]["model"] == "qwen2.5:7b"
    assert logs[0]["payload_hash"] == hash_1

    assert logs[1]["event_type"] == "gost_error"
    assert logs[1]["payload"]["error"] == "Line spacing is not 1.5"
    assert logs[1]["payload_hash"] == hash_2

    # Прибираем за собой тестовый файл
    if os.path.exists(test_log_path):
        os.remove(test_log_path)
