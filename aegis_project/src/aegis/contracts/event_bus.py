from typing import Protocol, AsyncIterator, Any

class AbstractEventBus(Protocol):
    """
    Контракт для Шины событий (Event Bus).
    Определяет, как компоненты Джарвиса публикуют сообщения и подписываются на них.
    """
    CONTRACT_VERSION: str = "1.0"

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """
        Опубликовать событие на шину.
        topic: тема события (например, 'task.complete')
        payload: данные события в виде словаря
        """
        ...

    def subscribe(self, topic: str) -> AsyncIterator[dict[str, Any]]:
        """
        Подписаться на определенную тему.
        Возвращает асинхронный поток сообщений.
        """
        ...
