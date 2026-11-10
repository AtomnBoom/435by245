import io
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from typing import Any

class XlsxCompiler:
    """
    Единый инженерно-научный компилятор таблиц Excel.
    Поддерживает мульти-листовые книги, запись сложных формул, 
    именованные диапазоны и автоматическую разметку страниц для печати.
    """

    def compile(self, ir: dict[str, Any]) -> bytes:
        """
        Принимает JSON-IR структуры Excel и компилирует её в полноценную книгу.
        Возвращает документ в виде байт.
        """
        wb = Workbook()
        # По умолчанию openpyxl создает один пустой лист, удалим его, чтобы строить строго по IR
        default_sheet = wb.active
        wb.remove(default_sheet)

        # Перебираем блоки нашего Промежуточного Представления (IR)
        for block in ir.get("blocks", []):
            if block.get("type") != "sheet":
                continue

            sheet_name = block.get("name", "Sheet")
            ws = wb.create_sheet(title=sheet_name)

            # 1. Заполняем базовые текстовые или числовые строки
            rows = block.get("rows", [])
            for row_idx, row_data in enumerate(rows, start=1):
                for col_idx, value in enumerate(row_data, start=1):
                    ws.cell(row=row_idx, column=col_idx, value=value)

            # 2. Записываем сложные инженерно-научные формулы
            # Формат в JSON-IR: {"C1": "=SUM(A1:B1)", "Calculations!B2": "=Inputs!A1*2"}
            formulas = block.get("formulas", {})
            for cell_ref, formula_str in formulas.items():
                # Если формула содержит имя текущего листа (например, "Inputs!A1"), очищаем его
                if "!" in cell_ref:
                    target_sheet, actual_ref = cell_ref.split("!", 1)
                    if target_sheet == sheet_name:
                        ws[actual_ref] = formula_str
                        ws[actual_ref].data_type = "f"
                else:
                    ws[cell_ref] = formula_str
                    # Жестко указываем тип "f" (Formula), чтобы Excel понял, что это расчет
                    ws[cell_ref].data_type = "f"

            # 3. Настраиваем разметку страниц и параметры печати, чтобы таблицы не обрезались
            # Выставляем альбомную ориентацию по умолчанию для больших инженерных таблиц
            ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
            ws.page_setup.paperSize = ws.PAPERSIZE_A4
            
            # Включаем автоматическое масштабирование таблицы под ширину страницы A4
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0  # 0 означает "автоматически по высоте"

            # Автоматически подбираем ширину колонок по содержимому для красоты
            for col in ws.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        # Сохраняем готовую книгу в память в виде потока байт
        file_stream = io.BytesIO()
        wb.save(file_stream)
        return file_stream.getvalue()
