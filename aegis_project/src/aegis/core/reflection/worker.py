import asyncio
from typing import Any
from src.aegis.core.event_bus import LocalEventBus
from src.aegis.core.reflection.trajectory import TrajectoryCollector
from src.aegis.core.reflection.extractor import PatternExtractor

class ReflectionWorker:
    """
    Фоновый асинхронный воркер контура самообучения.
    Слушает Шину событий и запускает процесс рефлексии в фоновом режиме,
    не блокируя основной поток генерации документов.
    """
    def __init__(
        self,
        event_bus: LocalEventBus,
        collector: TrajectoryCollector,
        extractor: PatternExtractor
    ) -> None:
        self.event_bus = event_bus
        self.collector = collector
        self.extractor = extractor
        self._is_running = False

    async def start(self) -> None:
        """Запускает фоновое прослушивание Шины событий."""
        self._is_running = True
        # Запускаем бесконечный цикл обработки в фоне через встроенный механизм задач asyncio
        asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        """Внутренний асинхронный цикл обработки событий task.done."""
        # Подписываемся на тему успешного завершения задач
        async for event in self.event_bus.subscribe("task.done"):
            if not self._is_running:
                break
            
            # Извлекаем метаданные задачи из payload события
            task_id = event.get("task_id")
            user_prompt = event.get("prompt")
            doc_type = event.get("doc_type")
            
            if task_id and user_prompt and doc_type:
                # Запускаем процесс самообучения в изолированном фоновом таске
                asyncio.create_task(self._run_reflection(task_id, user_prompt, doc_type))

    async def _run_reflection(self, task_id: str, user_prompt: str, doc_type: str) -> None:
        """Фоновый метод извлечения опыта."""
        try:
            # 1. Собираем историю задачи
            trajectory = await self.collector.collect(task_id=task_id, user_prompt=user_prompt, doc_type=doc_type)
            
            # 2. Просим ИИ извлечь квант опыта и записать его в SQLite L1
            await self.extractor.extract_and_save(trajectory)
            
        except Exception as e:
            # Сбой рефлексии изолирован! Он никогда не уронит основное приложение и не прервет работу юзера
            print(f"⚠️ Фоновая рефлексия для задачи {task_id} завершилась с ошибкой: {str(e)}")

    def stop(self) -> None:
        """Останавливает воркер рефлексии."""
        self._is_running = False
