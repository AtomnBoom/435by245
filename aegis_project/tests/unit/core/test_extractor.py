import pytest
import os
import shutil
import json
from src.aegis.core.reflection.trajectory import Trajectory
from src.aegis.core.reflection.extractor import PatternExtractor
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

# Фейковый роутер, имитирующий идеальный JSON-ответ рефлексии от qwen3:8b
class FakeReflectionRouter:
    async def route_and_generate(self, prompt: str, **kwargs) -> str:
        return json.dumps({
            "task_signature": "docx.diplom_format",
            "error_analysis": "Робот забыл сделать отступ 1.25 см в начале главы",
            "rule": "Всегда начинай заголовки глав диплома строго с новой страницы с абзацным отступом 1.25см."
        })

@pytest.fixture
def temp_extractor_db():
    """Фикстура разворачивает временную БД для теста экстрактора."""
    test_dir = "./data/test_extractor"
    db_path = os.path.join(test_dir, "extractor_test.db")
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
async def test_pattern_extractor_success(temp_extractor_db):
    """Тест: проверяем извлечение кванта опыта и его запись в реляционную таблицу SQLite."""
    db_path, store = temp_extractor_db
    
    # 1. Создаем готовую траекторию задачи с ручной правкой человека
    trajectory = Trajectory(
        task_id="task_000",
        prompt="Напиши главу диплома",
        document_type="docx",
        final_ir={"blocks": []},
        validation_errors=[],
        human_diffs=[{"op": "replace", "path": "/blocks/0/text", "value": "Новая правка"}]
    )

    # 2. Инициализируем Экстрактор опыта
    fake_router = FakeReflectionRouter()
    extractor = PatternExtractor(llm_router=fake_router, l1_store=store)
    
    # Запускаем контур извлечения
    pattern = await extractor.extract_and_save(trajectory)

    # 3. Проверяем, что опыт успешно извлечен и лег в SQL-таблицу
    assert pattern is not None
    assert pattern["task_signature"] == "docx.diplom_format"
    assert "абзацным отступом" in pattern["rule"]

    with store._get_connection() as conn:
        row = conn.execute("SELECT * FROM learned_patterns").fetchone()
        assert row is not None
        assert row["task_signature"] == "docx.diplom_format"
        # Проверяем, что внутри лежит валидная JSON-строка правила
        saved_json = json.loads(row["pattern_json"])
        assert saved_json["rule"] == pattern["rule"]
