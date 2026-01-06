import os
import sys
import threading
import logging
from flask import Flask
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Roblox Cookie Bot is RUNNING! <a href='/health'>Check health</a>"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/start')
def start_bot():
    return """
    <h1>Бот уже запущен!</h1>
    <p>Бот автоматически запускается при старте сервера.</p>
    <p>Проверьте логи для статуса.</p>
    """

def run_bot():
    """Запуск бота в отдельном потоке с собственным event loop"""
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        from bot import main
        main()
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        import traceback
        traceback.print_exc()

# Запускаем бот при старте
logger.info("🚀 Запускаем бота в отдельном потоке...")
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Веб-сервер запускается на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
