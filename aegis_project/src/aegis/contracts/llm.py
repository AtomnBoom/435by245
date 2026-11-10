from typing import Protocol, Any

class AbstractLLM(Protocol):
    """
    Контракт для подключения языковых моделей (LLM) и эмбеддеров.
    Любой адаптер (Ollama, vLLM, API) обязан реализовывать эти методы.
    """
    CONTRACT_VERSION: str = "1.0"

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
        Генерация текстового ответа по промпту.
        """
        ...

    async def embed(self, texts: list[str], model: str = "bge-m3") -> list[list[float]]:
        """
        Получение смысловых векторов (эмбеддингов) для списка текстов.
        """
        ...
