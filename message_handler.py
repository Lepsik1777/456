from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.error import TelegramError
import sqlite3
import asyncio
import logging

from config import MODERATOR_CHAT_ID
from admin_utils import get_admins, add_admin, delete_admin

logger = logging.getLogger(__name__)

# Структура функций и модульная организация
async def handle_spam(update: Update, context: ContextTypes.DEFAULT_TYPE, forbidden_words: list) -> None:
    user = update.message.from_user
    user_info = f"Пользователь: [{user.first_name}](tg://user?id={user.id}) ({user.username})\n"
    text = update.message.text
    message_info = f"Сообщение: {text}\n"
    forbidden_word_info = f"Запрещенные слова: {', '.join(forbidden_words)}\n"
    log = f"❗️ Спам-фильтр. Заблокирован пользователь с подозрением на спам:\n{user_info}{message_info}{forbidden_word_info}"

    await context.bot.send_message(MODERATOR_CHAT_ID, log, parse_mode='Markdown')
    await context.bot.send_message(
        update.message.chat_id,
        f"🛡 {user.first_name}, Вы были заблокированы навечно за использование запрещенных слов.",
        reply_to_message_id=update.message.message_id,
        parse_mode='Markdown'
    )
    await asyncio.sleep(10)

    try:
        await context.bot.delete_message(update.message.chat_id, update.message.message_id)
        permissions = ChatPermissions(can_send_messages=False, can_read_messages=False)
        await context.bot.restrict_chat_member(update.message.chat_id, user.id, permissions=permissions)
    except TelegramError as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")

async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'waiting_for_admin_id' in context.user_data:
        admin_id = int(update.message.text.strip())
        if admin_id not in get_admins():
            add_admin(admin_id)
            await context.bot.send_message(update.message.chat_id, text=f"ID {admin_id} добавлен в список администраторов.")
        else:
            await context.bot.send_message(update.message.chat_id, text=f"ID {admin_id} уже есть в списке администраторов.")
        del context.user_data['waiting_for_admin_id']

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    forbidden_words = [word for word in ['недопустимое_слово1', 'недопустимое_слово2'] if word in text.lower()]

    if forbidden_words:
        await handle_spam(update, context, forbidden_words)

    await handle_admin_management(update, context)