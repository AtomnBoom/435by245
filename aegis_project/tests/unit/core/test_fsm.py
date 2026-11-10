import pytest
from src.aegis.core.fsm import TaskFSM, State, Event, InvalidTransitionError

def test_fsm_successful_linear_flow():
    """Тест: Проверяем стандартную успешную цепочку шагов ИИ."""
    fsm = TaskFSM()
    assert fsm.current_state == State.IDLE

    # IDLE -> START -> PLANNING
    assert fsm.transition(Event.START) == State.PLANNING
    # PLANNING -> PLAN_READY -> GENERATING
    assert fsm.transition(Event.PLAN_READY) == State.GENERATING
    # GENERATING -> IR_READY -> VALIDATING
    assert fsm.transition(Event.IR_READY) == State.VALIDATING
    # VALIDATING -> VALIDATION_PASSED -> DONE
    assert fsm.transition(Event.VALIDATION_PASSED) == State.DONE

def test_fsm_interactive_user_interrupt_flow():
    """Тест: Проверяем режим ручной паузы и правок в интерфейсе WYSIWYG."""
    fsm = TaskFSM(start_state=State.GENERATING)
    
    # Юзер нажал паузу во время генерации: GENERATING -> USER_INTERRUPT -> INTERACTIVE
    assert fsm.transition(Event.USER_INTERRUPT) == State.INTERACTIVE
    
    # Юзер сделал ручную правку: INTERACTIVE -> USER_EDIT_APPLIED -> INTERACTIVE
    assert fsm.transition(Event.USER_EDIT_APPLIED) == State.INTERACTIVE
    
    # Юзер нажал "Продолжить": INTERACTIVE -> USER_RESUME -> VALIDATING
    assert fsm.transition(Event.USER_RESUME) == State.VALIDATING

def test_fsm_invalid_transition_protection():
    """Тест: Защита должна заблокировать нелогичный перевод состояний."""
    fsm = TaskFSM(start_state=State.IDLE)
    
    # Нельзя из сна сразу перепрыгнуть в проверку готового ГОСТа
    with pytest.raises(InvalidTransitionError):
        fsm.transition(Event.VALIDATION_PASSED)
