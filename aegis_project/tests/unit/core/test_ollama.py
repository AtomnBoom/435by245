import pytest
import httpx
from src.aegis.adapters.llm.ollama import OllamaAdapter

@pytest.mark.asyncio
async def test_ollama_adapter_generate_payload(respx_mock):
    """Тест: проверяем корректность сборки JSON-запроса к Ollama API."""
    # respx_mock автоматически перехватывает сетевые запросы httpx и подкладывает фейковый ответ
    ollama_url = "http://localhost:11434/api/generate"
    respx_mock.post(ollama_url).mock(return_value=httpx.Response(200, json={"response": "Привет, Инженер!"}))

    adapter = OllamaAdapter()
    
    # Делаем вызов генерации
    response_text = await adapter.generate(prompt="Привет", model="qwen3:8b", json_mode=True)
    
    # 1. Проверяем, что адаптер правильно прочитал текстовый ответ
    assert response_text == "Привет, Инженер!"
    
    # 2. Проверяем датчики: был ли запрос отправлен на правильный URL
    assert respx_mock.calls.called
    last_request = respx_mock.calls.last.request
    import json
    request_payload = json.loads(last_request.content)
    
    # Проверяем, что параметры модели и строгого формата встали на свои места
    assert request_payload["model"] == "qwen3:8b"
    assert request_payload["format"] == "json"
