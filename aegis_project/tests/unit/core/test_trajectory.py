import pytest
import os
import shutil
from src.aegis.core.reflection.trajectory import TrajectoryCollector
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

@pytest.fixture
def temp_reflection_db():
    """Фикстура разворачивает чистую временную базу данных для теста рефлексии."""
    test_dir = "./data/test_reflection"
    db_path = os.path.join(test_dir, "reflection_test.db")
    migration_path = "./src/aegis/adapters/memory/migrations/001_initial.sql"
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    # Инициализируем структуру таблиц через наш рабочий адаптер
    store = SqliteMemoryStore(db_path=db_path, migration_path=migration_path)
    
    yield db_path, store
    
    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_trajectory_collector_success(temp_reflection_db):
    """Тест: проверяем сборку полной истории задачи со всеми ручными правками человека."""
    db_path, store = temp_reflection_db
    
    task_id = "task_reflection_123"
    doc_type = "docx"
    user_prompt = "Создай дипломный проект по архитектуре ИИ"
    
    # 1. Симулируем, что ИИ сохранил базовую версию
    sample_ir = {"document_type": "docx", "blocks": [{"type": "paragraph", "text": "Робот написал текст"}]}
    version_id = await store.save_document_version(doc_id=task_id, ir=sample_ir, parent_version=None)
    
    # 2. Симулируем, что пользователь зашел в WYSIWYG и руками поправил текст (создаем дифф лог)
    human_patch = [{"op": "replace", "path": "/blocks/0/text", "value": "Человек исправил руками"}]
    await store.log_modification(
        doc_id=task_id,
        from_version=version_id,
        to_version="ver_final_999",
        diff=human_patch,
        source="human"
    )
    
    # Симулируем сохранение итоговой версии после правок
    final_ir = {"document_type": "docx", "blocks": [{"type": "paragraph", "text": "Человек исправил руками"}]}
    await store.save_document_version(doc_id=task_id, ir=final_ir, parent_version=version_id)

    # 3. Активируем наш Сборщик траекторий
    collector = TrajectoryCollector(db_path=db_path)
    trajectory = await collector.collect(task_id=task_id, user_prompt=user_prompt, doc_type=doc_type)

    # 4. Проверяем, что сборщик все нашел и склеил правильно
    assert trajectory.task_id == task_id
    assert trajectory.prompt == user_prompt
    assert trajectory.document_type == doc_type
    assert trajectory.final_ir["blocks"][0]["text"] == "Человек исправил руками"
    
    # Сборщик обязан был вытащить ручной патч изменений!
    assert len(trajectory.human_diffs) == 1
    assert trajectory.human_diffs[0]["value"] == "Человек исправил руками"
