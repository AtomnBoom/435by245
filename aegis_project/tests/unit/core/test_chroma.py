import pytest
import os
import shutil
from src.aegis.adapters.vector.chroma import LocalChromaStore

@pytest.fixture
def temp_chroma_setup():
    """Фикстура для создания изолированной тестовой папки ChromaDB и её зачистки."""
    test_dir = "./data/test_chroma"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    yield test_dir
    
    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_chroma_store_lifecycle(temp_chroma_setup):
    """Тест: Проверяем запись векторов и поиск по сходству в локальной ChromaDB."""
    persist_dir = temp_chroma_setup
    store = LocalChromaStore(persist_directory=persist_dir)
    
    collection_name = "test_collection"
    documents = ["Инженерия и ГОСТ", "Рецепт яблочного пирога"]
    ids = ["id_gost", "id_pie"]
    
    # Два игрушечных эмбеддинга для проверки (ChromaDB принимает любую фиксированную размерность)
    embeddings = [
        [1.0, 0.9, 0.0],  # Вектор про инженерию
        [0.0, 0.1, 1.0]   # Вектор про пирог
    ]

    # 1. Записываем документы и их векторы в базу
    await store.add_documents(collection_name=collection_name, documents=documents, ids=ids, embeddings=embeddings)
    
    # 2. Имитируем поисковый запрос про технику (его вектор близок к первому документу)
    query_vector = [0.9, 0.8, 0.1]
    
    # Ищем совпадения
    matches = await store.query_similarity(collection_name=collection_name, query_embedding=query_vector, max_results=1)
    
    # База должна математически понять, что "Инженерия и ГОСТ" ближе к запросу, чем пирог!
    assert len(matches) == 1
    assert matches[0]["id"] == "id_gost"
    assert "ГОСТ" in matches[0]["text"]
