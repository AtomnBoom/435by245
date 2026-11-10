import io
import zipfile
from lxml import etree
from docx import Document
from docx.shared import Pt, Cm
from typing import Any

class DocxCompiler:
    """
    Единый профессиональный компилятор документов Word по стандарту ГОСТ 7.32-2017.
    Содержит правила верстки, логику генерации из JSON-IR и XPath-валидатор XML разметки.
    """
    
    # Жесткие правила оформления по ГОСТ 7.32-2017 укомплектованы прямо внутри класса
    # Размеры полей: 1 см = 567 twips
    GOST_RULES = {
        "margins": {
            "top": 1134,      # 2.0 см
            "bottom": 1134,   # 2.0 см
            "left": 1701,     # 3.0 см
            "right": 851      # 1.5 см
        },
        "font": {
            "name": "Times New Roman",
            "size_half_points": 28,  # 14pt
        },
        "paragraph": {
            "line_spacing": 1.5,
            "first_line_indent_twips": 709,  # 1.25 см
        }
    }
    
    def compile(self, ir: dict[str, Any]) -> bytes:
        """Принимает JSON-IR, строит документ Word и возвращает его в виде байт."""
        doc = Document()
        
        # Настраиваем базовые поля страницы из внутренних правил ГОСТ
        for section in doc.sections:
            section.top_margin = Cm(self.GOST_RULES["margins"]["top"] / 567)
            section.bottom_margin = Cm(self.GOST_RULES["margins"]["bottom"] / 567)
            section.left_margin = Cm(self.GOST_RULES["margins"]["left"] / 567)
            section.right_margin = Cm(self.GOST_RULES["margins"]["right"] / 567)

        # Перебираем блоки нашего Промежуточного Представления (IR)
        for block in ir.get("blocks", []):
            block_type = block.get("type")
            
            if block_type == "heading":
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.keep_with_next = True
                
                # ГОСТ требует заголовки прописными буквами
                run = p.add_run(block.get("text", "").upper())
                run.font.name = self.GOST_RULES["font"]["name"]
                run.font.size = Pt(self.GOST_RULES["font"]["size_half_points"] / 2)
                run.bold = True
                
            elif block_type == "paragraph":
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = self.GOST_RULES["paragraph"]["line_spacing"]
                p.paragraph_format.first_line_indent = Cm(self.GOST_RULES["paragraph"]["first_line_indent_twips"] / 567)
                
                run = p.add_run(block.get("text", ""))
                run.font.name = self.GOST_RULES["font"]["name"]
                run.font.size = Pt(self.GOST_RULES["font"]["size_half_points"] / 2)

        # Сохраняем готовый документ в оперативную память как поток байт
        file_stream = io.BytesIO()
        doc.save(file_stream)
        return file_stream.getvalue()

    def validate_xml_gost(self, docx_bytes: bytes) -> list[str]:
        """Проверяет внутренний word/document.xml с помощью XPath на соответствие ГОСТу."""
        violations = []
        ns = {"w": "http://openxmlformats.org"}
        
        try:
            with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
                xml_content = z.read("word/document.xml")
                root = etree.fromstring(xml_content)
                
                # 1. XPath Проверка левого поля
                left_margins = root.xpath("//w:pgMar/@w:left", namespaces=ns)
                if left_margins and int(left_margins[0]) != self.GOST_RULES["margins"]["left"]:
                    violations.append(f"Нарушение ГОСТ: Левое поле {left_margins[0]} twips вместо {self.GOST_RULES['margins']['left']}")
                
                # 2. XPath Проверка отступа первой строки
                indents = root.xpath("//w:ind/@w:firstLine", namespaces=ns)
                for indent in indents:
                    if int(indent) != self.GOST_RULES["paragraph"]["first_line_indent_twips"]:
                        violations.append(f"Нарушение ГОСТ: Абзацный отступ {indent} twips вместо {self.GOST_RULES['paragraph']['first_line_indent_twips']}")
                        
        except Exception as e:
            violations.append(f"Ошибка разбора XML-структуры: {str(e)}")
            
        return violations
