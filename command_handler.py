#command_handler.py - логика обработки команд.

import asyncio
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
)
from telegram.error import TelegramError
from config import BOT_TOKEN, GROUP_ID, MODERATOR_CHAT_ID
from admin_utils import get_allowed_domains

# Константы для состояний диалога
ADDING_DOMAIN = 0  # Состояние добавления домена
DELETING_DOMAIN = 1  # Состояние удаления домена

# Импорт модулей в хендлерс
from message_handler import handle_message
from command_handler import handle_admin_command
from callback_handler import handle_admin_action
from domain_handler import handle_domains_settings

# Функция для обработки команды /admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("У вас нет прав администратора.")
        return

    # Создаем меню действий
    keyboard = [
        [InlineKeyboardButton("Настройки", callback_data='settings')],
        [InlineKeyboardButton("Добавить слово", callback_data='add_word')],
        [InlineKeyboardButton("Удалить слово", callback_data='delete_word')],
        [InlineKeyboardButton("Просмотреть список", callback_data='view_words')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return ConversationHandler.END  # Добавлено

# Функция для обработки настроек администраторов
async def handle_admins_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = context.callback_query  # Изменено
    action = query.data

    chat_id = query.message.chat_id if query.message else update.effective_chat.id

    # Создаем меню администрирования
    keyboard = [
        [InlineKeyboardButton("Добавить администратора", callback_data='add_admin')],
        [InlineKeyboardButton("Удалить администратора", callback_data='delete_admin')],
        [InlineKeyboardButton("Показать администраторов", callback_data='show_admins')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=chat_id, text="Управление администраторами:", reply_markup=reply_markup)

    if action == 'add_admin':
        await context.bot.send_message(chat_id=chat_id, text="Для добавления администратора пришлите его ID:")
        context.user_data['waiting_for_admin_action'] = 'add'  # Устанавливаем флаг ожидания действия
    elif action == 'delete_admin':
        await context.bot.send_message(chat_id=chat_id, text="Для удаления администратора пришлите его ID:")
        context.user_data['waiting_for_admin_action'] = 'delete'  # Устанавливаем флаг ожидания действия

# Обработчик действий администратора
async def handle_admin_list_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = context.callback_query  # Изменено
    action = query.data

    chat_id = query.message.chat_id if query.message else update.effective_chat.id

    if action == 'add_admin':
        await context.bot.send_message(chat_id=chat_id, text="Введите ID администратора для добавления:")
        context.user_data['waiting_for_admin_action'] = 'add'
    elif action == 'delete_admin':
        await context.bot.send_message(chat_id=chat_id, text="Введите ID администратора для удаления:")
        context.user_data['waiting_for_admin_action'] = 'delete'

    # Обработка добавления/удаления администратора
    if 'waiting_for_admin_action' in context.user_data and context.user_data['waiting_for_admin_action']:
        try:
            admin_id = int(update.message.text.strip())
        except (ValueError, AttributeError):
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Неверный формат ID. Введите число.")
            return

        action = context.user_data['waiting_for_admin_action']

        if action == 'add':
            if admin_id not in ADMINS:
                ADMINS.append(admin_id)
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Администратор с ID {admin_id} добавлен.")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Администратор с ID {admin_id} уже существует.")
        elif action == 'delete':
            if admin_id in ADMINS:
                ADMINS.remove(admin_id)
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Администратор с ID {admin_id} удален.")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=f"Администратора с ID {admin_id} нет в списке.")

        del context.user_data['waiting_for_admin_action']

# Функция для обработки действий администратора
async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    action = None  # Определяем action здесь
    if update.callback_query is not None:
        query = update.callback_query
        action = query.data

    if action == 'settings':
        if query.message:  # Проверяем, что query.message не None
            chat_id = query.message.chat_id
            # Создаем меню настроек
            keyboard = [
                [InlineKeyboardButton("Домены", callback_data='domains')],
                [InlineKeyboardButton("Администраторы", callback_data='admins')],
                [InlineKeyboardButton("Реклама", callback_data='ads')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=chat_id, text="Настройки:", reply_markup=reply_markup)
        else:
            # Обработка случая, когда query.message None
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Ошибка: Не могу получить ID чата.")
    elif action == 'domains':
        # Обработка настроек доменов
        await handle_domains_settings(update, context)
        return ConversationHandler.END  # Завершаем диалог
    elif action == 'admins':
        # Обработка настроек администраторов
        await handle_admins_settings(update, context)
        return ConversationHandler.END  # Завершаем диалог
    elif action == 'ads':
        # Обработка настроек рекламы
        await handle_ads_settings(update, context)
        return ConversationHandler.END  # Завершаем диалог

    if action == 'add_word':
        await context.bot.send_message(chat_id=query.message.chat_id, text="Введите слово для добавления:")
        # Устанавливаем флаг, что ожидаем слово для добавления
        context.user_data['waiting_for_word'] = True
    elif action == 'delete_word':
        # Получаем список слов из базы данных
        with sqlite3.connect('bot_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM restricted_words")
            words = [row[0] for row in cursor.fetchall()]

        # Создаем кнопки для каждого слова
        keyboard = []
        for word in words:
            keyboard.append([InlineKeyboardButton(word, callback_data=f'delete_{word}')])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=query.message.chat_id, text="Выберите слово для удаления:", reply_markup=reply_markup)
    elif action == 'view_words':
        # Получаем список слов из базы данных
        with sqlite3.connect('bot_database.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM restricted_words")
            words = [row[0] for row in cursor.fetchall()]

        # Формируем сообщение со списком слов
        words_list = "\n".join(words)
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"Список запрещенных слов:\n{words_list}")