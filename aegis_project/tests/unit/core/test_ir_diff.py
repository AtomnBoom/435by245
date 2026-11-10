import pytest
from src.aegis.core.ir_diff import IRDiffEngine

def test_ir_diff_and_patch_roundtrip():
    """Тест: проверяем вычисление диффа правок и его успешное применение к структуре."""
    
    # 1. Стартовое состояние документа
    old_document = {
        "schema_version": "1.0",
        "document_type": "docx",
        "metadata": {
          "title": "Старый документ",
          "author": "Автор"
        },
        "blocks": [
            {"type": "heading", "level": 1, "text": "Старый Заголовок"},
            {"type": "paragraph", "text": "Этот текст мы оставим без изменений."}
        ]
    }

    # 2. Новое состояние документа
    new_document = {
        "schema_version": "1.0",
        "document_type": "docx",
        "metadata": {
          "title": "Старый документ",
          "author": "Автор"
        },
        "blocks": [
            {"type": "heading", "level": 1, "text": "НОВЫЙ КРАСИВЫЙ ЗАГОЛОВОК"},
            {"type": "paragraph", "text": "Этот текст мы оставим без изменений."}
        ]
    }

    # 3. Вычисляем разницу
    diff_patch = IRDiffEngine.calculate_diff(old_document, new_document)
    
    # Проверяем структуру патча
    assert len(diff_patch) > 0
    assert diff_patch[0]["op"] == "replace"
    assert "text" in diff_patch[0]["path"]

    # 4. Накатываем патч на старый документ
    restored_document = IRDiffEngine.apply_patch(old_document, diff_patch)

    # Проверяем, что восстановленный документ совпадает с измененным
    assert restored_document == new_document
    # Берем именно первый блок, так как blocks — это список элементов
    assert restored_document["blocks"][0]["text"] == "НОВЫЙ КРАСИВЫЙ ЗАГОЛОВОК"
