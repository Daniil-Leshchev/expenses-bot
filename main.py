import os

from datetime import time as dt_time
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from sheets import add_expense

CATEGORIES = {
    'Продукты': 0,
    'Еда вне дома': 1
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Функция для вывода приветственного сообщения ботом'
    if update.message is None:
        return
    await update.message.reply_text(
        'Добро пожаловать в бота! Используйте /add, чтобы добавить трату'
    )


async def enter_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Принимает ответ от пользователя через команду /add <сумма траты>'
    if not (update.message and context.user_data and update.message.from_user):
        return
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('AUTHORIZED_USER', '0')):
        await update.message.reply_text(
            'У вас нет прав для использования этого бота'
        )
        return
    args = context.args or []
    if len(args) != 1:
        await update.message.reply_text(
            'Используйте /add <сумма_траты>'
        )
        return
    try:
        expense = float(args[0])  # берем первый аргумент после команды
        # в контекст записываем сумму траты
        context.user_data['expense'] = expense
        await ask_for_category(update, context)
    except ValueError:
        await update.message.reply_text(
            'Вы должны указать сумму траты в виде числа'
        )
        return


async def ask_for_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Создает клавиатуру с категориями для выбора пользователем'
    if update.message is None:
        return
    keyboard = [
        [
            InlineKeyboardButton(
                'Продукты',
                callback_data='category_Продукты',
            ),
        ],
        [
            InlineKeyboardButton(
                'Еда вне дома',
                callback_data='category_Еда вне дома',
            ),
        ],
    ]
    # создаем клавиатуру с опциями выбора
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите категорию:', reply_markup=reply_markup)


async def add_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Извлекает сумму траты, категорию из контекста и колбэка и вызывает функцию для работы с api'
    if update.callback_query is None:
        return
    if context.user_data is None:
        return

    query = update.callback_query
    await query.answer()
    if query.data is None:
        return
    parts = query.data.split('_')
    if len(parts) < 2:
        await query.edit_message_text('Неизвестная категория')
        return
    category_name = parts[1]
    # забираем индекс, по которому будем вносить данные в таблицу
    category_index = CATEGORIES.get(category_name)

    if category_index is None:
        await query.edit_message_text(
            'Неизвестная категория. Попробуйте снова'
        )
        return

    expense = context.user_data.get('expense')
    if expense is None:
        await query.edit_message_text(
            'Произошла ошибка. Пожалуйста, начните с /add'
        )
        return

    try:
        # данные необходимо передавать в виде списка
        add_expense([expense], category_index)
        if expense == int(expense):
            expense = int(expense)
        await query.edit_message_text(
            f'Сумма {expense} добавлена в категорию {category_name}'
        )
    except Exception as e:
        await query.edit_message_text(
            f'Произошла ошибка при добавлении данных: {e}'
        )


async def handle_plain_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Обрабатывает ввод только числа как сумму траты'
    if update.message is None or update.message.text is None:
        return
    text = update.message.text.strip()
    context.args = [text]
    await enter_expense(update, context)


async def daily_expense_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = int(os.getenv('AUTHORIZED_USER', '0'))
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text='Не забудьте записать траты за сегодняшний день'
        )
    except Exception:
        pass


async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand('start', 'Начало работы с ботом'),
        BotCommand('add', 'Добавить трату')
    ]
    await application.bot.set_my_commands(bot_commands)


def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token is None:
        return
    application = Application.builder().token(
        bot_token).post_init(post_init).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add', enter_expense))
    application.add_handler(
        CallbackQueryHandler(
            add_to_sheet,
            pattern='^category_',
        )
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d+(\.\d+)?$'),
            handle_plain_expense
        )
    )

    job_queue = application.job_queue
    if job_queue is None:
        return
    job_queue.run_daily(
        daily_expense_reminder,
        time=dt_time(hour=20, minute=0, tzinfo=ZoneInfo('Asia/Yekaterinburg'))
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
