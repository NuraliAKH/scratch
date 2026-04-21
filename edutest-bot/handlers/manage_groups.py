from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, StudentGroup
from utils.states import BroadcastStates  # we can create a new state or just reuse, better to create new
from aiogram.fsm.state import State, StatesGroup
from utils.keyboards import get_cancel_menu, get_main_menu

class ManageGroupsStates(StatesGroup):
    waiting_for_group_name = State()

router = Router()

async def is_teacher_or_admin(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role in [RoleEnum.TEACHER, RoleEnum.ADMIN]

@router.message(F.text == "👥 Мои группы")
async def cmd_manage_groups(message: Message):
    if not await is_teacher_or_admin(message):
        return
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать группу", callback_data="mg_create")],
        [InlineKeyboardButton(text="📋 Список моих групп", callback_data="mg_list")]
    ])
    
    await message.answer("Управление группами:", reply_markup=keyboard)

@router.callback_query(F.data == "mg_create")
async def mg_create(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название новой группы (например, '10А' или 'БИ-20'):", reply_markup=get_cancel_menu())
    await state.set_state(ManageGroupsStates.waiting_for_group_name)
    await callback.answer()

@router.message(ManageGroupsStates.waiting_for_group_name)
async def process_new_group_name(message: Message, state: FSMContext):
    group_name = message.text.strip()
    
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        user_res = await session.execute(stmt)
        user = user_res.scalar_one()
        
        # Check if exists
        check_stmt = select(StudentGroup).where(StudentGroup.name == group_name)
        check_res = await session.execute(check_stmt)
        existing = check_res.scalar_one_or_none()
        
        if existing:
            await message.answer(f"Группа '{group_name}' уже существует в базе.", reply_markup=get_main_menu(user.role))
            await state.clear()
            return
            
        new_group = StudentGroup(name=group_name, teacher_id=user.id)
        session.add(new_group)
        await session.commit()
        
    await message.answer(f"✅ Группа '{group_name}' успешно создана!\nТеперь ученики смогут выбрать её при регистрации.", reply_markup=get_main_menu(user.role))
    await state.clear()

@router.callback_query(F.data == "mg_list")
async def mg_list(callback: CallbackQuery):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == callback.from_user.id)
        user_res = await session.execute(stmt)
        user = user_res.scalar_one()
        
        groups_stmt = select(StudentGroup).where(StudentGroup.teacher_id == user.id)
        groups_res = await session.execute(groups_stmt)
        groups = groups_res.scalars().all()
        
    if not groups:
        await callback.message.edit_text("У вас пока нет созданных групп.")
        return
        
    text = "📋 Ваши группы:\n\n"
    for g in groups:
        text += f"🔹 {g.name}\n"
        
    await callback.message.edit_text(text)
