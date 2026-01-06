from flask import Flask
import threading
import os
import sys

sys.path.append('.')

app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Roblox Cookie Bot is running!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/start')
def start_bot():
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from bot import RobloxCookieBot
        
        def run_bot():
            bot = RobloxCookieBot()
            bot.run()
        
        thread = threading.Thread(target=run_bot, daemon=True)
        thread.start()
        
        return "Bot started!", 200
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
