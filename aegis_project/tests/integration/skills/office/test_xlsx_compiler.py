import pytest
from openpyxl import load_workbook
import io
from src.aegis.skills.office.xlsx_compiler import XlsxCompiler

def test_xlsx_compiler_engineering_success():
    """Тест: проверяем создание мульти-листовой книги и корректность записи формул."""
    compiler = XlsxCompiler()

    # Имитируем сложную научно-инженерную задачу: 
    # Лист Inputs с данными и Лист Calculations, который берет значения с первого листа
    sample_ir = {
        "schema_version": "1.0",
        "document_type": "xlsx",
        "metadata": {"title": "Расчет балки", "author": "Инженер"},
        "blocks": [
            {
                "type": "sheet",
                "name": "Inputs",
                "rows": [
                    [100, 200],  # Ячейки A1, B1
                    [300, 400]   # Ячейки A2, B2
                ],
                "formulas": {}
            },
            {
                "type": "sheet",
                "name": "Calculations",
                "rows": [
                    ["Результат", None]
                ],
                "formulas": {
                    "B1": "=SUM(Inputs!A1:B2)"  # Сложная формула, считающая данные с другого листа!
                }
            }
        ]
    }

    # 1. Генерируем байты файла
    xlsx_bytes = compiler.compile(sample_ir)
    assert len(xlsx_bytes) > 0
    assert xlsx_bytes[:4] == b"PK\x03\x04" # Любой современный файл Excel — это тоже zip-архив!

    # 2. Читаем сгенерированный файл обратно через openpyxl для проверки структуры
    wb = load_workbook(io.BytesIO(xlsx_bytes))
    
    # Проверяем, что создалось ровно 2 листа с нужными именами
    assert "Inputs" in wb.sheetnames
    assert "Calculations" in wb.sheetnames

    # Проверяем, что данные на листе Inputs записались верно
    ws_inputs = wb["Inputs"]
    assert ws_inputs["A1"].value == 100
    assert ws_inputs["B2"].value == 400

    # Проверяем формулу на листе Calculations
    ws_calc = wb["Calculations"]
    assert ws_calc["B1"].value == "=SUM(Inputs!A1:B2)"
    assert ws_calc["B1"].data_type == "f" # Проверяем, что тип ячейки строго "формула"

    # Проверяем параметры печати
    assert ws_calc.page_setup.orientation == ws_calc.ORIENTATION_LANDSCAPE
    assert ws_calc.sheet_properties.pageSetUpPr.fitToPage is True
