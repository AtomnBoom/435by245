from enum import Enum, auto
from typing import Any

class State(Enum):
    """Все возможные состояния разума нашего Джарвиса."""
    IDLE = auto()               # Система свободна и ждет задачу
    PLANNING = auto()           # Модель строит структуру и план работы (JSON-план)
    GENERATING = auto()         # Идет пошаговая генерация блоков текста/таблиц
    VALIDATING = auto()         # Программная проверка документа по схемам и ГОСТу
    REPAIRING = auto()          # ИИ исправляет ошибки, найденные валидатором
    WAITING_FOR_INPUT = auto()  # Система ждет ответа или одобрения от человека
    INTERACTIVE = auto()        # Режим WYSIWYG: вы руками правите файл, ИИ на паузе
    DONE = auto()               # Задача успешно завершена, артефакт готов

class Event(Enum):
    """События, которые заставляют автомат переключать состояния."""
    START = auto()              # Юзер дал задачу
    PLAN_READY = auto()         # ИИ построил план глав
    IR_READY = auto()           # Модель сгенерировала текст блоков
    VALIDATION_PASSED = auto()  # Документ идеален, ошибок нет
    VALIDATION_FAILED = auto()  # Валидатор нашел баг в верстке или формуле
    REPAIR_ATTEMPTED = auto()   # ИИ попробовал исправить свой баг
    USER_INTERRUPT = auto()     # Человек нажал "Пауза/Редактировать руками"
    USER_EDIT_APPLIED = auto()  # Ручные правки сохранены в лог базы данных L1
    USER_RESUME = auto()        # Человек нажал кнопку "Продолжить работу ИИ"

class InvalidTransitionError(Exception):
    """Ошибка, если система пытается совершить нелогичный перепрыг состояний."""
    pass

class TaskFSM:
    """
    Детерминированный конечный автомат (State Machine) управления логикой Джарвиса.
    Жестко контролирует шаги ИИ и поддерживает интерактивные прерывания человеком.
    """
    # Таблица легальных переходов: (Текущее_Состояние, Событие) -> Новое_Состояние
    TRANSITIONS: dict[tuple[State, Event], State] = {
        # Линейный успешный путь генерации
        (State.IDLE, Event.START): State.PLANNING,
        (State.PLANNING, Event.PLAN_READY): State.GENERATING,
        (State.GENERATING, Event.IR_READY): State.VALIDATING,
        (State.VALIDATING, Event.VALIDATION_PASSED): State.DONE,
        
        # Контур автоматической починки багов ИИ через Docker-песочницу
        (State.VALIDATING, Event.VALIDATION_FAILED): State.REPAIRING,
        (State.REPAIRING, Event.REPAIR_ATTEMPTED): State.VALIDATING,
        
        # Контур интерактивного ручного редактирования в WYSIWYG (Gamma-like)
        (State.GENERATING, Event.USER_INTERRUPT): State.INTERACTIVE,
        (State.VALIDATING, Event.USER_INTERRUPT): State.INTERACTIVE,
        (State.INTERACTIVE, Event.USER_EDIT_APPLIED): State.INTERACTIVE,
        (State.INTERACTIVE, Event.USER_RESUME): State.VALIDATING,
        
        # Сброс в исходное состояние для новых задач
        (State.DONE, Event.START): State.PLANNING,
    }

    def __init__(self, start_state: State = State.IDLE) -> None:
        self._current_state = start_state

    @property
    def current_state(self) -> State:
        """Возвращает текущий статус автомата."""
        return self._current_state

    def transition(self, event: Event) -> State:
        """Переключает состояние системы на основе произошедшего события."""
        key = (self._current_state, event)
        if key in self.TRANSITIONS:
            self._current_state = self.TRANSITIONS[key]
            return self._current_state
        else:
            raise InvalidTransitionError(
                f"Запрещенный переход! Нельзя переключить систему из стейта {self._current_state.name} по событию {event.name}!"
            )
