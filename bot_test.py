import os
import asyncpg
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from datetime import datetime
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"DATABASE_URL: {DATABASE_URL}")

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
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


class MedicalCardForm(StatesGroup):
    chronic_disease = State()
    allergy = State()
    disease = State()

class PetsForm(StatesGroup):
    add_pet = State()
    view_pets = State()

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
                return
            else:
                await message.answer(f"С возвращением, {name}!")

        await message.answer("Используй команды:\n"
                             "/add_pet - добавить питомца\n"
                             "/add_disease - добавить болезнь\n"
                             "/view_pets - показать всех питомцев\n"
                             "/add_chronic_diseases - добавить хроническую болезнь\n"
                             "/add_allergy - добавить аллергию")
        return
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return

# Добавление питомца
@dp.message_handler(commands=['add_pet'])
async def add_pet(message: types.Message):
    user_id = message.from_user.id
    async with db_pool.acquire() as conn:
            telegram_id = await conn.fetchval("SELECT EXISTS(SELECT FROM users WHERE telegram_id = $1)", user_id)
    if not telegram_id:
        await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
        return
    
    await message.answer("Введите данные о питомце в формате:\n"
                         "Имя, Дата рождения (ГГГГ-ММ-ДД), Пол (М/Ж), Порода, Цвет, Вес, Стерилизован (Да/Нет), Город, Условия содержания")
    # dp.register_message_handler(process_add_pet)
    await PetsForm.add_pet.set()

