# handlers.py - регистрация обработчиков

from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    Dispatcher
)
from message_handler import handle_message
from command_handler import handle_command
from callback_handler import handle_callback

def register_handlers(dp: Dispatcher):
    """
    Регистрирует обработчики для команд, текстовых сообщений и колбэк-запросов в Telegram боте.

    Args:
    dp (Dispatcher): Диспетчер бота, к которому будут добавлены обработчики.
    """
    # Регистрация обработчика для текстовых сообщений
    dp.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Регистрация обработчика для команды /start
    dp.add_handler(CommandHandler("start", handle_command))

    # Регистрация обработчика для колбэк-запросов (обычно используемых в inline-кнопках)
    dp.add_handler(CallbackQueryHandler(handle_callback))