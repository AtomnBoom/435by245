import pytest
import asyncio
from src.aegis.core.event_bus import LocalEventBus

@pytest.mark.asyncio
async def test_event_bus_delivery():
    """Тест: проверяем, что подписчик успешно получает отправленное сообщение."""
    bus = LocalEventBus()
    test_data = {"status": "success", "file": "report.docx"}
    received_events = []

    # Создаем асинхронную функцию для нашего подписчика
    async def subscriber_task():
        async for event in bus.subscribe("task.complete"):
            received_events.append(event)
            break # Выходим из цикла после получения первого сообщения, чтобы тест завершился

    # Запускаем подписчика "в фоне" как параллельную задачу
    sub_future = asyncio.create_task(subscriber_task())
    
    # Даем Python микросекунду, чтобы подписчик успел зарегистрироваться на шине
    await asyncio.sleep(0.001)

    # Публикуем событие на шину
    await bus.publish("task.complete", test_data)

    # Ждем завершения фоновой задачи с таймаутом в 2 секунды
    await asyncio.wait_for(sub_future, timeout=2.0)

    # Проверяем результаты
    assert len(received_events) == 1
    assert received_events[0]["file"] == "report.docx"
