import asyncio
import random
import os
from datetime import datetime

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import aiosqlite

from db import init_db, ensure_user, add_praise, get_top, get_user_stat, get_random_image, DB_NAME

# ------------------ Загрузка токена ------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

WISHES = [
    "вот бы у тебя разрядился телефон в самый нужный момент",
    "не шагу в перёд",
    "Пусть всё получится",
    "Сегодня твой день"
]

WHOAMI = [
    "эксперт по водке",
    "главный по сплетням",
    "беременный(ая) фури",
    "нетакуся просто"
]

scheduled = []

# ------------------ Фото ------------------
@dp.message(F.photo)
async def save_photo(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO images (chat_id, file_id) VALUES (?, ?)",
            (message.chat.id, message.photo[-1].file_id)
        )
        await db.commit()

# ------------------ Команды ------------------
@dp.message(Command("coin"))
async def coin(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    await message.answer(random.choice(["Орёл 🦅", "Решка 🪙"]))

@dp.message(Command("iq"))
async def iq(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    await message.answer(f"Твой IQ: {random.randint(0,200)}")

@dp.message(Command("wish"))
async def wish(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    await message.answer(random.choice(WISHES))

@dp.message(Command("whoim"))
async def whoim(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    await message.answer(f"Ты — {random.choice(WHOAMI)} 😄")

@dp.message(Command("helpthisbot"))
async def help_bot(message: Message):
    await message.answer(
        "/coin /iq /wish /whoim /shipp /kiss /slap /top /mestat /np /randomimage\n"
        "+ или ww (ответом) — похвала"
    )

# ------------------ Похвала ------------------
@dp.message(lambda message: message.text and message.text.lower() in ["+", "ww"] and message.reply_to_message)
async def praise_handler(message: Message):
    reply = message.reply_to_message
    if not reply.from_user.is_bot:
        await add_praise(message.chat.id, reply.from_user.id)
        await message.reply(f"{reply.from_user.full_name} получил похвалу! 👍")

# ------------------ /top ------------------
@dp.message(Command("top"))
async def top(message: Message):
    top_list = await get_top(message.chat.id, 10)
    if not top_list:
        await message.answer("Пока нет данных")
        return
    text = "🏆 Топ участников:\n"
    for i, (username, messages, praises) in enumerate(top_list, 1):
        text += f"{i}. {username} — сообщений: {messages}, похвал: {praises}\n"
    await message.answer(text)

# ------------------ /mestat ------------------
@dp.message(Command("mestat"))
async def mestat(message: Message):
    await ensure_user(message.chat.id, message.from_user)
    stat = await get_user_stat(message.chat.id, message.from_user.id)
    if not stat:
        await message.answer("Статистика отсутствует")
        return
    messages, praises = stat
    await message.answer(f"Ты написал {messages} сообщений и получил {praises} похвал")

# ------------------ /randomimage ------------------
@dp.message(Command("randomimage"))
async def randomimage(message: Message):
    file_id = await get_random_image(message.chat.id)
    if not file_id:
        await message.answer("Фото не найдено")
        return
    await message.answer_photo(file_id)

# ------------------ /kiss /slap ------------------
@dp.message(Command("kiss"))
async def kiss(message: Message):
    if not message.reply_to_message or message.reply_to_message.from_user.is_bot:
        await message.reply("Ответь на сообщение человека, чтобы поцеловать его")
        return
    await message.answer(f"{message.from_user.full_name} поцеловал {message.reply_to_message.from_user.full_name} ❤️")

@dp.message(Command("slap"))
async def slap(message: Message):
    if not message.reply_to_message or message.reply_to_message.from_user.is_bot:
        await message.reply("Ответь на сообщение человека, чтобы дать пощечину")
        return
    await message.answer(f"{message.from_user.full_name} дал пощечину {message.reply_to_message.from_user.full_name} 🤚")

# ------------------ /shipp ------------------
@dp.message(Command("shipp"))
async def shipp(message: Message):
    # Убедимся, что автор команды зарегистрирован
    await ensure_user(message.chat.id, message.from_user)
    
    # Получаем всех пользователей в базе для этого чата
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id, username FROM users WHERE chat_id=?",
            (message.chat.id,)
        )
        users = await cursor.fetchall()

    if len(users) < 2:
        await message.answer("Недостаточно активных участников для пары 😅\n(нужно хотя бы 2 человека, которые писали сообщения)")
        return

    # Выбираем случайную пару
    u1, u2 = random.sample(users, 2)
    await message.answer(f"❤️ Пара года: {u1[1]} + {u2[1]} ❤️")

# ------------------ /np ------------------
@dp.message(Command("np"))
async def np(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("Используй: /np текст ДД.ММ.ГГГГ")
        return
    text = parts[1]
    date = parts[2]
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO np_tasks (chat_id, text, date) VALUES (?, ?, ?)", (message.chat.id, text, date))
        await db.commit()
    await message.reply(f"Задача '{text}' запланирована на {date}")

# ------------------ Debug для остальных сообщений ------------------
@dp.message(lambda message: True)
async def debug_messages(message: Message):
    print(f"[DEBUG] {message.chat.id} | {message.from_user.username}: {message.text}")

# ------------------ Планировщик ------------------
async def scheduler():
    while True:
        now = datetime.now().strftime("%d.%m.%Y")
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT chat_id, text, date FROM np_tasks WHERE date=?", (now,))
            rows = await cursor.fetchall()
            for chat_id, text, date in rows:
                await bot.send_message(chat_id, text)
        await asyncio.sleep(60)

# ------------------ Main ------------------
async def main():
    await init_db()
    asyncio.create_task(scheduler())
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
