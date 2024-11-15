import os

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
    CallbackQueryHandler
)

from sheets import add_expense

CATEGORIES = {
    'Продукты': 0,
    'Еда вне дома': 1
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Функция для вывода приветственного сообщения ботом'
    await update.message.reply_text('Добро пожаловать в бота! Используйте /add, чтобы добавить трату')


async def enter_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Принимает ответ от пользователя через команду /add <сумма траты>'
    user_id = update.message.from_user.id
    if user_id != int(os.getenv('AUTHORIZED_USER')):
        await update.message.reply_text('У вас нет прав для использования этого бота')
        return
    if len(context.args) != 1:
        await update.message.reply_text('Используйте /add <сумма_траты>')
        return
    try:
        expense = float(context.args[0])  # берем первый аргумент после команды
        context.user_data['expense'] = expense  # в контекст записываем сумму траты
        await ask_for_category(update, context)
    except ValueError:
        await update.message.reply_text('Вы должны указать сумму траты в виде числа')
        return


async def ask_for_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Создает клавиатуру с категориями для выбора пользователем'
    keyboard = [
        [InlineKeyboardButton('Продукты', callback_data='category_Продукты')],
        [InlineKeyboardButton('Еда вне дома', callback_data='category_Еда вне дома')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard) # создаем клавиатуру с опциями выбора
    await update.message.reply_text('Выберите категорию:', reply_markup=reply_markup)


async def add_to_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    'Извлекает сумму траты, категорию из контекста и колбэка и вызывает функцию для работы с api'
    query = update.callback_query
    await query.answer() # ожидаем ответ от запроса

    category_name = query.data.split('_')[1] # отделяем категорию от полного запроса
    category_index = CATEGORIES.get(category_name) # забираем индекс, по которому будем вносить данные в таблицу

    if category_index is None:
        await query.edit_message_text('Неизвестная категория. Попробуйте снова')
        return

    expense = context.user_data.get('expense')
    if expense is None:
        await query.edit_message_text('Произошла ошибка. Пожалуйста, начните с /add')
        return

    try:
        add_expense([expense], category_index) # данные необходимо передавать в виде списка
        if expense == int(expense):
            expense = int(expense)
        await query.edit_message_text(f'Сумма {expense} добавлена в категорию {category_name}')
    except Exception as e:
        await query.edit_message_text(f'Произошла ошибка при добавлении данных: {e}')



async def post_init(application: Application) -> None:
    bot_commands = [
        BotCommand('start', 'Начало работы с ботом'),
        BotCommand('add', 'Добавить трату')
    ]
    await application.bot.set_my_commands(bot_commands)


def main() -> None:
    application = Application.builder().token(os.getenv('BOT_TOKEN')).post_init(post_init).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add', enter_expense))
    application.add_handler(CallbackQueryHandler(add_to_sheet, pattern='^category_')) # обработчик колбэка с паттерном

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
