import os

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from sheets import add_expense

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """start template"""
    pass


async def command1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


async def command2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


# Функция для регистрации команд в BotFather
async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand("start", "Начало работы с ботом")
    ]
    await application.bot.set_my_commands(bot_commands)

def main() -> None:
    """"""   
    # создаем приложение 
    application = Application.builder().token(os.getenv("BOT_TOKEN")).post_init(post_init).build()

    # добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("command1", command1))
    application.add_handler(CommandHandler("command2", command2))

    # можно добавить отдельные обработки чего угодно
    # сообщения, но не команды
    ## application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # местоположения
    ## application.add_handler(MessageHandler(filters.LOCATION, location))
    # изображения
    ## application.add_handler(MessageHandler(filters.ATTACHMENT, attachment))
    # и тд

    # Запускаем до нажатия Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()