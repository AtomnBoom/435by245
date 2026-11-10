import json
import jsonpatch
from typing import Any

class IRDiffEngine:
    """
    Двигатель двусторонней синхронизации документов.
    Умеет вычислять разницу (diff) между версиями по стандарту RFC 6902
    и применять точечные патчи правок к JSON-IR структуре.
    """
    
    @staticmethod
    def calculate_diff(old_ir: dict[str, Any], new_ir: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Сравнивает старую и новую версию документа.
        Возвращает список точечных операций (патч).
        """
        patch = jsonpatch.make_patch(old_ir, new_ir)
        return list(patch)

    @staticmethod
    def apply_patch(base_ir: dict[str, Any], patch_operations: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Берет базовый документ, накатывает на него список правок (патч)
        и возвращает обновленный документ.
        """
        # Теперь модуль json подключен, и эта строчка отработает без ошибок!
        base_copy = json.loads(json.dumps(base_ir, ensure_ascii=False))
        
        json_patch = jsonpatch.JsonPatch(patch_operations)
        return json_patch.apply(base_copy)
