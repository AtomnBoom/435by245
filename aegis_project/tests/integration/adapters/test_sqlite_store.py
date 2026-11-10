import pytest
import os
import shutil
import time
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

pytestmark = pytest.mark.asyncio

def remove_readonly(func, path, excinfo):
    """Специальный обработчик ошибок для Windows, чтобы принудительно удалять занятые или защищенные файлы."""
    # Даем системе микропаузу освободить файл и пробуем удалить снова
    time.sleep(0.1)
    try:
        os.unlink(path)
    except Exception:
        pass

@pytest.fixture
def temp_db_setup():
    """Фикстура-сценограф. Создает изолированную временную папку и безопасно удаляет её."""
    test_dir = "./data/test_db"
    db_path = os.path.join(test_dir, "test_aegis.db")
    migration_path = "./src/aegis/adapters/memory/migrations/001_initial.sql"
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, onerror=remove_readonly)
        
    yield db_path, migration_path
    
    # Убираем мусор, используя наш безопасный Windows-обработчик
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir, onerror=remove_readonly)

async def test_sqlite_store_lifecycle(temp_db_setup):
    """Тест: Проверяем полный жизненный цикл работы с базой данных L1."""
    db_path, migration_path = temp_db_setup
    
    # 1. Инициализируем хранилище
    store = SqliteMemoryStore(db_path=db_path, migration_path=migration_path)
    
    # Проверяем, что файл базы данных физически появился на диске
    assert os.path.exists(db_path)
    
    # 2. Создаем тестовое промежуточное представление (JSON-IR) документа
    doc_id = "doc_test_123"
    sample_ir = {
        "schema_version": "1.0",
        "document_type": "docx",
        "blocks": [{"type": "paragraph", "text": "Тест Джарвиса"}]
    }
    
    version_id = await store.save_document_version(doc_id=doc_id, ir=sample_ir, parent_version=None)
    
    assert version_id.startswith("ver_")
    
    # 3. Достаем самую свежую версию этого документа из базы данных
    latest_ir = await store.get_latest(doc_id=doc_id)
    
    assert latest_ir is not None
    assert latest_ir["document_type"] == "docx"
    # Исправляем обращение к ключу blocks (в JSON это список, берем первый элемент)
    assert latest_ir["blocks"][0]["text"] == "Тест Джарвиса"

    # 4. Симулируем ручную правку пользователя в WYSIWYG-интерфейсе
    sample_diff = [{"op": "replace", "path": "/blocks/0/text", "value": "Правка человека"}]
    next_version_id = "ver_human_modified_456"
    
    await store.log_modification(
        doc_id=doc_id,
        from_version=version_id,
        to_version=next_version_id,
        diff=sample_diff,
        source="human"
    )
