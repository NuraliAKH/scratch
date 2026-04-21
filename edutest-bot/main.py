import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database.db import init_db

logging.basicConfig(level=logging.INFO)

async def main():
    await init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    from handlers import registration, teacher, student, admin, groups, championship, statistics, manage_groups
    dp.include_router(registration.router)
    dp.include_router(teacher.router)
    dp.include_router(student.router)
    dp.include_router(admin.router)
    dp.include_router(groups.router)
    dp.include_router(championship.router)
    dp.include_router(statistics.router)
    dp.include_router(manage_groups.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
