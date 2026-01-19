from flask import Flask
import threading
import asyncio
import bot  # это твой bot.py

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает! ✅"

def run_bot():
    asyncio.run(bot.main())

if __name__ == "__main__":
    # Запускаем бот в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=8080)
