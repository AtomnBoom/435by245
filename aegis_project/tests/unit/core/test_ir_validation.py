import pytest
from src.aegis.core.validators import IRValidator, IRValidationError

@pytest.fixture
def validator():
    """Фикстура инициализирует валидатор с путем к нашей схеме."""
    schema_path = "./src/aegis/contracts/schemas/document_ir.json"
    return IRValidator(schema_path=schema_path)

def test_validation_valid_docx(validator):
    """Тест: правильный документ для Word должен проходить проверку без ошибок."""
    valid_ir = {
        "schema_version": "1.0",
        "document_type": "docx",
        "metadata": {
          "title": "Реферат по физике",
          "author": "Студент"
        },
        "blocks": [
          {"type": "heading", "level": 1, "text": "Введение"},
          {"type": "paragraph", "text": "Текст первого абзаца."}
        ]
    }
    # Ошибок быть не должно, функция просто отработает до конца
    validator.validate(valid_ir)

def test_validation_invalid_document_type(validator):
    """Тест: если тип документа указан неверно, должна сработать защита."""
    invalid_ir = {
        "schema_version": "1.0",
        "document_type": "unknown_file",  # Такой тип запрещен схемой
        "metadata": {"title": "Тест", "author": "Тестер"},
        "blocks": []
    }
    
    with pytest.raises(IRValidationError):
        validator.validate(invalid_ir)

def test_validation_missing_required_field(validator):
    """Тест: заголовок (heading) обязан содержать уровень level. Если его нет — ловим ошибку."""
    invalid_ir = {
        "schema_version": "1.0",
        "document_type": "docx",
        "metadata": {"title": "Тест", "author": "Тестер"},
        "blocks": [
          {"type": "heading", "text": "Забыли указать уровень заголовка"}
        ]
    }
    
    with pytest.raises(IRValidationError):
        validator.validate(invalid_ir)
