from typing import Protocol, Any, List, Dict

class AbstractVectorStore(Protocol):
    """
    Контракт для локальной векторной памяти (L2).
    Определяет, как компоненты Джарвиса сохраняют и ищут тексты по их смысловым эмбеддингам.
    """
    CONTRACT_VERSION: str = "1.0"

    async def add_documents(self, collection_name: str, documents: List[str], ids: List[str], embeddings: List[List[float]]) -> None:
        """Сохранить список текстов и их векторов в коллекцию."""
        ...

    async def query_similarity(self, collection_name: str, query_embedding: List[float], max_results: int = 3) -> List[Dict[str, Any]]:
        """Найти наиболее похожие по смыслу тексты на основе вектора запроса."""
        ...
