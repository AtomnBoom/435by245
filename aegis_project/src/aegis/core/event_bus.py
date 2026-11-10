import asyncio
from typing import Any, AsyncIterator
from src.aegis.contracts.event_bus import AbstractEventBus

class LocalEventBus(AbstractEventBus):
    """
    Локальная шина событий, работающая внутри оперативной памяти компьютера.
    Использует очереди asyncio.Queue для мгновенной передачи сообщений между модулями.
    """
    def __init__(self) -> None:
        # Словарь, где ключ — тема, а значение — список очередей подписчиков
        self._subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Отправляет сообщение всем, кто подписан на эту тему."""
        # Если на эту тему никто не подписан, просто ничего не делаем
        if topic not in self._subscribers:
            return

        # Делаем копию сообщения, чтобы подписчики случайно не испортили данные друг другу
        message = payload.copy()

        # Рассылаем сообщение в очередь каждому подписчику
        for queue in self._subscribers[topic]:
            await queue.put(message)

    async def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        """Создает подписку на тему и ждет новые сообщения."""
        # Создаем личную асинхронную очередь для этого конкретного подписчика
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        # Если темы еще нет в словаре, создаем для нее пустой список
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        # Добавляем очередь подписчика в список
        self._subscribers[topic].append(queue)

        try:
            # Запускаем бесконечный цикл ожидания сообщений
            while True:
                # await заставляет программу "заснуть" здесь, пока в очереди не появится сообщение.
                # Это не грузит процессор компьютера!
                event = await queue.get()
                yield event
        finally:
            # Если подписчик решил отключиться, аккуратно удаляем его очередь из списка
            if topic in self._subscribers and queue in self._subscribers[topic]:
                self._subscribers[topic].remove(queue)
