import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///edutest.db")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
