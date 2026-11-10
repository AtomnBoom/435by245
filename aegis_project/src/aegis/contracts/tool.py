from typing import Protocol, Any

class AbstractTool(Protocol):
    """
    Универсальный контракт для всех подключаемых инструментов и скиллов.
    Каждое умение (например, веб-поиск) обязано его реализовать.
    """
    CONTRACT_VERSION: str = "1.0"

    @property
    def name(self) -> str:
        """Уникальное имя инструмента, по которому его вызывает ядро."""
        ...

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Выполнение действия инструмента. 
        """
        ...
