# Импорты для работы с Telegram API и асинхронностью
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ContextTypes

# Импорт для работы с базой данных
import sqlite3

# Обработчик колбека для удаления запрещенных слов
async def handle_delete_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    word_to_delete = query.data.split('_')[1]

    # Попытка удалить слово из базы данных
    try:
        conn = sqlite3.connect('bot_database.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM restricted_words WHERE word = ?", (word_to_delete,))
        conn.commit()
    except sqlite3.Error as e:
        await query.edit_message_text(text=f"Ошибка при удалении слова: {e}")
    finally:
        conn.close()

    # Уведомление пользователя об удалении слова
    await query.edit_message_text(text=f"Слово '{word_toKdelete}' удалено из списка запрещенных.")

# Функция для обработки настроек рекламы
async def handle_ads_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.message.reply_text("Пришлите рекламное сообщение:")
    context.user_data['waiting_for_ad_message'] = True

# Функция для получения рекламного сообщения
async def receive_ad_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'waiting_for_ad_message' in context.user_data and context.user_data['waiting_for_ad_message']:
        ad_message = update.message.text
        await update.message.reply_text("Рекламное сообщение сохранено.")
        context.user_data['waiting_for_ad_message'] = False
        # Здесь можно добавить логику сохранения сообщения в базу данных или другое хранилище

# Файл закончен.