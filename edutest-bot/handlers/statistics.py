from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, Test, Result
from utils.states import ExportStatsStates
from utils.keyboards import get_cancel_menu, get_main_menu
import pandas as pd
import os

router = Router()

async def is_teacher_or_admin(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role in [RoleEnum.TEACHER, RoleEnum.ADMIN]

@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика тестов")
async def cmd_stats(message: Message, state: FSMContext):
    if not await is_teacher_or_admin(message):
        return
        
    await message.answer("Введите ID (код) теста для выгрузки результатов:", reply_markup=get_cancel_menu())
    await state.set_state(ExportStatsStates.waiting_for_test_id)

@router.message(ExportStatsStates.waiting_for_test_id)
async def process_stats_test_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID теста должен быть числом.")
        return
        
    test_id = int(message.text)
    
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()

        test = await session.get(Test, test_id)
        if not test:
            await message.answer("Тест не найден.", reply_markup=get_main_menu(user.role))
            await state.clear()
            return
            
        stmt = select(User.group_name).join(Result, Result.user_id == User.id).where(Result.test_id == test_id).distinct()
        res = await session.execute(stmt)
        groups = res.scalars().all()
        
    if not groups:
        await message.answer("Пока нет результатов по этому тесту.", reply_markup=get_main_menu(user.role))
        await state.clear()
        return
        
    await state.update_data(test_id=test_id, test_title=test.title)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Всё вместе (Все классы)", callback_data="statsgrp_all")]
    ])
    
    for g in groups:
        if g:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text=f"Только {g}", callback_data=f"statsgrp_{g}")])
            
    await message.answer("Выгрузить статистику для всех или только для конкретной группы?", reply_markup=keyboard)

@router.callback_query(ExportStatsStates.waiting_for_test_id, F.data.startswith("statsgrp_"))
async def process_stats_group(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    data = await state.get_data()
    test_id = data['test_id']
    test_title = data['test_title']
    
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()

        if action == "all":
            stmt_results = (
                select(User.full_name, User.group_name, Result.score, Result.student_answers, Result.created_at)
                .join(Result, Result.user_id == User.id)
                .where(Result.test_id == test_id)
                .order_by(Result.score.desc())
            )
        else:
            stmt_results = (
                select(User.full_name, User.group_name, Result.score, Result.student_answers, Result.created_at)
                .join(Result, Result.user_id == User.id)
                .where(Result.test_id == test_id, User.group_name == action)
                .order_by(Result.score.desc())
            )
            
        result = await session.execute(stmt_results)
        results = result.all()
        
    if not results:
        await callback.message.edit_text("Пока нет результатов.", reply_markup=get_main_menu(user.role))
        await state.clear()
        return
        
    # Generate Excel using pandas
    data = []
    for name, group, score, answers, date in results:
        data.append({
            "ФИО": name,
            "Группа": group,
            "Балл": score,
            "Ответы": answers,
            "Дата": date.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(data)
    group_str = "all" if action == "all" else action
    filename = f"stats_test_{test_id}_{group_str}.xlsx"
    df.to_excel(filename, index=False)
    
    # Send document
    try:
        doc = FSInputFile(filename)
        caption = f"📊 Статистика по тесту '{test_title}'"
        if action != "all":
            caption += f"\nГруппа: {action}"
        await callback.message.answer_document(doc, caption=caption, reply_markup=get_main_menu(user.role))
        await callback.message.delete()
    except Exception as e:
        await callback.message.answer("Ошибка при отправке файла.", reply_markup=get_main_menu(user.role))
    finally:
        if os.path.exists(filename):
            os.remove(filename)
            
    await state.clear()
