from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, Test
from utils.states import CreateTestStates
from utils.keyboards import get_cancel_menu, get_main_menu

router = Router()

async def is_teacher(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role in [RoleEnum.TEACHER, RoleEnum.ADMIN]

@router.message(Command("new_test"))
@router.message(F.text == "➕ Создать тест")
async def cmd_new_test(message: Message, state: FSMContext):
    if not await is_teacher(message):
        await message.answer("У вас нет прав для создания тестов.")
        return
    
    await message.answer("Введите название теста (например, 'Алгебра 10 класс Итоговая'):", reply_markup=get_cancel_menu())
    await state.set_state(CreateTestStates.waiting_for_title)

@router.message(CreateTestStates.waiting_for_title)
async def process_test_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите строку правильных ответов без пробелов (например, 'ABCDABCDA'):\nДопустимые символы: A, B, C, D, E (можно использовать кириллицу А, Б, В, Г, Д, бот переведет их).")
    await state.set_state(CreateTestStates.waiting_for_answers)

@router.message(CreateTestStates.waiting_for_answers)
async def process_test_answers(message: Message, state: FSMContext):
    answers = message.text.strip().upper()
    # Replace cyrillic with latin
    translit = str.maketrans("АБВГДЕ", "ABCDEF")
    answers = answers.translate(translit)
    
    valid_chars = set("ABCDEF")
    if not all(char in valid_chars for char in answers):
        await message.answer("Ошибка! Ответы должны содержать только буквы A, B, C, D, E. Попробуйте еще раз.")
        return
    
    await state.update_data(answers=answers)
    await message.answer(
        f"Ответы приняты ({len(answers)} вопросов).\n"
        "Теперь отправьте файл с заданиями (PDF, картинка или документ), который увидят ученики.\n"
        "Если файла нет, просто отправьте слово 'нет' или 'пропустить'."
    )
    await state.set_state(CreateTestStates.waiting_for_file)

@router.message(CreateTestStates.waiting_for_file, F.content_type.in_({'document', 'photo', 'text'}))
async def process_test_file(message: Message, state: FSMContext):
    file_id = None
    if message.content_type == ContentType.DOCUMENT:
        file_id = message.document.file_id
    elif message.content_type == ContentType.PHOTO:
        file_id = message.photo[-1].file_id
    elif message.text and message.text.lower() not in ['нет', 'пропустить', 'no', 'skip']:
        await message.answer("Пожалуйста, отправьте файл или напишите 'пропустить'.")
        return

    data = await state.get_data()
    
    async with async_session() as session:
        # Get user id
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one()

        new_test = Test(
            title=data['title'],
            author_id=user.id,
            correct_answers=data['answers'],
            file_id=file_id
        )
        session.add(new_test)
        await session.flush() # To get the new_test.id
        test_id = new_test.id
        await session.commit()

    await message.answer(
        f"✅ Тест '{data['title']}' успешно создан!\n\n"
        f"🔑 Код для учеников: `{test_id}`\n"
        f"Количество вопросов: {len(data['answers'])}",
        parse_mode="Markdown",
        reply_markup=get_main_menu(user.role)
    )
    await state.clear()
