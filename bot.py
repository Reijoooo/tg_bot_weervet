import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

# Логирование для отслеживания ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Создаем планировщик
scheduler = BackgroundScheduler()
scheduler.start()

# Функция для отправки напоминания
async def send_reminder(chat_id, text, bot):
    await bot.send_message(chat_id=chat_id, text=f"Напоминание: {text}")

# Обертка для запуска асинхронных функций в синхронном контексте
def run_async_task(chat_id, text, bot):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_reminder(chat_id, text, bot))

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Используйте команду /remind, чтобы добавить напоминание.")

# Вызов выбора даты
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(str(i), callback_data=f"day_{i}") for i in range(1, 32)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите день:", reply_markup=reply_markup)

# Обработка выбора дня
async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    day = int(query.data.split("_")[1])
    
    # Сохраните выбранный день
    context.user_data['day'] = day

    # Запрос времени
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"{hour:02d}:00", callback_data=f"hour_{hour}") for hour in range(24)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Выберите час:", reply_markup=reply_markup)

# Обработка выбора часа
async def hour_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    hour = int(query.data.split("_")[1])
    
    # Сохраните выбранный час
    context.user_data['hour'] = hour

    # Запрос повторений
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("1 раз", callback_data="repeat_1"),
         InlineKeyboardButton("Каждый день", callback_data="repeat_daily"),
         InlineKeyboardButton("Каждую неделю", callback_data="repeat_weekly"),
         InlineKeyboardButton("Каждый месяц", callback_data="repeat_monthly")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("Выберите повторение:", reply_markup=reply_markup)

# Обработка выбора повторений
async def repeat_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    repeat = query.data.split("_")[1]
    
    # Получение сохраненных данных
    day = context.user_data.get('day')
    hour = context.user_data.get('hour')

    # Получение текущей даты
    now = datetime.now()
    reminder_date = datetime(now.year, now.month, day, hour)

    # Если время уже прошло, устанавливаем на следующий день
    if reminder_date < now:
        reminder_date += timedelta(days=1)

    # Устанавливаем напоминание
    if repeat == 'daily':
        scheduler.add_job(
            run_async_task,
            trigger='cron',
            hour=hour,
            minute=0,
            day='*',
            month='*',
            year='*',
            kwargs={'chat_id': update.effective_chat.id, 'text': f"Напоминание на {reminder_date}", 'bot': context.bot},
            replace_existing=True
        )
    elif repeat == 'weekly':
        scheduler.add_job(
            run_async_task,
            trigger='cron',
            hour=hour,
            minute=0,
            day='*',
            month='*',
            day_of_week='*',  # Каждый день недели
            kwargs={'chat_id': update.effective_chat.id, 'text': f"Напоминание на {reminder_date}", 'bot': context.bot},
            replace_existing=True
        )
    elif repeat == 'monthly':
        scheduler.add_job(
            run_async_task,
            trigger='cron',
            hour=hour,
            minute=0,
            day=day,  # Устанавливаем на выбранный день месяца
            kwargs={'chat_id': update.effective_chat.id, 'text': f"Напоминание на {reminder_date}", 'bot': context.bot},
            replace_existing=True
        )
    else:
        scheduler.add_job(
            run_async_task,
            trigger=DateTrigger(run_date=reminder_date),
            kwargs={'chat_id': update.effective_chat.id, 'text': f"Напоминание на {reminder_date}", 'bot': context.bot},
            replace_existing=True
        )

    await query.answer()
    await query.message.reply_text(f"Напоминание установлено на {reminder_date} с повторением: {repeat}.")

# Запуск приложения бота
if __name__ == '__main__':
    app = ApplicationBuilder().token('7629897895:AAHAiHvZA5rk8UKfilMeLyYZR7ckrpGo3DQ').build()

    # Добавляем обработчики команд и колбеков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CallbackQueryHandler(day_selected, pattern=r'^day_'))
    app.add_handler(CallbackQueryHandler(hour_selected, pattern=r'^hour_'))
    app.add_handler(CallbackQueryHandler(repeat_selected, pattern=r'^repeat_'))

    # Запуск опроса сообщений
    app.run_polling()
