import asyncio
from typing import Any, Dict
from src.aegis.core.fsm import TaskFSM, State, Event
from src.aegis.core.router import LLMRouter
from src.aegis.core.l0_logger import L0RawLogger
from src.aegis.core.validators import IRValidator
from src.aegis.skills.office.engine import OfficeEngine
from src.aegis.adapters.memory.sqlite_store import SqliteMemoryStore

class Orchestrator:
    """
    Центральный управляющий оркестратор (дирижёр) системы A.E.G.I.S.
    Связывает FSM, роутер моделей ИИ, логгер L0, СУБД L1 и Офисный движок
    в единый автоматизированный рабочий цикл выполнения задач.
    """
    def __init__(
        self,
        fsm: TaskFSM,
        router: LLMRouter,
        l0_logger: L0RawLogger,
        l1_store: SqliteMemoryStore,
        ir_validator: IRValidator,
        office_engine: OfficeEngine
    ) -> None:
        self.fsm = fsm
        self.router = router
        self.l0_logger = l0_logger
        self.l1_store = l1_store
        self.ir_validator = ir_validator
        self.office_engine = office_engine

    async def run_task(self, doc_id: str, user_prompt: str, doc_type: str) -> Dict[str, Any]:
        """
        Запускает сквозной процесс выполнения задачи: от планирования до сборки файла.
        """
        # Логируем старт задачи в "чёрный ящик" L0
        await self.l0_logger.append("task_start", {"doc_id": doc_id, "prompt": user_prompt, "type": doc_type})
        
        # 1. СТЕЙТ: PLANNING
        self.fsm.transition(Event.START)
        print(f"[{self.fsm.current_state.name}] 🧠 Планирую структуру документа...")
        
        planning_prompt = (
            f"Ты — системный планировщик Aegis. Сформируй структуру документа для задачи: '{user_prompt}'. "
            f"Тип документа: '{doc_type}'. Верни строго валидный JSON-объект, "
            f"соответствующий полям schema_version='1.0', document_type, metadata и пустой массив blocks."
        )
        
        # Запрашиваем структуру у ИИ в строгом json-формате
        raw_plan = await self.router.route_and_generate(planning_prompt, task_type="light", json_mode=True)
        await self.l0_logger.append("ai_plan_response", {"raw_plan": raw_plan})
        
        # Десериализуем базовый план документа
        import json
        doc_ir = json.loads(raw_plan)
        
        # 2. СТЕЙТ: GENERATING
        self.fsm.transition(Event.PLAN_READY)
        print(f"[{self.fsm.current_state.name}] ✍️ Генерирую контентное наполнение блоков...")
        
        generation_prompt = (
            f"Напиши содержательную текстовую часть для документа на тему: '{user_prompt}'. "
            f"Верни блоки для массива 'blocks' в формате JSON. Например: "
            f"[{{\"type\": \"heading\", \"level\": 1, \"text\": \"Введение\"}}, "
            f"{{\"type\": \"paragraph\", \"text\": \"Основной текст...\"}}]"
        )
        
        # Модель генерирует содержательные блоки
        raw_blocks = await self.router.route_and_generate(generation_prompt, task_type="heavy", json_mode=True)
        await self.l0_logger.append("ai_blocks_response", {"raw_blocks": raw_blocks})
        
        # Укомплектовываем блоки внутрь структуры документа
        doc_ir["blocks"] = json.loads(raw_blocks)
        
        # 3. СТЕЙТ: VALIDATING
        self.fsm.transition(Event.IR_READY)
        print(f"[{self.fsm.current_state.name}] 🔍 Запускаю проверку JSON-схемы и стандартов верстки...")
        
        try:
            # Проверяем документ по нашей строгой JSON-схеме контрактов
            self.ir_validator.validate(doc_ir)
            
            # Сохраняем успешную JSON-версию в базу данных L1 SQLite
            version_id = await self.l1_store.save_document_version(doc_id=doc_id, ir=doc_ir, parent_version=None)
            
            # Передаем JSON-IR на компиляцию в Офисный Фасад для сборки бинарного файла
            file_bytes = self.office_engine.compile(doc_ir)
            
            # Если это Word-документ, дополнительно прогоняем его через встроенный XPath-валидатор ГОСТа
            if doc_type == "docx":
                from src.aegis.skills.office.docx_compiler import DocxCompiler
                compiler_validator = DocxCompiler()
                violations = compiler_validator.validate_xml_gost(file_bytes)
                if violations:
                    raise ValueError(f"XPath Валидатор обнаружил нарушения ГОСТа: {violations}")

            # Если все проверки пройдены — переводим автомат в финальный стейт
            self.fsm.transition(Event.VALIDATION_PASSED)
            print(f"[{self.fsm.current_state.name}] 🎉 Документ успешно собран и проверен!")
            
            await self.l0_logger.append("task_success", {"doc_id": doc_id, "version_id": version_id})
            return {"status": "success", "version_id": version_id, "bytes": file_bytes, "ir": doc_ir}
            
        except Exception as e:
            # Если валидация рухнула, переводим автомат в контур починки (REPAIRING)
            self.fsm.transition(Event.VALIDATION_FAILED)
            print(f"[{self.fsm.current_state.name}] ❌ Обнаружена ошибка: {str(e)}. Перехожу к обработке бага.")
            await self.l0_logger.append("task_failed", {"doc_id": doc_id, "error": str(e)})
            return {"status": "failed", "error": str(e), "ir": doc_ir}
