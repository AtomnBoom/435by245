import httpx
from typing import Any, List
from src.aegis.contracts.llm import AbstractLLM

class OllamaAdapter(AbstractLLM):
    """
    Адаптер для подключения локального движка Ollama.
    Связывает систему с моделями qwen3:8b и qwen3-embedding:8b.
    """
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        self.embeddings_url = f"{base_url}/api/embeddings"

    async def generate(
        self, 
        prompt: str, 
        *, 
        model: str | None = None, 
        temperature: float = 0.1, 
        json_mode: bool = False,
        **kwargs: Any
    ) -> str:
        """
        Отправляет промпт локальной модели и возвращает сгенерированный текст.
        Дает модели 10 секунд на генерацию на CPU, после чего ОЗУ автоматически очищается.
        """
        target_model = model if model else "qwen3:8b"
        
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10s",
            "options": {
                "temperature": temperature
            }
        }

        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.generate_url, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Ошибка Ollama API: HTTP {response.status_code} -> {response.text}")
            
            result_json = response.json()
            return result_json.get("response", "")

    async def embed(self, texts: list[str], model: str = "qwen3-embedding:8b") -> list[list[float]]:
        """
        Генерирует смысловые векторы и выгружает модель эмбеддинга через 10 секунд.
        """
        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model": model,
                    "prompt": text,
                    "keep_alive": "10s"
                }
                response = await client.post(self.embeddings_url, json=payload)
                if response.status_code != 200:
                    raise RuntimeError(f"Ошибка Ollama Embeddings API: HTTP {response.status_code}")
                
                result_json = response.json()
                embeddings.append(result_json.get("embedding", []))
        return embeddings
