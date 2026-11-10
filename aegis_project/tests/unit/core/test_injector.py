import pytest
import os
import shutil
import json
from src.aegis.core.reflection.injector import ExperienceInjector
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

@pytest.fixture
def temp_injector_db():
    """Фикстура разворачивает временную БД для теста инжектора правок."""
    test_dir = "./data/test_injector_flow"
    db_path = os.path.join(test_dir, "injector_test.db")
    migration_path = "./src/aegis/adapters/memory/migrations/001_initial.sql"
    
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    store = SqliteMemoryStore(db_path=db_path, migration_path=migration_path)
    yield db_path, store
    
    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_experience_injection_success(temp_injector_db):
    """Тест: проверяем успешное подмешивание опыта в системную инструкцию ИИ."""
    db_path, store = temp_injector_db
    
    task_signature = "docx.gost_style"
    base_prompt = "Ты — офисный компилятор."
    
    # 1. Записываем фейковое правило опыта в SQLite
    import time
    pattern_id = "pat_test_777"
    pattern_payload = {
        "task_signature": task_signature,
        "rule": "Всегда делай левое поле ровно 30мм."
    }
    
    with store._get_connection() as conn:
        conn.execute(
            "INSERT INTO learned_patterns (id, task_signature, pattern_json, last_used_at) VALUES (?, ?, ?, ?)",
            (pattern_id, task_signature, json.dumps(pattern_payload), str(time.time()))
        )
        conn.commit()

    # 2. Инициализируем Инжектор
    injector = ExperienceInjector(db_path=db_path)
    
    # Запускаем инъекцию
    enriched_prompt = await injector.inject_experience(base_prompt=base_prompt, task_signature=task_signature)

    # 3. Проверяем, что базовый промпт обогатился правилом из базы данных L1
    assert enriched_prompt != base_prompt
    assert "ИЗВЛЕЧЕННЫЙ ОПЫТ СИСТЕМЫ" in enriched_prompt
    assert "левое поле ровно 30мм" in enriched_prompt
