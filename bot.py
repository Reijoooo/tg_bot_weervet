import os
import asyncpg
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from datetime import datetime  # Добавляем импорт библиотеки datetime

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Подключаемся к базе данных
async def create_db_pool():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        async with pool.acquire() as conn:
            await conn.execute('SELECT 1')
        print("Подключение к базе данных успешно")
        return pool
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        raise

db_pool = None

# Команда /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    try:
        telegram_id = message.from_user.id  # Получаем Telegram ID пользователя
        name = message.from_user.first_name  # Получаем имя пользователя (first_name)

        # Подключаемся к базе данных и вставляем пользователя в таблицу users, если его ещё нет
        async with db_pool.acquire() as conn:
            user_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id = $1)", telegram_id
            )

            if not user_exists:
                await conn.execute(
                    """
                    INSERT INTO users (telegram_id, name) 
                    VALUES ($1, $2)
                    """, telegram_id, name
                )
                await message.answer(f"Привет, {name}! Я записал тебя в базу данных.")
            else:
                await message.answer(f"С возвращением, {name}!")

        await message.answer("Используй команды:\n"
                             "/add_pet - добавить питомца\n"
                             "/add_disease - добавить болезнь\n"
                             "/view_pets - показать всех питомцев")
    
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

# Добавление питомца
@dp.message_handler(commands=['add_pet'])
async def add_pet(message: types.Message):
    await message.answer("Введите данные о питомце в формате:\n"
                         "Имя, Дата рождения (ГГГГ-ММ-ДД), Пол (М/Ж), Порода, Цвет, Вес, Стерилизован (Да/Нет), Город, Условия содержания")
    dp.register_message_handler(process_add_pet)

async def process_add_pet(message: types.Message):
    try:
        user_id = message.from_user.id
        data = message.text.split(',')
        if len(data) != 9:
            await message.answer("Ошибка: необходимо ввести все 9 полей через запятую.")
            return

        name, birth_date_str, sex, breed, color, weight, sterilized, town, keeping = [x.strip() for x in data]
        weight = float(weight)

        # Преобразуем строку даты рождения в объект datetime.date
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            await message.answer("Ошибка: неверный формат даты. Используйте формат ГГГГ-ММ-ДД.")
            return

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pets (user_id, name, date_birth, sex, breed, color, weight, sterilized, town, keeping)
                VALUES ((SELECT user_id FROM users WHERE telegram_id = $1), $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id, name, birth_date, sex, breed, color, weight, sterilized, town, keeping
            )
            await message.answer(f"Питомец {name} успешно добавлен!")
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении питомца: {e}")
        await message.answer("Произошла ошибка при добавлении питомца. Попробуйте позже.")

# Просмотр всех питомцев пользователя
@dp.message_handler(commands=['view_pets'])
async def view_pets(message: types.Message):
    try:
        user_id = message.from_user.id
        async with db_pool.acquire() as conn:
            pets = await conn.fetch(
                """
                SELECT p.name, p.date_birth, p.breed, p.color, p.weight
                FROM pets p
                JOIN users u ON p.user_id = u.user_id
                WHERE u.telegram_id = $1
                """, user_id
            )
            
            if not pets:
                await message.answer("У вас нет питомцев.")
            else:
                response = "Ваши питомцы:\n"
                for pet in pets:
                    
                    disease_curent = await conn.fetch(
                        """
                        SELECT m.allergy, m.chronic_diseases, m.diseases[counter], m.recommendations[counter]
                        FROM medical_card m
                        JOIN pets p ON m.pet_id = p.pet_id
                        WHERE u.telegram_id = $1
                        """, user_id
                        )

                    response += f"Имя: {pet['name']}, Дата рождения: {pet['date_birth']}, Порода: {pet['breed']}, Цвет: {pet['color']}, Вес: {pet['weight']} кг, 
                    Аллергия: {disease_curent['allergy']}, Хронические болезни: {disease_curent[chronic_diseases]}, Текущая болезнь: {disease_curent[diseases[counter]]}, 
                    Текущие рекомендации: {disease_curent[recommendations[counter]]}\n\n"
                await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при просмотре питомцев: {e}")
        await message.answer("Произошла ошибка при просмотре питомцев. Попробуйте позже.")

# Добавление болезни в медицинскую карту
@dp.message_handler(commands=['add_disease'])
async def add_disease(message: types.Message):
    await message.answer("Введите данные о болезни в формате:\n"
                         "Имя питомца, Болезнь, Рекомендация")
    dp.register_message_handler(process_add_disease)

async def process_add_disease(message: types.Message):

    try:
        data_disease = message.text.split(',')
        if len(data_disease) != 3:
            await message.answer("Ошибка: необходимо ввести 3 поля (Имя питомца, Болезнь, Рекомендация) через запятую.")
            return

        name, diseases, recommendations = [x.strip() for x in data_disease]

        telegram_id = message.from_user.id

        diseases_list = [diseases]
        recommendations_list = [recommendations]

        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, diseases, recommendations)
                    VALUES ($1, $2, $3)
                    """, pet_id, diseases_list, recommendations_list
                )
                await message.answer(f"Болезнь '{diseases}' и рекомендация '{recommendations}' добавлены для питомца с именем {name}.")
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET diseases = array_append(diseases, $1),
                    recommendations = array_append(recommendations, $2)
                WHERE pet_id = $3
                """, diseases, recommendations, pet_id
                )
                await message.answer(f"Болезнь '{diseases}' и рекомендация '{recommendations}' добавлены для питомца с именем {name}.")

    except Exception as e:
        logger.error(f"Ошибка при добавлении болезни: {e}")
        await message.answer("Произошла ошибка при добавлении болезни. Попробуйте позже.")

# Запуск бота
if __name__ == '__main__':

    async def on_startup(dp):
        global db_pool
        db_pool = await create_db_pool()
        print("Бот инициализирован")

    async def on_shutdown(dp):
        await db_pool.close()

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)