from aiogram.fsm.state import StatesGroup, State

class ContactAdminStates(StatesGroup):
    waiting_for_message = State()
    