from typing import Any, TypeVar, Type

# Это специальная переменная для Python, которая означает "любой тип данных"
T = TypeVar("T")

class RegistryError(Exception):
    """Базовый класс для всех ошибок нашего реестра."""
    pass

class MissingCapabilityError(RegistryError):
    """Ошибка, которая возникает, если ядро просит навык, которого нет в реестре."""
    pass

class AmbiguousCapabilityError(RegistryError):
    """Ошибка, если в реестре под одним именем лежат два разных прибора, и система запуталась."""
    pass

class CapabilityRegistry:
    """
    Распределительный щиток (Реестр) нашего Джарвиса.
    Здесь регистрируются все компоненты и плагины системы.
    """
    def __init__(self) -> None:
        # В этом словаре мы будем хранить наши приборы
        self._registry: dict[str, dict[str, Any]] = {}

    def register(self, key: str, impl: Any, provides: list[Type[Any]]) -> None:
        """
        Метод для регистрации нового прибора (адаптера или скилла).
        key: уникальное текстовое имя (например, 'llm.ollama')
        impl: сам работающий объект (код прибора)
        provides: список контрактов (интерфейсов), которым этот прибор соответствует
        """
        self._registry[key] = {
            "instance": impl,
            "contracts": provides
        }

    def resolve(self, contract: Type[T]) -> T:
        """
        Метод, с помощью которого ядро просит выдать нужный прибор.
        contract: класс-контракт, который нам нужен (например, AbstractLLM)
        """
        candidates = []
        
        # Перебираем все зарегистрированные приборы и ищем те, что подходят под контракт
        for item in self._registry.values():
            if contract in item["contracts"]:
                candidates.append(item["instance"])

        # Если не нашли ни одного подходящего прибора — бьем тревогу
        if not candidates:
            raise MissingCapabilityError(f"Компонент для контракта {contract.__name__} не найден в реестре!")

        # Если нашли больше одного — система не знает, какой выбрать, и тоже сообщает об ошибке
        if len(candidates) > 1:
            raise AmbiguousCapabilityError(f"Найдено несколько компонентов для контракта {contract.__name__}!")

        # Если всё хорошо — возвращаем единственный правильный прибор
        return candidates[0]

    def list_capabilities(self) -> dict[str, list[str]]:
        """Возвращает список всех подключенных в данный момент возможностей для контроля."""
        result = {}
        for key, item in self._registry.items():
            result[key] = [c.__name__ for c in item["contracts"]]
        return result
