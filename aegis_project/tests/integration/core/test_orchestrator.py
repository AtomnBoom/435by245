import pytest
import os
import shutil
from src.aegis.core.fsm import TaskFSM, State
from src.aegis.core.router import LLMRouter
from src.aegis.core.l0_logger import L0RawLogger
from src.aegis.core.validators import IRValidator
from src.aegis.core.orchestrator import Orchestrator
from src.aegis.skills.office.engine import OfficeEngine
from src.aegis.skills.office.docx_compiler import DocxCompiler
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore
from src.aegis.core.registry import CapabilityRegistry

# Игрушечный ИИ-адаптер, который возвращает предсказуемый валидный JSON для теста
class OrchestratorMockLLM:
    CONTRACT_VERSION = "1.0"
    async def generate(self, prompt: str, **kwargs) -> str:
        import json
        if "системный планировщик" in prompt:
            # Имитируем стейт PLANNING: отдаем костяк JSON-IR
            return json.dumps({
                "schema_version": "1.0",
                "document_type": "docx",
                "metadata": {"title": "Тест", "author": "Тестер"},
                "blocks": []
            })
        else:
            # Имитируем стейт GENERATING: отдаем массив блоков
            return json.dumps([
                {"type": "heading", "level": 1, "text": "Введение"},
                {"type": "paragraph", "text": "Текст параграфа."}
            ])

@pytest.fixture
def orchestrator_setup():
    """Фикстура собирает весь контур Оркестратора во временных папках."""
    test_dir = "./data/test_orchestrator"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        
    db_path = os.path.join(test_dir, "l1.db")
    log_path = os.path.join(test_dir, "l0.jsonl")
    migration_path = "./src/aegis/adapters/memory/migrations/001_initial.sql"
    schema_path = "./src/aegis/contracts/schemas/document_ir.json"

    # Инициализируем инфраструктуру
    fsm = TaskFSM()
    mock_llm = OrchestratorMockLLM()
    router = LLMRouter(llm_adapter=mock_llm, memory_limit_mb=1.0)
    l0_logger = L0RawLogger(log_path=log_path)
    l1_store = SqliteMemoryStore(db_path=db_path, migration_path=migration_path)
    ir_validator = IRValidator(schema_path=schema_path)
    
    # Собираем офисный движок через реестр
    registry = CapabilityRegistry()
    registry.register("office.docx", DocxCompiler(), provides=[])
    office_engine = OfficeEngine(registry=registry)

    orchestrator = Orchestrator(
        fsm=fsm, router=router, l0_logger=l0_logger,
        l1_store=l1_store, ir_validator=ir_validator, office_engine=office_engine
    )

    yield orchestrator

    if os.path.exists(test_dir):
        try:
            shutil.rmtree(test_dir)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_orchestrator_full_successful_cycle(orchestrator_setup):
    """Интеграционный тест: Проверяем сквозной проход задачи через Оркестратор."""
    orchestrator = orchestrator_setup
    
    # Запускаем задачу на автоматическое написание отчета
    result = await orchestrator.run_task(
        doc_id="task_abc",
        user_prompt="Напиши технический отчет по программированию ядра",
        doc_type="docx"
    )

    # Проверяем результаты
    assert result["status"] == "success"
    assert "version_id" in result
    assert result["bytes"][:4] == b"PK\x03\x04" # Проверяем, что на выходе получили готовый бинарник Word!
    assert orchestrator.fsm.current_state == State.DONE # Автомат обязан дойти до финальной победной точки!
