import io
from pptx import Presentation
from pptx.util import Inches, Pt
from typing import Any

class PptxCompiler:
    """
    Единый компилятор адаптивных презентаций PowerPoint.
    Использует детерминированную 12-колоночную сетку (Gamma-like)
    для идеального размещения контента и заголовков на слайде.
    """
    
    # Геометрия широкоформатного слайда 16:9 в дюймах
    SLIDE_WIDTH = 13.333
    SLIDE_HEIGHT = 7.5
    
    # Расчет ширины одной колонки (13.333 / 12 колонок = ~1.111 дюйма)
    COLUMN_WIDTH = SLIDE_WIDTH / 12
    
    # Отступы от краев слайда (безопасные зоны)
    MARGIN_LEFT = 0.8
    MARGIN_TOP = 1.5

    def compile(self, ir: dict[str, Any]) -> bytes:
        """
        Преобразует JSON-IR структуру слайдов в бинарный файл .pptx.
        """
        prs = Presentation()
        
        # Задаем жесткие размеры слайда 16:9
        prs.slide_width = Inches(self.SLIDE_WIDTH)
        prs.slide_height = Inches(self.SLIDE_HEIGHT)
        
        # Используем пустой макет (обычно это индекс 6 в стандартных шаблонах), 
        # чтобы строить свою адаптивную сетку без ограничений Microsoft
        blank_slide_layout = prs.slide_layouts[6]

        # Перебираем слайды из нашего Промежуточного Представления (IR)
        for slide_block in ir.get("blocks", []):
            if slide_block.get("type") != "slide":
                continue
                
            slide = prs.slides.add_slide(blank_slide_layout)
            
            # 1. Добавляем красивый фиксированный заголовок слайда
            title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.8))
            tf_title = title_box.text_frame
            tf_title.word_wrap = True
            p_title = tf_title.paragraphs[0]
            p_title.text = slide_block.get("slide_title", "Без названия").upper()
            p_title.font.name = "Arial"
            p_title.font.size = Pt(28)
            p_title.font.bold = True

            # 2. Размещаем контентные элементы по 12-колоночной сетке
            # Допустимые макеты (layout): 'title' (одиночный), 'two_column' (две колонки)
            layout_type = slide_block.get("layout", "content")
            elements = slide_block.get("elements", [])
            
            if layout_type == "two_column" and len(elements) >= 2:
                # Делим слайд ровно пополам: две колонки по 5 колонок шириной (span=5) + отступ
                self._add_grid_element(slide, elements[0], col_start=0, col_span=5)
                self._add_grid_element(slide, elements[1], col_start=6, col_span=5)
            else:
                # Обычный макет на всю ширину слайда (занимает 10 колонок из 12)
                for element in elements:
                    self._add_grid_element(slide, element, col_start=0, col_span=10)

        # Сохраняем готовую презентацию в поток байт
        file_stream = io.BytesIO()
        prs.save(file_stream)
        return file_stream.getvalue()

    def _add_grid_element(self, slide: Any, element: dict[str, Any], col_start: int, col_span: int) -> None:
        """Внутренний математический метод для расчета точных координат блока на сетке."""
        # Вычисляем физический отступ слева: базовый маргин + (индекс колонки * ширину колонки)
        left_pos = self.MARGIN_LEFT + (col_start * self.COLUMN_WIDTH)
        width_pos = col_span * self.COLUMN_WIDTH
        
        # Создаем текстовое поле по выверенным координатам сетки
        tx_box = slide.shapes.add_textbox(Inches(left_pos), Inches(self.MARGIN_TOP), Inches(width_pos), Inches(4.5))
        tf = tx_box.text_frame
        tf.word_wrap = True  # Включаем автоперенос слов, чтобы текст не улетал вбок
        
        p = tf.paragraphs[0]
        p.text = element.get("text", "")
        p.font.name = "Calibri"
        p.font.size = Pt(16)
