from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, Test, Result
from utils.states import TakeTestStates
from utils.keyboards import get_cancel_menu, get_main_menu

router = Router()

async def is_student(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role == RoleEnum.STUDENT

@router.message(Command("test"))
@router.message(F.text == "📝 Пройти тест")
async def cmd_test(message: Message, state: FSMContext):
    if not await is_student(message):
        await message.answer("Только ученики могут проходить тесты.")
        return
    
    await message.answer("Введите код теста:", reply_markup=get_cancel_menu())
    await state.set_state(TakeTestStates.waiting_for_code)

@router.message(TakeTestStates.waiting_for_code)
async def process_test_code(message: Message, state: FSMContext):
    test_code = message.text.strip()
    if not test_code.isdigit():
        await message.answer("Код теста должен состоять из цифр. Попробуйте еще раз.")
        return
    
    test_id = int(test_code)
    
    async with async_session() as session:
        stmt = select(Test).where(Test.id == test_id, Test.is_active == True)
        result = await session.execute(stmt)
        test = result.scalar_one_or_none()
        
        if not test:
            await message.answer("Тест не найден или не активен.")
            return
            
        # Check if already taken
        user_stmt = select(User).where(User.telegram_id == message.from_user.id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one()

        res_stmt = select(Result).where(Result.test_id == test.id, Result.user_id == user.id)
        res_result = await session.execute(res_stmt)
        existing_result = res_result.scalar_one_or_none()

        if existing_result:
            await message.answer(f"Вы уже проходили этот тест. Ваш результат: {existing_result.score} из {len(test.correct_answers)}")
            await state.clear()
            return
            
    await state.update_data(test_id=test.id, correct_answers=test.correct_answers, user_id=user.id)
    
    if test.file_id:
        try:
            # We don't know if it's a document or photo, let's try document first, if fails try photo
            await message.bot.send_document(message.chat.id, test.file_id)
        except Exception:
            try:
                await message.bot.send_photo(message.chat.id, test.file_id)
            except Exception:
                await message.answer("Не удалось загрузить прикрепленный файл.")

    await message.answer(
        f"Тест '{test.title}' начат!\n"
        f"Количество вопросов: {len(test.correct_answers)}.\n"
        "Отправьте ваши ответы одной строкой без пробелов (например, 'ABCDABCDA').\n"
        "Допустимые символы: A, B, C, D, E (или А, Б, В, Г, Д)."
    )
    await state.set_state(TakeTestStates.waiting_for_answers)

@router.message(TakeTestStates.waiting_for_answers)
async def process_student_answers(message: Message, state: FSMContext):
    answers = message.text.strip().upper()
    translit = str.maketrans("АБВГДЕ", "ABCDEF")
    answers = answers.translate(translit)
    
    data = await state.get_data()
    correct_answers = data['correct_answers']
    
    valid_chars = set("ABCDEF")
    if not all(char in valid_chars for char in answers):
        await message.answer("Ошибка! Ответы должны содержать только буквы A, B, C, D, E. Попробуйте еще раз.")
        return
        
    if len(answers) != len(correct_answers):
        await message.answer(f"Ошибка! Вы ввели {len(answers)} ответов, а нужно {len(correct_answers)}. Попробуйте еще раз.")
        return
        
    # Calculate score
    score = sum(1 for a, c in zip(answers, correct_answers) if a == c)
    
    async with async_session() as session:
        new_result = Result(
            user_id=data['user_id'],
            test_id=data['test_id'],
            student_answers=answers,
            score=score
        )
        session.add(new_result)
        await session.commit()
        
    await message.answer(
        f"Тест завершен!\nВаш результат: {score} из {len(correct_answers)}",
        reply_markup=get_main_menu(RoleEnum.STUDENT)
    )
    await state.clear()
