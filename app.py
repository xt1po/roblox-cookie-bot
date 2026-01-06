import os
import sys
import threading
import logging
from flask import Flask

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Roblox Cookie Bot is LIVE! <a href='/start_bot'>Запустить бота</a>"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/start_bot')
def start_bot():
    """Запуск бота вручную"""
    try:
        # Проверяем переменные
        token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if not token:
            return "❌ BOT_TOKEN не установлен", 500
        
        logger.info(f"🚀 Запускаем бота...")
        logger.info(f"Токен: {token[:10]}...")
        logger.info(f"Админ ID: {admin_id}")
        
        # Запускаем бота в отдельном потоке
        def run_bot():
            try:
                from bot import RobloxCookieBot
                bot = RobloxCookieBot()
                bot.run()
            except Exception as e:
                logger.error(f"❌ Ошибка бота: {e}", exc_info=True)
        
        if not hasattr(app, 'bot_thread') or not app.bot_thread.is_alive():
            app.bot_thread = threading.Thread(target=run_bot, daemon=True)
            app.bot_thread.start()
            return "✅ Бот запущен! Проверьте логи Render."
        else:
            return "⚠️ Бот уже запущен"
            
    except Exception as e:
        logger.error(f"❌ Ошибка запуска: {e}", exc_info=True)
        return f"❌ Ошибка: {str(e)}", 500

@app.route('/check')
def check():
    """Проверка переменных и статуса"""
    token = os.getenv('BOT_TOKEN', 'НЕ УСТАНОВЛЕН')
    admin_id = os.getenv('ADMIN_ID', 'НЕ УСТАНОВЛЕН')
    
    bot_status = "❌ НЕ ЗАПУЩЕН"
    if hasattr(app, 'bot_thread') and app.bot_thread.is_alive():
        bot_status = "✅ ЗАПУЩЕН"
    
    return f"""
    <h1>Проверка бота</h1>
    <p><b>BOT_TOKEN:</b> {'✅ Установлен' if token != 'НЕ УСТАНОВЛЕН' else '❌ Отсутствует'}</p>
    <p><b>Длина токена:</b> {len(token)} символов</p>
    <p><b>ADMIN_ID:</b> {admin_id}</p>
    <p><b>Статус бота:</b> {bot_status}</p>
    <p><a href='/start_bot'>🚀 Запустить бота</a></p>
    <p><a href='/'>🏠 Главная</a></p>
    """

# Автоматический запуск при старте
def auto_start_bot():
    """Автозапуск бота при старте сервера"""
    token = os.getenv('BOT_TOKEN')
    admin_id = os.getenv('ADMIN_ID')
    
    if not token:
        logger.error("❌ BOT_TOKEN не найден!")
        return
    
    logger.info("=== АВТОЗАПУСК БОТА ===")
    logger.info(f"Токен: {token[:10]}...")
    logger.info(f"Админ ID: {admin_id}")
    
    # Даем время Flask запуститься
    import time
    time.sleep(2)
    
    try:
        from bot import RobloxCookieBot
        logger.info("✅ Импорт бота успешен")
        
        def run():
            try:
                logger.info("🚀 Запускаем бота Telegram...")
                bot = RobloxCookieBot()
                bot.run()
            except Exception as e:
                logger.error(f"❌ Ошибка в боте: {e}", exc_info=True)
        
        # Запускаем в отдельном потоке
        app.bot_thread = threading.Thread(target=run, daemon=True)
        app.bot_thread.start()
        logger.info("✅ Бот запущен в отдельном потоке")
        
    except ImportError as e:
        logger.error(f"❌ Не могу импортировать bot.py: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка автозапуска: {e}", exc_info=True)

# Запускаем автозапуск при импорте
if __name__ == "__main__":
    # Запускаем автозапуск в отдельном потоке с задержкой
    import time
    time.sleep(1)
    
    start_thread = threading.Thread(target=auto_start_bot, daemon=True)
    start_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запускаем Flask на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
else:
    # При запуске через gunicorn
    logger.info("=== GUNICORN ЗАПУСК ===")
    # Запускаем автозапуск с задержкой
    import time
    time.sleep(3)
    auto_start_bot()
