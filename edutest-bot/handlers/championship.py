from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy import func
from database.db import async_session
from database.models import User, RoleEnum, Championship, Test, Result
from utils.states import CreateChampionshipStates, LinkTestStates
from utils.keyboards import get_cancel_menu, get_main_menu

router = Router()

async def is_teacher_or_admin(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role in [RoleEnum.TEACHER, RoleEnum.ADMIN]

@router.message(Command("new_champ"))
@router.message(F.text == "🏆 Создать чемпионат")
async def cmd_new_champ(message: Message, state: FSMContext):
    if not await is_teacher_or_admin(message):
        await message.answer("Только учителя и администраторы могут создавать чемпионаты.")
        return
    
    await message.answer("Введите название нового чемпионата:", reply_markup=get_cancel_menu())
    await state.set_state(CreateChampionshipStates.waiting_for_title)

@router.message(CreateChampionshipStates.waiting_for_title)
async def process_champ_title(message: Message, state: FSMContext):
    title = message.text.strip()
    
    async with async_session() as session:
        new_champ = Championship(title=title)
        session.add(new_champ)
        await session.flush()
        champ_id = new_champ.id
        
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        await session.commit()
        
    await message.answer(f"✅ Чемпионат '{title}' создан!\nID чемпионата: `{champ_id}`\n\nИспользуйте команду /link_test, чтобы добавить тесты в этот чемпионат.", parse_mode="Markdown", reply_markup=get_main_menu(user.role))
    await state.clear()

@router.message(Command("link_test"))
@router.message(F.text == "🔗 Привязать тест")
async def cmd_link_test(message: Message, state: FSMContext):
    if not await is_teacher_or_admin(message):
        return
    await message.answer("Введите ID (код) теста, который нужно привязать:", reply_markup=get_cancel_menu())
    await state.set_state(LinkTestStates.waiting_for_test_id)

@router.message(LinkTestStates.waiting_for_test_id)
async def process_link_test_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID теста должен быть числом.")
        return
    await state.update_data(test_id=int(message.text))
    await message.answer("Теперь введите ID чемпионата:")
    await state.set_state(LinkTestStates.waiting_for_champ_id)

@router.message(LinkTestStates.waiting_for_champ_id)
async def process_link_champ_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID чемпионата должен быть числом.")
        return
        
    data = await state.get_data()
    test_id = data['test_id']
    champ_id = int(message.text)
    
    async with async_session() as session:
        test = await session.get(Test, test_id)
        champ = await session.get(Championship, champ_id)
        
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        
        if not test or not champ:
            await message.answer("Ошибка: Тест или Чемпионат с таким ID не найден.", reply_markup=get_main_menu(user.role))
            await state.clear()
            return
            
        test.championship_id = champ.id
        await session.commit()
        
    await message.answer(f"✅ Тест '{test.title}' успешно привязан к чемпионату '{champ.title}'!", reply_markup=get_main_menu(user.role))
    await state.clear()

@router.message(Command("leaderboard"))
@router.message(F.text == "🏆 Лидерборды")
async def cmd_leaderboard(message: Message, state: FSMContext):
    if message.text == "🏆 Лидерборды":
        await message.answer("Введите ID чемпионата, чтобы посмотреть лидерборд:", reply_markup=get_cancel_menu())
        from utils.states import ExportStatsStates
        # Reusing state for simplicity, or we can make a new state WaitChampId
        # Actually let's create a quick state WaitChampId inline or add it.
        # Let's add it to utils/states.py or just use FSM
        await state.set_state("waiting_for_leaderboard_champ_id")
        return
        
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /leaderboard <id_чемпионата>")
        return
        
    await show_leaderboard(message, int(parts[1]))

@router.message(F.state == "waiting_for_leaderboard_champ_id")
async def process_leaderboard_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID чемпионата должен быть числом.")
        return
    await show_leaderboard(message, int(message.text))
    await state.clear()

async def show_leaderboard(message: Message, champ_id: int):
    async with async_session() as session:
        champ = await session.get(Championship, champ_id)
        
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        res = await session.execute(stmt)
        user = res.scalar_one()
        
        if not champ:
            await message.answer("Чемпионат не найден.", reply_markup=get_main_menu(user.role))
            return
            
        stmt = (
            select(User.full_name, User.group_name, func.sum(Result.score).label('total_score'))
            .join(Result, Result.user_id == User.id)
            .join(Test, Result.test_id == Test.id)
            .where(Test.championship_id == champ_id)
            .group_by(User.id)
            .order_by(func.sum(Result.score).desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        leaders = result.all()
        
    if not leaders:
        await message.answer(f"🏆 Лидерборд '{champ.title}':\n\nПока нет результатов.", reply_markup=get_main_menu(user.role))
        return
        
    text = f"🏆 Лидерборд чемпионата '{champ.title}':\n\n"
    for i, (name, group, score) in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔸"
        text += f"{medal} {i}. {name} ({group}) — {score} баллов\n"
        
    await message.answer(text, reply_markup=get_main_menu(user.role))
