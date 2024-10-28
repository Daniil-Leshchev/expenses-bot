import os

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from sheets import add_expense


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Добро пожаловать в бота! Используйте /add, чтобы добавить трату')


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text('Используйте /add <сумма_траты>')
        return
    try:
        expense = float(context.args[0])
    except ValueError:
        await update.message.reply_text('Вы должны указать сумму траты в виде числа')
        return

    try:
        add_expense([expense])
        await update.message.reply_text('Трата успешно добавлена')
    except Exception as e:
        await update.message.reply_text(f'Произошла ошибка: {e}')


async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand("start", "Начало работы с ботом"),
        BotCommand("add", "Добавить трату")
    ]
    await application.bot.set_my_commands(bot_commands)


def main() -> None:
    application = Application.builder().token(os.getenv("BOT_TOKEN")).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
