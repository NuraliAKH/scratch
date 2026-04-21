from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from database.db import async_session
from database.models import User, RoleEnum, StudentGroup
from utils.states import RegistrationStates
from utils.keyboards import get_main_menu, get_cancel_menu
from config import ADMIN_ID

router = Router()

@router.message(Command("cancel"))
@router.message(F.text == "❌ Отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
    if user:
        await message.answer("Действие отменено.", reply_markup=get_main_menu(user.role))
    else:
        await message.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if user:
        await message.answer(
            f"С возвращением, {user.full_name or 'пользователь'}! Ваша роль: {user.role.value}",
            reply_markup=get_main_menu(user.role)
        )
        return

    # Check if this user is the admin from config
    role_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ученик 🎓", callback_data="role_student")],
        [InlineKeyboardButton(text="Учитель 👨‍🏫", callback_data="role_teacher")]
    ])

    if message.from_user.id == ADMIN_ID:
        role_keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text="Администратор 🛠", callback_data="role_admin")]
        )

    await message.answer(
        "👋 Добро пожаловать в EduTest Bot!\nПожалуйста, выберите вашу роль:",
        reply_markup=role_keyboard
    )
    await state.set_state(RegistrationStates.waiting_for_role)

@router.callback_query(RegistrationStates.waiting_for_role, F.data.startswith("role_"))
async def process_role_selection(callback: CallbackQuery, state: FSMContext):
    role_str = callback.data.split("_")[1]
    
    if role_str == "admin" and callback.fromuser.id != ADMIN_ID:
        await callback.answer("У вас нет прав администратора!", show_alert=True)
        return

    role_mapping = {
        "student": RoleEnum.STUDENT,
        "teacher": RoleEnum.TEACHER,
        "admin": RoleEnum.ADMIN
    }
    selected_role = role_mapping.get(role_str, RoleEnum.STUDENT)

    await state.update_data(role=selected_role)

    if selected_role == RoleEnum.ADMIN:
        async with async_session() as session:
            new_admin = User(
                telegram_id=callback.from_user.id,
                role=RoleEnum.ADMIN,
                full_name="Administrator"
            )
            session.add(new_admin)
            await session.commit()
        await callback.message.delete()
        await callback.message.answer("Вы зарегистрированы как Администратор!", reply_markup=get_main_menu(RoleEnum.ADMIN))
        await state.clear()
        return

    await callback.message.edit_text("Пожалуйста, введите ваше ФИО (Фамилия Имя Отчество):")
    await state.set_state(RegistrationStates.waiting_for_full_name)

@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    data = await state.get_data()

    if data.get("role") == RoleEnum.STUDENT:
        async with async_session() as session:
            stmt = select(StudentGroup.name).distinct()
            res = await session.execute(stmt)
            groups = res.scalars().all()
            
        if groups:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            # Add up to 10 groups as buttons to avoid too large keyboards
            for g in groups[:10]:
                keyboard.inline_keyboard.append([InlineKeyboardButton(text=g, callback_data=f"selgrp_{g}")])
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="✍️ Ввести вручную", callback_data="selgrp_manual")])
            
            await message.answer("Выберите ваш класс/группу из списка ниже или введите вручную:", reply_markup=keyboard)
        else:
            await message.answer("Введите ваш класс/группу (например, 10А или БИ-20):")
        await state.set_state(RegistrationStates.waiting_for_group)
    else:
        async with async_session() as session:
            new_user = User(
                telegram_id=message.from_user.id,
                role=data["role"],
                full_name=message.text.strip()
            )
            session.add(new_user)
            await session.commit()
        await message.answer("Вы успешно зарегистрированы как Учитель!", reply_markup=get_main_menu(data["role"]))
        await state.clear()

@router.callback_query(RegistrationStates.waiting_for_group, F.data.startswith("selgrp_"))
async def process_group_selection(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "manual":
        await callback.message.edit_text("Введите ваш класс/группу текстом:")
        return
        
    # The action is the group name
    await finalize_student_registration(callback.message, action, state, is_callback=True)

@router.message(RegistrationStates.waiting_for_group)
async def process_group(message: Message, state: FSMContext):
    group_name = message.text.strip()
    await finalize_student_registration(message, group_name, state, is_callback=False)

async def finalize_student_registration(message: Message, group_name: str, state: FSMContext, is_callback: bool):
    data = await state.get_data()

    async with async_session() as session:
        new_user = User(
            telegram_id=message.chat.id if is_callback else message.from_user.id,
            role=data["role"],
            full_name=data["full_name"],
            group_name=group_name
        )
        session.add(new_user)
        await session.commit()
    
    msg_text = f"Вы успешно зарегистрированы как Ученик группы {group_name}!"
    if is_callback:
        await message.edit_text(msg_text)
        await message.answer("Добро пожаловать!", reply_markup=get_main_menu(data["role"]))
    else:
        await message.answer(msg_text, reply_markup=get_main_menu(data["role"]))
        
    await state.clear()

@router.message(F.text == "👤 Мой профиль")
async def profile_handler(message: Message):
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
    if user:
        text = f"👤 Профиль:\nФИО: {user.full_name}\nРоль: {user.role.value}"
        if user.group_name:
            text += f"\nГруппа: {user.group_name}"
        await message.answer(text, reply_markup=get_main_menu(user.role))
