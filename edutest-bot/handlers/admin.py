from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, GroupChat
from utils.states import BroadcastStates
from utils.keyboards import get_cancel_menu, get_main_menu

router = Router()

async def is_admin(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role == RoleEnum.ADMIN

async def is_teacher(message: Message) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        return user is not None and user.role in [RoleEnum.TEACHER, RoleEnum.ADMIN]

@router.message(Command("broadcast_all"))
@router.message(F.text == "📣 Рассылка всем")
async def cmd_broadcast_all(message: Message, state: FSMContext):
    if not await is_admin(message):
        await message.answer("У вас нет прав администратора.")
        return
        
    await message.answer("Введите текст сообщения для рассылки всем пользователям:", reply_markup=get_cancel_menu())
    await state.set_state(BroadcastStates.waiting_for_all_text)

@router.message(BroadcastStates.waiting_for_all_text)
async def process_broadcast_all(message: Message, state: FSMContext):
    text = message.text
    async with async_session() as session:
        stmt = select(User.telegram_id)
        result = await session.execute(stmt)
        user_ids = result.scalars().all()
        
    count = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, f"🔔 Уведомление от Администрации:\n\n{text}")
            count += 1
        except Exception:
            pass
            
    await message.answer(f"Рассылка завершена. Доставлено {count} пользователям.", reply_markup=get_main_menu(RoleEnum.ADMIN))
    await state.clear()

@router.message(Command("broadcast_teachers"))
@router.message(F.text == "👨‍🏫 Рассылка учителям")
async def cmd_broadcast_teachers(message: Message, state: FSMContext):
    if not await is_admin(message):
        return
        
    await message.answer("Введите текст сообщения для рассылки учителям:", reply_markup=get_cancel_menu())
    await state.set_state(BroadcastStates.waiting_for_teachers_text)

@router.message(BroadcastStates.waiting_for_teachers_text)
async def process_broadcast_teachers(message: Message, state: FSMContext):
    text = message.text
    async with async_session() as session:
        stmt = select(User.telegram_id).where(User.role == RoleEnum.TEACHER)
        result = await session.execute(stmt)
        teacher_ids = result.scalars().all()
        
    count = 0
    for uid in teacher_ids:
        try:
            await message.bot.send_message(uid, f"👨‍🏫 Уведомление для учителей:\n\n{text}")
            count += 1
        except Exception:
            pass
            
    await message.answer(f"Рассылка завершена. Доставлено {count} учителям.", reply_markup=get_main_menu(RoleEnum.ADMIN))
    await state.clear()

@router.message(Command("broadcast_group"))
@router.message(F.text == "📣 Рассылка группе")
async def cmd_broadcast_group(message: Message, state: FSMContext):
    if not await is_teacher(message):
        await message.answer("Только учителя могут делать рассылку по группам.")
        return
        
    await message.answer("Введите название группы для рассылки:", reply_markup=get_cancel_menu())
    await state.set_state(BroadcastStates.waiting_for_group_name)

@router.message(BroadcastStates.waiting_for_group_name)
async def process_broadcast_group_name(message: Message, state: FSMContext):
    await state.update_data(group_name=message.text.strip())
    await message.answer("Отлично. Теперь введите текст сообщения:")
    await state.set_state(BroadcastStates.waiting_for_group_text)

@router.message(BroadcastStates.waiting_for_group_text)
async def process_broadcast_group_text(message: Message, state: FSMContext):
    data = await state.get_data()
    group_name = data['group_name']
    text = message.text
    
    count = 0
    async with async_session() as session:
        # User who initiated
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        user_res = await session.execute(stmt)
        user = user_res.scalar_one()

        stmt = select(User.telegram_id).where(User.group_name == group_name)
        result = await session.execute(stmt)
        student_ids = result.scalars().all()
        
        for uid in student_ids:
            try:
                await message.bot.send_message(uid, f"📣 Сообщение вашей группе от учителя:\n\n{text}")
                count += 1
            except Exception:
                pass
                
        group_stmt = select(GroupChat.chat_id).where(GroupChat.group_name == group_name)
        group_res = await session.execute(group_stmt)
        group_chats = group_res.scalars().all()
        
        for chat_id in group_chats:
            try:
                await message.bot.send_message(chat_id, f"📣 Сообщение от учителя:\n\n{text}")
            except Exception:
                pass
                
    await message.answer(f"Рассылка группе '{group_name}' завершена. Доставлено {count} ученикам.", reply_markup=get_main_menu(user.role))
    await state.clear()