@dp.message_handler(state=PetsForm.add_pet)
async def process_add_pet(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        data = message.text.split(',')
        if len(data) != 9:
            await message.answer("Ошибка: необходимо ввести все 9 полей через запятую.")

        name, birth_date_str, sex, breed, color, weight, sterilized, town, keeping = [x.strip() for x in data]
        weight = float(weight)

        # Преобразуем строку даты рождения в объект datetime.date
        try:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError:
            await message.answer("Ошибка: неверный формат даты. Используйте формат ГГГГ-ММ-ДД.")

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pets (user_id, name, date_birth, sex, breed, color, weight, sterilized, town, keeping)
                VALUES ((SELECT user_id FROM users WHERE telegram_id = $1), $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id, name, birth_date, sex, breed, color, weight, sterilized, town, keeping
            )
            await message.answer(f"Питомец {name} успешно добавлен!")
            await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при добавлении питомца: {e}")
        await message.answer("Произошла ошибка при добавлении питомца. Попробуйте позже.")
        await state.finish()

# Просмотр всех питомцев пользователя
@dp.message_handler(commands=['view_pets'])
@dp.message_handler(state=PetsForm.view_pets)
async def process_view_pets(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        async with db_pool.acquire() as conn:
            telegram_id = await conn.fetchval("SELECT EXISTS(SELECT FROM users WHERE telegram_id = $1)", user_id)
        if not telegram_id:
            await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
            await state.finish()
        async with db_pool.acquire() as conn:
            pets = await conn.fetch(
                """
                SELECT p.name, p.date_birth, p.breed, p.color, p.weight, p.pet_id
                FROM pets p
                JOIN users u ON p.user_id = u.user_id
                WHERE u.telegram_id = $1
                """, user_id
            )
            if not pets:
                await message.answer("У вас нет питомцев.")
                await state.finish()
            else:
                response = "Ваши питомцы:\n"
                for pet in pets:
                    disease_curent = await conn.fetchrow(
                        """
                        SELECT 
                            allergy, 
                            chronic_diseases, 
                            diseases[counter] AS current_disease, 
                            recommendations[counter] AS current_recommendation
                        FROM 
                            medical_card
                        WHERE
                            pet_id = $1
                        """, pet['pet_id']
                )
                    # Если медицинская карта есть
                    if disease_curent:
                        allergy = disease_curent['allergy'] if disease_curent['allergy'] else "Нет"
                        chronic_diseases = disease_curent['chronic_diseases'] if disease_curent['chronic_diseases'] else "Нет"
                        current_disease = disease_curent['current_disease'] if disease_curent['current_disease'] else "Нет"
                        current_recommendation = disease_curent['current_recommendation'] if disease_curent['current_recommendation'] else "Нет"
                    else:
                        allergy = chronic_diseases = current_disease = current_recommendation = "Нет данных"

                    # Формируем строку ответа для каждого питомца
                    response += (
                        f"Имя: {pet['name']}, Дата рождения: {pet['date_birth']}, Порода: {pet['breed']}, "
                        f"Цвет: {pet['color']}, Вес: {pet['weight']} кг, "
                        f"Аллергия: {allergy}, Хронические болезни: {chronic_diseases}, "
                        f"Текущая болезнь: {current_disease}, Текущие рекомендации: {current_recommendation}\n\n"
                    )
                await message.answer(response)
                await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при просмотре питомцев: {e}")
        await message.answer("Произошла ошибка при просмотре питомцев. Попробуйте позже.")
        await state.finish()

# Добавление болезни в медицинскую карту
@dp.message_handler(commands=['add_disease'])
async def add_disease(message: types.Message):
    user_id = message.from_user.id
    async with db_pool.acquire() as conn:
        telegram_id = await conn.fetchval("SELECT EXISTS(SELECT FROM users WHERE telegram_id = $1)", user_id)
        if not telegram_id:
            await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
            return
    await message.answer("Введите данные о болезни в формате:\n"
                         "Имя питомца, Болезнь, Рекомендация")
    # dp.register_message_handler(process_add_disease)
    await MedicalCardForm.disease.set()

@dp.message_handler(state=MedicalCardForm.disease)
async def process_add_disease(message: types.Message, state: FSMContext):
    try:
        data_disease = message.text.split(',')
        if len(data_disease) != 3:
            await message.answer("Ошибка: необходимо ввести 3 поля (Имя питомца, Болезнь, Рекомендация) через запятую.")

        name, diseases, recommendations = [x.strip() for x in data_disease]

        telegram_id = message.from_user.id

        diseases_list = [diseases]
        recommendations_list = [recommendations]

        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            if user_id == None:
                await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
                await state.finish()
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            if pet_id == None:
                await message.answer(f"Такого питомца не существует")
                await state.finish()
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, diseases, recommendations)
                    VALUES ($1, $2, $3)
                    """, pet_id, diseases_list, recommendations_list
                )
                await message.answer(f"Болезнь '{diseases}' и рекомендация '{recommendations}' добавлены для питомца с именем {name}.")
                await state.finish()
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
                await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при добавлении болезни: {e}")
        await message.answer("Произошла ошибка при добавлении болезни. Попробуйте позже.")
        await state.finish()

# Добавление хронической болезни в медицинскую карту
@dp.message_handler(commands=['add_chronic_diseases'])
async def add_chronic_diseases(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with db_pool.acquire() as conn:
        telegram_id = await conn.fetchval("SELECT EXISTS(SELECT FROM users WHERE telegram_id = $1)", user_id)
        if not telegram_id:
            await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
            return
    await message.answer("Введите данные о болезни в формате:\n"
                         "Имя питомца, Хроническая болезнь")
    
    # Установите состояние для следующего шага
    await MedicalCardForm.chronic_disease.set()

@dp.message_handler(state=MedicalCardForm.chronic_disease)
async def process_add_chronic_diseases(message: types.Message, state: FSMContext):
    try:
        data_chronic = message.text.split(',')
        if len(data_chronic) != 2:
            await message.answer("Ошибка: необходимо ввести 2 поля (Имя питомца, Хроническая болезнь) через запятую.")
            return
        name, chronic_diseases = [x.strip() for x in data_chronic]
        telegram_id = message.from_user.id
        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            if user_id == None:
                await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
                return
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            if pet_id == None:
                await message.answer(f"Такого питомца не существует")
                return
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, chronic_diseases)
                    VALUES ($1, $2)
                    """, pet_id, chronic_diseases
                )
                await message.answer(f"Хроническая болезнь '{chronic_diseases}' добавлена для питомца с именем {name}.")
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET chronic_diseases = $1
                WHERE pet_id = $2
                """, chronic_diseases, pet_id
                )
                await message.answer(f"Хроническая болезнь '{chronic_diseases}' добавлена для питомца с именем {name}.")
                await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при добавлении хронической болезни: {e}")
        await message.answer("Произошла ошибка при добавлении хронической болезни. Попробуйте позже.")
        # Завершите состояние
        await state.finish()

# Добавление аллергии в медицинскую карту
@dp.message_handler(commands=['add_allergy'])
async def add_allergy(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with db_pool.acquire() as conn:
        telegram_id = await conn.fetchval("SELECT EXISTS(SELECT FROM users WHERE telegram_id = $1)", user_id)
        if not telegram_id:
            await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
            return
    await message.answer("Введите данные о болезни в формате:\n"
                         "Имя питомца, Аллергия")
    
    # Установите состояние для следующего шага
    await MedicalCardForm.allergy.set()
    # dp.register_message_handler(process_add_allergy)

@dp.message_handler(state=MedicalCardForm.allergy)
async def process_add_allergy(message: types.Message, state: FSMContext):
    try:
        print("Я в try аллергии")
        data_allergy = message.text.split(',')
        if len(data_allergy) != 2:
            await message.answer("Ошибка: необходимо ввести 2 поля (Имя питомца, Аллергия) через запятую.")
            return
        name, allergy = [x.strip() for x in data_allergy]
        telegram_id = message.from_user.id
        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            if user_id == None:
                await message.answer(f"Вы не зарегистрировались, введите /start для регистрации")
                return
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            if pet_id == None:
                await message.answer(f"Такого питомца не существует")
                return
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, allergy)
                    VALUES ($1, $2)
                    """, pet_id, allergy
                )
                await message.answer(f"Аллергия '{allergy}' добавлена для питомца с именем {name}.")
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET allergy = $1
                WHERE pet_id = $2
                """, allergy, pet_id
                )
                await message.answer(f"Аллергия '{allergy}' добавлена для питомца с именем {name}.")
                await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при добавлении аллергии: {e}")
        await message.answer("Произошла ошибка при добавлении аллергии. Попробуйте позже.")
        # Завершите состояние
        await state.finish()

# Запуск бота
if __name__ == '__main__':
    async def on_startup(dp):
        global db_pool
        db_pool = await create_db_pool()
        print("Бот инициализирован")
    async def on_shutdown(dp):
        await db_pool.close()
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)