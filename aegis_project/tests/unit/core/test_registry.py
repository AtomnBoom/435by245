import pytest
from src.aegis.core.registry import (
    CapabilityRegistry, 
    MissingCapabilityError, 
    AmbiguousCapabilityError
)
from src.aegis.contracts.llm import AbstractLLM

# Создаем два фейковых (игрушечных) класса, чтобы проверить работу реестра
class FakeOllamaLLM:
    CONTRACT_VERSION = "1.0"
    async def generate(self, prompt, **kwargs): return "ollama"
    async def embed(self, texts, **kwargs): return [[0.0]]

class FakeVllmLLM:
    CONTRACT_VERSION = "1.0"
    async def generate(self, prompt, **kwargs): return "vllm"
    async def embed(self, texts, **kwargs): return [[0.0]]

def test_registry_success_flow():
    """Тест: проверяем, что прибор успешно регистрируется и выдается системой."""
    registry = CapabilityRegistry()
    fake_ollama = FakeOllamaLLM()
    
    # Регистрируем фейковую Ollama как поставщика контракта AbstractLLM
    registry.register("llm.ollama", fake_ollama, provides=[AbstractLLM])
    
    # Просим реестр выдать нам прибор для AbstractLLM
    resolved = registry.resolve(AbstractLLM)
    
    assert resolved == fake_ollama

def test_registry_missing_error():
    """Тест: проверяем, что если прибора нет, система выдает правильную ошибку."""
    registry = CapabilityRegistry()
    
    # Ничего не регистрируем и сразу просим прибор
    with pytest.raises(MissingCapabilityError):
        registry.resolve(AbstractLLM)

def test_registry_ambiguous_error():
    """Тест: проверяем защиту от ситуации, когда зарегистрировано два одинаковых прибора."""
    registry = CapabilityRegistry()
    
    # Регистрируем сразу два разных прибора на один и тот же контракт
    registry.register("llm.ollama", FakeOllamaLLM(), provides=[AbstractLLM])
    registry.register("llm.vllm", FakeVllmLLM(), provides=[AbstractLLM])
    
    # Система должна выдать ошибку двусмысленности
    with pytest.raises(AmbiguousCapabilityError):
        registry.resolve(AbstractLLM)
