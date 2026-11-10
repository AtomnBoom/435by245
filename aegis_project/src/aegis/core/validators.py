import json
import os
from typing import Any
import jsonschema
from jsonschema.exceptions import ValidationError

class IRValidationError(Exception):
    """Кастомное исключение для ошибок валидации структуры документа."""
    pass

class IRValidator:
    """Компонент ядра, отвечающий за жесткую проверку структуры JSON-IR документов по схеме."""
    def __init__(self, schema_path: str) -> None:
        self.schema_path = schema_path
        self._schema = self._load_schema()

    def _load_schema(self) -> dict[str, Any]:
        """Загружает JSON-схему с жесткого диска."""
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Файл схемы IR не найден по адресу: {self.schema_path}")
        
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, instance: dict[str, Any]) -> None:
        """
        Проверяет документ на соответствие схеме.
        Если находит ошибку — выбрасывает понятное человеческое исключение IRValidationError.
        """
        try:
            jsonschema.validate(instance=instance, schema=self._schema)
        except ValidationError as e:
            # Превращаем системную ошибку в понятный лог нарушений
            raise IRValidationError(f"Ошибка структуры документа: {e.message} в блоке {list(e.absolute_path)}")
