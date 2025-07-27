from datetime import time as dt_time
from sheets import add_expense, get_monthly_total
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from zoneinfo import ZoneInfo
import os
from functools import wraps


CATEGORIES = {
    'Продукты': 0,
    'Еда вне дома': 1
}

AUTHORIZED_USER_ID = int(os.getenv('AUTHORIZED_USER', '0'))


def authorized_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None or user.id != AUTHORIZED_USER_ID:
            if update.message:
                await update.message.reply_text(
                    'У вас нет прав для использования этого бота'
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    'У вас нет прав для использования этого бота',
                    show_alert=True
                )
            return
        return await func(update, context)
    return wrapper


CATEGORIES = {
    'Продукты': 0,
    'Еда вне дома': 1
}


@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Функция для вывода приветственного сообщения ботом'
    if update.message is None:
        return
    await update.message.reply_text(
        'Добро пожаловать в бота! Используйте /add, чтобы добавить трату'
    )


@authorized_only
async def enter_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Принимает ответ от пользователя через команду /add <сумма траты>'
    if update.message is None or context.user_data is None \
       or update.message.from_user is None:
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


@authorized_only
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


@authorized_only
async def handle_plain_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Обрабатывает ввод только числа как сумму траты'
    if update.message is None or update.message.text is None:
        return
    text = update.message.text.strip()
    context.args = [text]
    await enter_expense(update, context)


async def daily_expense_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await context.bot.send_message(
            chat_id=AUTHORIZED_USER_ID,
            text='Не забудьте записать траты за сегодняшний день'
        )
    except Exception:
        pass


async def get_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    total, remaining = get_monthly_total()
    message = (
        f'Общие траты за месяц: {total} руб.\n'
        f'Остаток: {remaining:.2f} руб.'
    )
    await context.bot.send_message(
        chat_id=AUTHORIZED_USER_ID,
        text=message
    )


async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand('start', 'Начало работы с ботом'),
        BotCommand('add', 'Добавить трату'),
        BotCommand('stats', 'Посмотреть статистику за месяц')
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
    application.add_handler(CommandHandler('stats', get_stats))
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
