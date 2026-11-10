import pytest
from src.aegis.core.registry import CapabilityRegistry, MissingCapabilityError
from src.aegis.skills.office.engine import OfficeEngine

# Создаем два игрушечных (фейковых) компилятора для быстрой проверки логики фасада
class FakeDocxCompiler:
    def compile(self, ir: dict): return b"fake_docx_bytes"

class FakeXlsxCompiler:
    def compile(self, ir: dict): return b"fake_xlsx_bytes"

def test_office_engine_routing_success():
    """Тест: Проверяем, что Фасад правильно выбирает компилятор на основе типа документа."""
    # 1. Создаем чистый реестр и регистрируем наши фейковые компиляторы
    registry = CapabilityRegistry()
    fake_docx = FakeDocxCompiler()
    fake_xlsx = FakeXlsxCompiler()
    
    registry.register("office.docx", fake_docx, provides=[])
    registry.register("office.xlsx", fake_xlsx, provides=[])

    # 2. Инициализируем наш Единый Офисный Двигатель
    engine = OfficeEngine(registry=registry)

    # 3. Проверяем сборку Word
    word_ir = {"document_type": "docx", "blocks": []}
    word_result = engine.compile(word_ir)
    assert word_result == b"fake_docx_bytes"

    # 4. Проверяем сборку Excel
    excel_ir = {"document_type": "xlsx", "blocks": []}
    excel_result = engine.compile(excel_ir)
    assert excel_result == b"fake_xlsx_bytes"

def test_office_engine_missing_compiler_error():
    """Тест: Если тип документа неизвестен, система должна выдать ошибку MissingCapabilityError."""
    registry = CapabilityRegistry()
    engine = OfficeEngine(registry=registry)
    
    # Передаем неизвестный тип документа pptx, который мы не регистрировали в этом тесте
    unknown_ir = {"document_type": "pptx", "blocks": []}
    
    with pytest.raises(MissingCapabilityError):
        engine.compile(unknown_ir)
