import aiosqlite
import asyncio
from config import GROUP_ID

async def get_allowed_domains(context):
    async with context.bot_data['db_conn'].execute("SELECT domain FROM allowed_domains") as cursor:
        return [row[0] for row in await cursor.fetchall()]

async def add_admin(admin_id):
    async with aiosqlite.connect('bot_database.db') as db:
        try:
            await db.execute("INSERT INTO users (telegram_id, role) VALUES (?, 'admin')", (admin_id,))
            await db.commit()
        except aiosqlite.IntegrityError:
            # Обработка случая, когда пользователь уже есть в базе
            pass

async def delete_admin(admin_id):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute("DELETE FROM users WHERE telegram_id=? AND role='admin'", (admin_id,))
        await db.commit()

async def get_admins(context):
    async with context.bot_data['db_conn'].execute("SELECT telegram_id FROM users WHERE role='admin'") as cursor:
        return [row[0] for row in await cursor.fetchall()]

async def update_admin_role(context, admin_id, role):
    async with context.bot_data['db_conn'].execute("UPDATE users SET role=? WHERE telegram_id=?", (role, admin_id)) as cursor:
        await context.bot_data['db_conn'].commit()

async def send_ads(context):
    async with context.bot_data['db_conn'].execute("SELECT message, interval FROM ads") as cursor:
        ads = await cursor.fetchall()

        for ad_message, interval in ads:
            await context.bot.send_message(chat_id=GROUP_ID, text=ad_message)
            await asyncio.sleep(interval)

async def init_database(application):
    application.bot_data['db_conn'] = await aiosqlite.connect('bot_database.db')
    application.bot_data['db_cursor'] = await application.bot_data['db_conn'].cursor()