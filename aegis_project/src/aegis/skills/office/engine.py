from typing import Any
from src.aegis.core.registry import CapabilityRegistry, MissingCapabilityError

class OfficeEngine:
    """
    Фасад (Единая точка входа) для генерации всех типов документов.
    Автоматически распознает тип документа и вызывает нужный компилятор из Реестра.
    """
    def __init__(self, registry: CapabilityRegistry) -> None:
        # Привязываем наш распределительный щиток (Реестр) к двигателю
        self.registry = registry

    def compile(self, ir: dict[str, Any]) -> bytes:
        """
        Единый метод для сборки любого файла.
        ir: словарь структуры документа (JSON-IR)
        """
        # Достаем тип документа из JSON (например, 'docx')
        doc_type = ir.get("document_type")
        if not doc_type:
            raise ValueError("В структуре документа отсутствует обязательное поле 'document_type'!")

        # Формируем строковый ключ, по которому компилятор зарегистрирован в системе
        registry_key = f"office.{doc_type}"
        
        try:
            # Пытаемся найти компилятор в Реестре по его текстовому ключу
            # Мы используем прямой доступ к словарю реестра для Фазы 1
            if registry_key in self.registry._registry:
                compiler = self.registry._registry[registry_key]["instance"]
                # Запускаем компиляцию у найденного прибора и возвращаем байты
                return compiler.compile(ir)
            else:
                raise MissingCapabilityError(f"Компонент для компиляции типа '{doc_type}' не зарегистрирован!")
                
        except KeyError:
            raise MissingCapabilityError(f"Критическая ошибка реестра при поиске компилятора {registry_key}")
