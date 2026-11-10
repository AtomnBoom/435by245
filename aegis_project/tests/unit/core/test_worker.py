import pytest
import asyncio
from src.aegis.core.event_bus import LocalEventBus
from src.aegis.core.reflection.worker import ReflectionWorker
from src.aegis.core.reflection.trajectory import Trajectory

# Игрушечные заглушки для быстрой изоляции теста
class FakeCollector:
    async def collect(self, task_id, user_prompt, doc_type):
        return Trajectory(task_id, user_prompt, doc_type, {}, [], [])

class FakeExtractor:
    def __init__(self):
        self.called = False
    async def extract_and_save(self, trajectory):
        self.called = True

@pytest.mark.asyncio
async def test_reflection_worker_trigger():
    """Тест: Проверяем, что фоновый воркер перехватывает событие из Шины и запускает рефлексию."""
    bus = LocalEventBus()
    collector = FakeCollector()
    extractor = FakeExtractor()
    
    # Инициализируем и запускаем воркер
    worker = ReflectionWorker(event_bus=bus, collector=collector, extractor=extractor)
    await worker.start()
    
    # Даем микропаузу для старта фонового цикла
    await asyncio.sleep(0.001)
    
    # Симулируем, что Оркестратор выкинул в шину новость о завершении задачи
    payload = {"task_id": "task_999", "prompt": "Тестовый промпт", "doc_type": "docx"}
    await bus.publish("task.done", payload)
    
    # Даем процессору микросекунду выполнить фоновый таск воркера
    await asyncio.sleep(0.001)
    
    # Проверяем датчик: экстрактор опыта обязан был сработать в фоне!
    assert extractor.called is True
    
    # Останавливаем воркер
    worker.stop()
