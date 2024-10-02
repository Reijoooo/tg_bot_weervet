import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import asyncpg
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Подключение к базе данных PostgreSQL
async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)

db_pool = None

# Обработка данных, которые поступают из Mini App
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def web_app_data_handler(message: types.Message):
    try:
        web_app_data = message.web_app_data.data
        data = json.loads(web_app_data)
        
        if data.get('action') == 'add_pet':
            pet = data['petData']
            user_id = message.from_user.id  # ID пользователя в Telegram

            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO pets (user_id, name, date_birth, sex, breed, color, weight, sterilized, town, keeping)
                    VALUES ((SELECT user_id FROM users WHERE telegram_id = $1), $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    user_id, pet['name'], pet['birthdate'], pet['sex'], pet['breed'], pet['color'], 
                    float(pet['weight']), pet['sterilized'], pet['town'], pet['keeping']
                )

            await message.answer(f"Питомец {pet['name']} успешно добавлен!")
    except Exception as e:
        await message.answer(f"Ошибка при добавлении питомца: {e}")

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # Отправляем приветственное сообщение с кнопкой для открытия Mini App
    web_app_button = types.KeyboardButton(text="Добавить питомца", web_app=types.WebAppInfo(url="http://127.0.0.1:5000"))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(web_app_button)
    await message.answer("Добро пожаловать! Нажмите на кнопку ниже, чтобы добавить питомца.", reply_markup=keyboard)

if __name__ == '__main__':
    async def on_startup(dp):
        global db_pool
        db_pool = await create_db_pool()
        print("Бот запущен и готов к работе")

    async def on_shutdown(dp):
        await db_pool.close()

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
