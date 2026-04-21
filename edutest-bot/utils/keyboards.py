from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.models import RoleEnum

def get_main_menu(role: RoleEnum) -> ReplyKeyboardMarkup:
    if role == RoleEnum.STUDENT:
        keyboard = [
            [KeyboardButton(text="📝 Пройти тест"), KeyboardButton(text="🏆 Лидерборды")],
            [KeyboardButton(text="👤 Мой профиль")]
        ]
    elif role == RoleEnum.TEACHER:
        keyboard = [
            [KeyboardButton(text="➕ Создать тест"), KeyboardButton(text="📊 Статистика тестов")],
            [KeyboardButton(text="🏆 Создать чемпионат"), KeyboardButton(text="🔗 Привязать тест")],
            [KeyboardButton(text="👥 Мои группы"), KeyboardButton(text="📣 Рассылка группе")],
            [KeyboardButton(text="👤 Мой профиль")]
        ]
    elif role == RoleEnum.ADMIN:
        keyboard = [
            [KeyboardButton(text="➕ Создать тест"), KeyboardButton(text="📊 Статистика тестов")],
            [KeyboardButton(text="🏆 Создать чемпионат"), KeyboardButton(text="🔗 Привязать тест")],
            [KeyboardButton(text="👥 Мои группы"), KeyboardButton(text="📣 Рассылка всем")],
            [KeyboardButton(text="👨‍🏫 Рассылка учителям"), KeyboardButton(text="👤 Мой профиль")]
        ]
    else:
        keyboard = []

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие в меню ниже 👇"
    )

def get_cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
