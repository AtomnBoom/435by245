from typing import Protocol, Any, Literal

class AbstractMemoryStore(Protocol):
    """
    Контракт для структурированной памяти L1.
    Определяет, как компоненты Джарвиса работают с базой данных версий и опыта.
    """
    CONTRACT_VERSION: str = "1.0"

    async def save_document_version(self, doc_id: str, ir: dict[str, Any], parent_version: str | None) -> str:
        """Сохранить новую JSON-версию документа в историю."""
        ...

    async def get_latest(self, doc_id: str) -> dict[str, Any] | None:
        """Получить самую свежую версию документа по его ID."""
        ...

    async def log_modification(
        self, 
        doc_id: str, 
        from_version: str, 
        to_version: str, 
        diff: list[dict[str, Any]], 
        source: Literal["agent", "human"]
    ) -> None:
        """Записать diff-лог точечных изменений документа."""
        ...
