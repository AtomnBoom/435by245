import pytest
from src.aegis.skills.office.docx_compiler import DocxCompiler

def test_docx_compiler_gost_success():
    """Тест: Проверяем компиляцию эталонного документа и отсутствие XML-нарушений ГОСТа."""
    compiler = DocxCompiler()
    
    sample_ir = {
        "schema_version": "1.0",
        "document_type": "docx",
        "metadata": {
            "title": "Эталонный отчет",
            "author": "Инженер"
        },
        "blocks": [
            {"type": "heading", "level": 1, "text": "Введение"},
            {"type": "paragraph", "text": "Правильный абзац текста по всем правилам ГОСТа."}
        ]
    }
    
    # 1. Генерируем файл
    docx_bytes = compiler.compile(sample_ir)
    assert len(docx_bytes) > 0
    assert docx_bytes[:4] == b"PK\x03\x04"

    # 2. Проверяем XML-структуру через XPath
    violations = compiler.validate_xml_gost(docx_bytes)
    
    # Нарушений быть не должно
    assert len(violations) == 0
