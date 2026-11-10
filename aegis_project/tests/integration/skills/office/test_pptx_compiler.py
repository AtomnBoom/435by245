import pytest
import io
from pptx import Presentation
from src.aegis.skills.office.pptx_compiler import PptxCompiler

def test_pptx_compiler_grid_success():
    """Тест: проверяем создание адаптивной презентации на 12-колоночной сетке."""
    compiler = PptxCompiler()

    # Имитируем JSON-IR план презентации из двух слайдов: титульный и двухколоночный
    sample_ir = {
        "schema_version": "1.0",
        "document_type": "pptx",
        "metadata": {"title": "Презентация проекта", "author": "Менеджер"},
        "blocks": [
            {
                "type": "slide",
                "layout": "title",
                "slide_title": "Главный слайд",
                "elements": [{"text": "Добро пожаловать в экосистему Aegis."}]
            },
            {
                "type": "slide",
                "layout": "two_column",
                "slide_title": "Сравнение систем",
                "elements": [
                    {"text": "Левая колонка: преимущества локального ИИ."},
                    {"text": "Правая колонка: риски облачных решений."}
                ]
            }
        ]
    }

    # 1. Генерируем бинарные байты файла
    pptx_bytes = compiler.compile(sample_ir)
    assert len(pptx_bytes) > 0
    assert pptx_bytes[:4] == b"PK\x03\x04" # Файлы презентаций Microsoft — это тоже zip-архивы!

    # 2. Читаем сгенерированную презентацию обратно для проверки геометрии
    prs = Presentation(io.BytesIO(pptx_bytes))
    
    # Проверяем, что создалось ровно 2 слайда
    assert len(prs.slides) == 2
    
    # Проверяем первый слайд (макет на всю ширину)
    slide_1 = prs.slides[0]
    # На слайде должно быть 2 фигуры (1 заголовок + 1 блок контента)
    assert len(slide_1.shapes) == 2
    
    # Проверяем второй слайд (двухколоночный макет)
    slide_2 = prs.slides[1]
    # Должно быть 3 фигуры (1 заголовок + 2 независимые колонки контента)
    assert len(slide_2.shapes) == 3

    # Проверяем геометрические границы: коробки колонок не должны вылезать за ширину слайда 13.333
    for shape in slide_2.shapes:
        # Переводим дюймы обратно в числа (shape.left.inches)
        left_inches = shape.left.inches
        width_inches = shape.width.inches
        # Правый край фигуры (отступ + ширина) обязан быть меньше физической ширины слайда
        assert (left_inches + width_inches) <= 13.333
