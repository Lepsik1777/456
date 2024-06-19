#domain_handler.py - логика доменов

from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from admin_utils import get_allowed_domains

async def handle_domains_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = context.callback_query  # Изменено
    keyboard = [
        [InlineKeyboardButton("Добавить домен", callback_data='add_domain')],
        [InlineKeyboardButton("Удалить домен", callback_data='delete_domain')],
        [InlineKeyboardButton("Показать домены", callback_data='show_domains')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=query.message.chat_id, text="Управление доменами:", reply_markup=reply_markup)

async def handle_domain_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = context.callback_query  # Изменено
    action = query.data

    if action == 'add_domain':
        await context.bot.send_message(chat_id=query.message.chat_id, text="Введите домен для добавления:")
        return ADDING_DOMAIN
    elif action == 'delete_domain':
        await context.bot.send_message(chat_id=query.message.chat_id, text="Введите домен для удаления:")
        return DELETING_DOMAIN
    elif action == 'show_domains':
        allowed_domains = await get_allowed_domains()
        if allowed_domains:
            domains_list = "\n".join(allowed_domains)
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"Разрешенные домены:\n{domains_list}")
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Список разрешенных доменов пуст.")
        return ConversationHandler.END
async def add_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    domain = update.message.text.strip().lower()
    async with aiosqlite.connect('database.db') as db:
        try:
            await db.execute("INSERT INTO allowed_domains (domain) VALUES (?)", (domain,))
            await db.commit()
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"Домен '{domain}' добавлен в список разрешенных.")
        except aiosqlite.IntegrityError:
            await context.bot.send_message(chat_id=update.message.chat_id, text=f"Домен '{domain}' уже существует в списке разрешенных.")
    return ConversationHandler.END
async def delete_domain(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    domain = update.message.text.strip().lower()
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("DELETE FROM allowed_domains WHERE domain=?", (domain,)) as cursor:
            await db.commit()
            if cursor.rowcount > 0:
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"Домен '{domain}' удален из списка разрешенных.")
            else:
                await context.bot.send_message(chat_id=update.message.chat_id, text=f"Домена '{domain}' нет в списке разрешенных.")
    return ConversationHandler.END
async def get_allowed_domains():
    async with aiosqlite.connect('database.db') as db:
        async with db.execute("SELECT domain FROM allowed_domains") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]