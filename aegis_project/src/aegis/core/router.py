import os
import psutil
import httpx
from typing import Any, Dict, List

class AdaptiveRouter:
    def __init__(self, registry: Any):
        self.registry = registry
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    async def _discover_available_models(self) -> Dict[str, List[str]]:
        """Динамически запрашивает список всех скачанных моделей из локальной Ollama без хардкода."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.ollama_host}/api/tags")
            if response.status_code != 200:
                raise RuntimeError("Локальный сервис Ollama недоступен или не отвечает.")
            
            models_data = response.json().get("models", [])
            text_models = []
            embed_models = []
            
            for m in models_data:
                name = m.get("name", "")
                # Разделение пула по сигнатуре назначения на основе метаданных или имени
                if "embed" in name or "bge" in name:
                    embed_models.append(name)
                else:
                    text_models.append(name)
                    
            if not text_models and not embed_models:
                raise ValueError("В локальном пространстве Ollama не обнаружено скачанных моделей.")
                
            return {"text": text_models, "embed": embed_models}

    async def select_best_model(self, task_signature: str) -> str:
        """Автоматически выбирает лучшую модель из физически доступных в системе."""
        discovered = await self._discover_available_models()
        text_pool = discovered.get("text", [])
        
        if not text_pool:
            raise ValueError("Пул доступных текстовых моделей пуст. Скачайте модель через 'ollama run'.")
            
        vm = psutil.virtual_memory()
        available_ram_gb = vm.available / (1024 ** 3)

        # 1. Защита ОЗУ: если памяти критически мало, берем самую компактную по параметрам модель
        if available_ram_gb < 4.0:
            light_models = [m for m in text_pool if "7b" in m or "8b" in m or "3b" in m]
            return light_models[0] if light_models else text_pool[0]

        # 2. Ранжирование по сигнатуре сложной задачи, если пользователь добавит тяжелые веса в будущем
        if task_signature in ["code_repair", "complex_planning", "reflection"]:
            heavy_models = [m for m in text_pool if "14b" in m or "27b" in m or "70b" in m or "coder" in m]
            if heavy_models:
                return heavy_models[-1] if available_ram_gb > 12.0 else heavy_models[0]

        # 3. Базовый сценарий: возвращаем первую доступную текстовую модель
        return text_pool[0]

    async def generate(self, task_signature: str, prompt: str, **kwargs) -> str:
        """Выполняет инференс на динамически найденной модели с последующей автовыгрузкой."""
        selected_model = await self.select_best_model(task_signature)
        
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.1),
                "num_ctx": kwargs.get("num_ctx", 4096)
            },
            "keep_alive": "10s" # Внутренний таймер Ollama: выгрузить через 10 секунд пассивности
        }
        
        if kwargs.get("json_mode", False):
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.ollama_host}/api/generate", json=payload)
            response.raise_for_status()
            text_response = response.json().get("response", "")
            
            # Оптимизация ОЗУ: Принудительный сброс весов модели сразу после генерации
            try:
                await client.post(f"{self.ollama_host}/api/generate", json={"model": selected_model, "keep_alive": "3s"})
            except Exception:
                pass # Игнорируем сбои сети на этапе очистки, keep_alive на 10с сработает как страховка
                
            return text_response

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Динамически находит модель эмбеддингов и выгружает её из ОЗУ сразу после расчета векторов."""
        discovered = await self._discover_available_models()
        embed_pool = discovered.get("embed", [])
        
        if not embed_pool:
            raise ValueError("Модели для генерации векторов (embeddings) не обнаружены.")
            
        selected_embed_model = embed_pool[0]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ollama_host}/api/embed",
                json={
                    "model": selected_embed_model,
                    "input": texts,
                    "keep_alive": "10s"
                }
            )
            response.raise_for_status()
            embeddings = response.json().get("embeddings", [])
            
            # Немедленная очистка памяти после создания эмбеддингов
            try:
                await client.post(f"{self.ollama_host}/api/generate", json={"model": selected_embed_model, "keep_alive": "1s"})
            except Exception:
                pass
                
            return embeddings
