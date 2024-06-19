#main.py - запуск приложения.

# Импорт стандартных библиотек Python
import time  # Работа со временем
import sqlite3  # Работа с базой данных SQLite
import asyncio  # Асинхронное программирование
import traceback  # Работа с трассировками ошибок
import logging  # Логирование


# Импорт сторонних библиотек
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # Планировщик задач
import pytz  # Работа с часовыми поясами
import aiosqlite  # Асинхронная работа с SQLite
import nest_asyncio # Асинхронная работа

# Импорт модулей Telegram
from telegram import Bot  # Базовый класс бота
from telegram import (
  Update,
  Message,
  Chat,
  User,
    # другие классы
)
from datetime import datetime
from telegram.error import TelegramError  # Обработка ошибок Telegram
from telegram.ext import (  # Обработчики событий Telegram
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
    Application,
    Updater,
)
from queue import Queue
# Импорт конфигурации проекта
from config import BOT_TOKEN, GROUP_ID  # Токен бота и идентификатор группы

# Импорт обработчиков и состояний из модуля handlers
from handlers import (
    handle_message,            # Обработчик сообщений
    handle_admin_action,       # Обработчик действий администратора
    handle_domain_action,      # Обработчик действий с доменами
    handle_delete_word,        # Обработчик удаления слов
    handle_admin_list_action,  # Обработчик списка администраторов
    handle_admins_settings,    # Обработчик настроек администраторов
    handle_ads_settings,       # Обработчик настроек рекламы
    handle_admin_management,   # Обработчик управления администраторами
    is_allowed_link,           # Функция проверки разрешенной ссылки
    handle_domains_settings,   # Обработчик настроек доменов
    add_domain,                # Функция добавления домена
    delete_domain,             # Функция удаления домена
    get_allowed_domains,       # Функция получения разрешенных доменов
    handle_spam,               # Обработчик спама
    admin_command,             # Обработчик команды администратора
    receive_ad_message,        # Обработчик получения рекламного сообщения
    ADDING_DOMAIN,             # Состояние добавления домена
    DELETING_DOMAIN            # Состояние удаления домена
)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Список администраторов
ADMINS = [860730368]

# Глобальная переменная для хранения рекламного сообщения
ad_message = ""

# Глобальная переменная для хранения запрещенных слов
restricted_words = []

# Асинхронная функция для инициализации базы данных
async def init_database(application):
    """Создает соединение с базой данных и инициализирует таблицы."""
    application.bot_data["db_conn"] = await aiosqlite.connect("bot_database.db")
    db = application.bot_data["db_conn"]
    async with db.cursor() as cursor:
        application.bot_data["db_cursor"] = cursor
        logger.info("2. Соединение с БД установлено")

        # Создание таблиц
        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS allowed_domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL
            )
            """
        )
        logger.info("3. Таблица 'allowed_domains' создана/существует")

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS restricted_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL
            )
            """
        )
        logger.info("4. Таблица 'restricted_words' создана/существует")

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL
            )
            """
        )
        logger.info("5. Таблица 'admins' создана/существует")

        # Загрузка запрещенных слов из базы данных
        await cursor.execute("SELECT word FROM restricted_words")
        rows = await cursor.fetchall()
        global restricted_words
        restricted_words = [row[0].lower() for row in rows]
        logger.info("6. Запрещенные слова загружены из базы данных")

    await db.commit()

# Функция для запуска планировщика задач
async def run_scheduler(bot: Bot):
    """Запускает планировщик задач для отправки рекламы."""
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))

    # Функция для отправки рекламы
    async def send_ads(context: ContextTypes.DEFAULT_TYPE):
        """Отправляет рекламное сообщение в группу."""
        await context.bot.send_message(chat_id=GROUP_ID, text=ad_message)

    # Добавляем задачу в планировщик
    scheduler.add_job(send_ads, 'interval', hours=1, args=[bot])
    scheduler.start()
    logger.info("Планировщик задач запущен")

# Функция для создания приложения и настройки обработчиков
async def main():
    update_queue = Queue()
    app = ApplicationBuilder().token(BOT_TOKEN).update_queue(update_queue).build()
    nest_asyncio.apply()
    await init_database(app)
    update = Update(
        0,
        message=Message(
            0,
            datetime.now(),
            Chat(id="test", type=Chat.GROUP)
        )
    )
    await process_update(update)

    # Настройка команд и обработчиков сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("admin_action", handle_admin_action))
    app.add_handler(CommandHandler("domain_action", handle_domain_action))
    app.add_handler(CommandHandler("delete_word", handle_delete_word))
    app.add_handler(CommandHandler("admin_list_action", handle_admin_list_action))
    app.add_handler(CommandHandler("add_domain", add_domain))
    app.add_handler(CommandHandler("domains_settings", handle_domains_settings))
    app.add_handler(CommandHandler("admins_settings", handle_admins_settings))
    app.add_handler(CommandHandler("ads_settings", handle_ads_settings))

    # Запуск планировщика задач
    bot = app.bot
    await run_scheduler(bot)

    # Запуск приложения
    logger.info("Инициализация приложения...")
    await app.initialize()
    logger.info("Приложение инициализировано")

    logger.info("Запуск приложения...")
    await app.start()
    logger.info("Приложение запущено")

    logger.info("Запуск polling...")
    # await app.run_polling()
    # logger.info("Polling завершен")
async def process_update(update):

  import pdb; pdb.set_trace()

  await handle_message(update, app)

if __name__ == '__main__':
    asyncio.run(main())

