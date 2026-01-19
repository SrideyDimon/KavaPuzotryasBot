import aiosqlite

DB_NAME = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER,
            user_id INTEGER,
            username TEXT,
            messages INTEGER DEFAULT 0,
            praises INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS images (
            chat_id INTEGER,
            file_id TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS np_tasks (
            chat_id INTEGER,
            text TEXT,
            date TEXT
        )
        """)
        await db.commit()


async def ensure_user(chat_id, user):
    if user.is_bot:
        return
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (chat_id, user_id, username) VALUES (?, ?, ?)",
            (chat_id, user.id, user.username)
        )
        await db.execute(
            "UPDATE users SET messages = messages + 1 WHERE chat_id=? AND user_id=?",
            (chat_id, user.id)
        )
        await db.commit()


async def add_praise(chat_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET praises = praises + 1 WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        await db.commit()


async def get_top(chat_id, limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT username, messages, praises FROM users WHERE chat_id=? ORDER BY praises DESC, messages DESC LIMIT ?",
            (chat_id, limit)
        )
        return await cursor.fetchall()


async def get_user_stat(chat_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT messages, praises FROM users WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        )
        return await cursor.fetchone()


async def get_random_image(chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT file_id FROM images WHERE chat_id=? ORDER BY RANDOM() LIMIT 1",
            (chat_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
