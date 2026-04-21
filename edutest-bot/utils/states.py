from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_full_name = State()
    waiting_for_group = State()

class CreateTestStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_answers = State()
    waiting_for_file = State()

class TakeTestStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_answers = State()

class CreateChampionshipStates(StatesGroup):
    waiting_for_title = State()

class LinkTestStates(StatesGroup):
    waiting_for_test_id = State()
    waiting_for_champ_id = State()

class ExportStatsStates(StatesGroup):
    waiting_for_test_id = State()

class BroadcastStates(StatesGroup):
    waiting_for_all_text = State()
    waiting_for_teachers_text = State()
    waiting_for_group_name = State()
    waiting_for_group_text = State()
