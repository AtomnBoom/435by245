import os
import chromadb
from typing import List, Dict, Any
from src.aegis.contracts.vector import AbstractVectorStore

class LocalChromaStore(AbstractVectorStore):
    """
    Реализация векторной памяти L2 на базе СУБД ChromaDB.
    Работает локально на диске компьютера, сохраняя чанки документов и их смысловые отпечатки.
    """
    def __init__(self, persist_directory: str) -> None:
        self.persist_directory = persist_directory
        # Создаем папку для хранения индексов, если её нет
        os.makedirs(self.persist_directory, exist_ok=True)
        # Инициализируем локальный клиент ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)

    async def add_documents(self, collection_name: str, documents: List[str], ids: List[str], embeddings: List[List[float]]) -> None:
        """Записывает тексты и готовые эмбеддинги в базу данных."""
        # Получаем или создаем коллекцию (таблицу) в ChromaDB
        collection = self.client.get_or_create_collection(name=collection_name)
        
        # Добавляем данные атомарно
        collection.add(
            documents=documents,
            ids=ids,
            embeddings=embeddings
        )

    async def query_similarity(self, collection_name: str, query_embedding: List[float], max_results: int = 3) -> List[Dict[str, Any]]:
        """Ищет в базе тексты, математически ближайшие к смысловому вектору запроса."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            return []

        # Выполняем векторный поиск (косинусное сходство расстояний)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results
        )

        formatted_results = []
        # Превращаем сырой ответ ChromaDB в удобный плоский список Python-словарей
        if results and results["documents"] and results["documents"][0]:
            for idx in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][idx],
                    "text": results["documents"][0][idx],
                    "distance": results["distances"][0][idx] if "distances" in results and results["distances"] else 0.0
                })
        return formatted_results
