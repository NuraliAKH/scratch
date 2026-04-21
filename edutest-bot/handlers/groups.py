from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from sqlalchemy.future import select
from database.db import async_session
from database.models import GroupChat

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group(event: ChatMemberUpdated):
    # This event triggers when the bot is added to a group/supergroup
    if event.chat.type in ['group', 'supergroup']:
        chat_id = event.chat.id
        group_title = event.chat.title

        async with async_session() as session:
            stmt = select(GroupChat).where(GroupChat.chat_id == chat_id)
            result = await session.execute(stmt)
            existing_group = result.scalar_one_or_none()

            if not existing_group:
                new_group = GroupChat(chat_id=chat_id, group_name=group_title)
                session.add(new_group)
                await session.commit()
        
        # We can try to send a message to the group
        try:
            await event.bot.send_message(
                chat_id, 
                f"Привет! Я EduTest Bot. Группа '{group_title}' успешно зарегистрирована в системе для получения уведомлений."
            )
        except Exception:
            pass
