import sys
import json
import base64
import zipfile
import io
import xml.etree.ElementTree as ET

def extract_docx(binary_data):
    try:
        with zipfile.ZipFile(io.BytesIO(binary_data)) as z:
            # Нативно извлекаем XML-структуру основного текста Word
            xml_content = z.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # Собираем все текстовые теги <w:t> в один человекочитаемый текст
            paragraphs = []
            namespaces = {'w': 'http://openxmlformats.org'}
            for p in root.findall('.//w:p', namespaces):
                text_pieces = [t.text for t in p.findall('.//w:t', namespaces) if t.text]
                if text_pieces:
                    paragraphs.append("".join(text_pieces))
            return "\n\n".join(paragraphs)
    except Exception:
        return "Ошибка разбора структуры Word документа."

def extract_xlsx(binary_data):
    try:
        with zipfile.ZipFile(io.BytesIO(binary_data)) as z:
            # Извлекаем общую базу строк таблицы
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_xml = z.read('xl/sharedStrings.xml')
                ss_root = ET.fromstring(ss_xml)
                ns = {'ns': 'http://openxmlformats.org'}
                shared_strings = [t.text if t.text else "" for t in ss_root.findall('.//ns:t', ns)]

            # Читаем первый рабочий лист таблицы
            sheet_xml = z.read('xl/worksheets/sheet1.xml')
            sheet_root = ET.fromstring(sheet_xml)
            ns = {'ns': 'http://openxmlformats.org'}
            
            rows = {}
            for row in sheet_root.findall('.//ns:row', ns):
                r_idx = row.get('r')
                cells = []
                for c in row.findall('.//ns:v', ns):
                    val = c.text
                    # Если значение — это индекс из базы строк, подставляем текст
                    if c.getparent() is not None and c.getparent().get('t') == 's':
                        val = shared_strings[int(val)]
                    cells.append(val)
                if cells:
                    rows[r_idx] = "  |  ".join(cells)
            
            return "[A.E.G.I.S. Структура Локальной Таблицы]\n\n" + "\n".join([f"Строка {k}: {v}" for k, v in rows.items()])
    except Exception:
        return "Ошибка разбора листов Excel таблицы."

def main():
    try:
        # Считываем входные параметры от JavaScript
        input_data = json.loads(sys.stdin.read())
        file_name = input_data.get('name', '')
        ext = file_name.split('.')[-1].toLowerCase() if '.' in file_name else ''
        base64_content = input_data.get('base64', '')
        
        if ',' in base64_content:
            base64_content = base64_content.split(',')[1]
            
        binary_data = base64.b64decode(base64_content)
        
        if ext == 'docx':
            result = extract_docx(binary_data)
        elif ext == 'xlsx':
            result = extract_xlsx(binary_data)
        else:
            result = f"[A.E.G.I.S.] Файл {file_name} успешно импортирован в ядро."
            
        print(json.dumps({"status": "success", "text": result}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "text": str(e)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
