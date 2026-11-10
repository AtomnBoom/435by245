import pytest
from typing import Any
from src.aegis.core.router import LLMRouter, InsufficientMemoryError
from src.aegis.contracts.llm import AbstractLLM

# Создаем фейковый адаптер ИИ для проверки роутера без реального запуска Ollama
class FakeLLMAdapter:
    CONTRACT_VERSION = "1.0"
    def __init__(self):
        self.last_model_used = None

    async def generate(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        self.last_model_used = model
        return f"generated_by_{model}"

    async def embed(self, texts: list[str], model: str = "bge-m3") -> list[list[float]]:
        return [[0.0]]

@pytest.mark.asyncio
async def test_router_successful_routing():
    """Тест: Проверяем обычную штатную работу роутера и выбор параметров."""
    fake_llm = FakeLLMAdapter()
    # Указываем лимит в 1 МБ, чтобы тест гарантированно прошел на любом ПК
    router = LLMRouter(llm_adapter=fake_llm, memory_limit_mb=1.0)
    
    # Запускаем легкую задачу
    result = await router.route_and_generate(prompt="Тест", task_type="light")
    
    assert result == "generated_by_qwen3:8b"
    assert fake_llm.last_model_used == "qwen3:8b"

@pytest.mark.asyncio
async def test_router_memory_safety_trigger():
    """Тест: Симулируем критическую нехватку ОЗУ."""
    fake_llm = FakeLLMAdapter()
    # Ставим безумный лимит в 100 000 000 МБ RAM
    router = LLMRouter(llm_adapter=fake_llm, memory_limit_mb=100000000.0)
    
    # Роутер должен поймать перегрузку датчиков и выкинуть InsufficientMemoryError
    with pytest.raises(InsufficientMemoryError):
        await router.route_and_generate(prompt="Тяжелая задача", task_type="heavy")
