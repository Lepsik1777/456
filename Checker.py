import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = "6994631863:AAHA929qANrHUSzmXjKCoKsk-mna8ePZqLk"  # Replace with your actual token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"Hello {update.effective_user.first_name}! 👋"
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Use asyncio.run() to run the bot
    asyncio.run(application.initialize())
    asyncio.run(application.start())
    asyncio.run(application.run_polling())