import asyncio
import os
import asyncpg
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from dotenv import load_dotenv
from datetime import datetime, timedelta
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
    add_pet_name = State()
    add_pet_type = State()
    add_pet_date = State()
    add_pet_sex = State()
    add_pet_breed = State()
    add_pet_color = State()
    add_pet_weight = State()
    add_pet_sterilized = State()
    add_pet_town = State()
    add_pet = State()

    view_pets = State()

class ReminderStates(StatesGroup):
    chose_pet = State()
    get_pets = State()
    waiting_for_text = State()
    waiting_for_time = State()
    waiting_for_frequency = State()
    waiting_for_repeat_end = State()

def canceled():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(text="Отменить", callback_data='cancel'),
    ]
    keyboard.add(*buttons)
    return keyboard

@dp.message_handler(state=ReminderStates.get_pets)
async def get_pets(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    try:
        print("Я тут")
        conn = await asyncpg.connect(DATABASE_URL)
        user_id = await conn.fetch("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
        name = await conn.fetch("SELECT name FROM pets WHERE user_id = $1", user_id)
        pet = await conn.fetch("SELECT pet_id FROM pets WHERE user_id = $1", user_id)
        print("Строка", name, pet)
        await conn.close()
        await state.finish()
        return await message.answer(reply_markup=chose_pets(name, pet))
    except Exception as e:
        print(f"Ошибка при получении данных из базы: {e}")
        return

def chose_pets(name, pet):
    keyboard = InlineKeyboardMarkup(row_width=1)  # Создаем клавиатуру

    for button in name:
        button_name = name  # Название кнопки
        callback_data = pet  # Callback для кнопки
        keyboard.add(InlineKeyboardButton(text=button_name, callback_data=callback_data))

    return keyboard
    

@dp.callback_query_handler(lambda c: c.data == 'cancel', state="*")
async def process_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()  # Завершаем текущее состояние
    await callback_query.message.answer("Действие отменено. Выберите следующее:", reply_markup=get_main_menu())

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

        # Отправляем сообщение с кнопками
        await message.answer("Выберите действие:", reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")
        return

# Создаем инлайн-клавиатуру для выбора опций
def get_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton(text="Добавить питомца", callback_data="add_pet"),
        InlineKeyboardButton(text="Показать питомцев", callback_data="view_pets"),
        InlineKeyboardButton(text="Добавить болезнь", callback_data="add_disease"),
        InlineKeyboardButton(text="Добавить хроническую болезнь", callback_data="add_chronic_disease"),
        InlineKeyboardButton(text="Добавить аллергию", callback_data="add_allergy"),
        InlineKeyboardButton(text="Добавить напоминание", callback_data="add_shedule"),
    ]
    keyboard.add(*buttons)
    return keyboard

# Обрабатываем нажатие на кнопки
@dp.callback_query_handler(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id

        async with db_pool.acquire() as conn:
            user_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id = $1)", user_id)
            if not user_exists:
                await callback_query.message.answer("Вы не зарегистрировались, введите /start для регистрации")
                return

        # Определение состояния по команде
        if data == "add_pet":
            await PetsForm.add_pet_name.set()
            await callback_query.message.answer("Введите имя питомца:", reply_markup=canceled())
 
        elif data == "view_pets":
            await PetsForm.view_pets.set()  # Устанавливаем состояние для просмотра питомцев
            await process_view_pets(callback_query, callback_query.message, state)  # Передаем состояние
       
        elif data == "add_disease":
            await MedicalCardForm.disease.set()
            await callback_query.message.answer("Введите данные о болезни в формате:\n"
                                                "Имя питомца, Болезнь, Рекомендация")
        
        elif data == "add_chronic_disease":
            await MedicalCardForm.chronic_disease.set()
            await callback_query.message.answer("Введите данные о болезни в формате:\n"
                                                "Имя питомца, Хроническая болезнь")
        
        elif data == "add_allergy":
            await MedicalCardForm.allergy.set()
            await callback_query.message.answer("Введите данные о болезни в формате:\n"
                                                "Имя питомца, Аллергия")
            
        elif data == "add_shedule":
            await ReminderStates.get_pets.set()
            await get_pets(callback_query.message, state)

    except Exception as e:
        logger.error(f"Ошибка при выборе команды: {e}")
        await callback_query.message.answer("Произошла ошибка при выборе команды. Попробуйте позже.")


# Добавление питомца
@dp.message_handler(state=PetsForm.add_pet_name)
async def process_add_pet_name(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['name'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите тип питомца:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_type)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['type'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите дату рождения в формате ГГГГ-ММ-ДД:", reply_markup=asyncio.run(canceled()))

@dp.message_handler(state=PetsForm.add_pet_date)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        birth_date_str = message.text.strip()

        try:
            ani['birth_date'] = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        except ValueError as ve:
            logger.error(f"Ошибка преобразования даты: {ve}")
            await message.answer("Ошибка: неверный формат даты. Пожалуйста, используйте формат ГГГГ-ММ-ДД. Повторите ввод даты:", reply_markup=canceled())
            await PetsForm.add_pet_date()

    await PetsForm.next()
    await message.answer("Введите мол М или Ж:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_sex)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['sex'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите породу:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_breed)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['breed'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите цвет:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_color)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['color'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите вес:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_weight)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['weight'] = int(message.text.strip())
    await PetsForm.next()
    await message.answer("Введите стерилизацию Да или Нет:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_sterilized)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['sterilized'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите город:", reply_markup=canceled())

@dp.message_handler(state=PetsForm.add_pet_town)
async def process_add_pet_type(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['town'] = message.text.strip()
    await PetsForm.next()
    await message.answer("Введите условия содержания:", reply_markup=canceled())
    

@dp.message_handler(state=PetsForm.add_pet)
async def process_add_pet(message: types.Message, state: FSMContext):
    async with state.proxy() as ani:
        ani['keeping'] = message.text.strip()
        try:
            user_id = message.from_user.id
            async with db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO pets (user_id, name, type, date_birth, sex, breed, color, weight, sterilized, town, keeping)
                    VALUES ((SELECT user_id FROM users WHERE telegram_id = $1), $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    user_id, ani['name'], ani['type'], ani['birth_date'], ani['sex'], ani['breed'], ani['color'], ani['weight'], ani['sterilized'], ani['town'], ani['keeping']
                )
                await message.answer(f"Питомец {ani['name']} успешно добавлен!", await state.finish(), reply_markup=get_main_menu())
        except Exception as e:
            logger.error(f"Ошибка при добавлении питомца: {e}")
            await message.answer("Произошла ошибка при добавлении питомца. Попробуйте позже.", await state.finish(), reply_markup=get_main_menu())
        

# Просмотр всех питомцев пользователя
@dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=PetsForm.view_pets)
async def process_view_pets(callback_query: types.CallbackQuery, message: types.Message, state: FSMContext):
    try:
        telegram_id = callback_query.from_user.id

        async with db_pool.acquire() as conn:
            pets = await conn.fetch(
                """
                SELECT p.name, p.type, p.date_birth, p.breed, p.color, p.weight, p.pet_id
                FROM pets p
                JOIN users u ON p.user_id = u.user_id
                WHERE u.telegram_id = $1
                """, telegram_id
            )

            # Логируем результат запроса
            logger.info(f"Найдено {len(pets)} питомцев для пользователя с ID {telegram_id}")
            logger.info(f"Питомцы: {pets}")

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
                        f"<b>Имя:</b> {pet['name']}\n"
                        f"<b>Тип:</b> {pet['type']}\n"
                        f"<b>Дата рождения:</b> {pet['date_birth']}\n"
                        f"<b>Порода:</b> {pet['breed']}\n"
                        f"<b>Цвет:</b> {pet['color']}\n"
                        f"<b>Вес:</b> {pet['weight']} кг\n"
                        f"<b>Аллергия:</b> {allergy}\n"
                        f"<b>Хронические болезни:</b> {chronic_diseases}\n"
                        f"<b>Текущая болезнь:</b> {current_disease}\n"
                        f"<b>Рекомендации:</b> {current_recommendation}\n\n"
                    )
                await message.answer(response, parse_mode=ParseMode.HTML)
            await state.finish()
            await message.answer("Что вы хотите сделать дальше?", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при просмотре питомцев: {e}")
        await state.finish()
        await message.answer("Произошла ошибка при просмотре питомцев. Попробуйте позже.", reply_markup=get_main_menu())

# Добавление болезни в медицинскую карту
@dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=MedicalCardForm.disease)
async def process_add_disease(message: types.Message, state: FSMContext):
    try:
        data_disease = message.text.split(',')
        if len(data_disease) != 3:
            await message.answer("Ошибка: необходимо ввести 3 поля (Имя питомца, Болезнь, Рекомендация) через запятую.")
            await state.finish()
        name, diseases, recommendations = [x.strip() for x in data_disease]

        telegram_id = message.from_user.id

        diseases_list = [diseases]
        recommendations_list = [recommendations]

        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
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
                await message.answer(f"Болезнь '{diseases}' и рекомендация '{recommendations}' добавлены для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET diseases = array_append(diseases, $1),
                    recommendations = array_append(recommendations, $2)
                WHERE pet_id = $3
                """, diseases, recommendations, pet_id
                )
                await message.answer(f"Болезнь '{diseases}' и рекомендация '{recommendations}' добавлены для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при добавлении болезни: {e}")
        await message.answer("Произошла ошибка при добавлении болезни. Попробуйте позже.", await state.finish(), reply_markup=get_main_menu())

# Добавление хронической болезни в медицинскую карту
@dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=MedicalCardForm.chronic_disease)
async def process_add_chronic_diseases(message: types.Message, state: FSMContext):
    try:
        data_chronic = message.text.split(',')
        if len(data_chronic) != 2:
            await message.answer("Ошибка: необходимо ввести 2 поля (Имя питомца, Хроническая болезнь) через запятую.")
            await state.finish()
        name, chronic_diseases = [x.strip() for x in data_chronic]
        telegram_id = message.from_user.id
        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            if pet_id == None:
                await message.answer(f"Такого питомца не существует", await state.finish(), reply_markup=get_main_menu())
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, chronic_diseases)
                    VALUES ($1, $2)
                    """, pet_id, chronic_diseases
                )
                await message.answer(f"Хроническая болезнь '{chronic_diseases}' добавлена для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET chronic_diseases = $1
                WHERE pet_id = $2
                """, chronic_diseases, pet_id
                )
                await message.answer(f"Хроническая болезнь '{chronic_diseases}' добавлена для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при добавлении хронической болезни: {e}")
        await message.answer("Произошла ошибка при добавлении хронической болезни. Попробуйте позже.", await state.finish(), reply_markup=get_main_menu())

# Добавление аллергии в медицинскую карту
@dp.message_handler(lambda message: message.text and not message.text.startswith('/'), state=MedicalCardForm.allergy)
async def process_add_allergy(message: types.Message, state: FSMContext):
    try:
        data_allergy = message.text.split(',')
        if len(data_allergy) != 2:
            await message.answer("Ошибка: необходимо ввести 2 поля (Имя питомца, Аллергия) через запятую.")
            await state.finish()
        name, allergy = [x.strip() for x in data_allergy]
        telegram_id = message.from_user.id
        async with db_pool.acquire() as conn:
            user_id = await conn.fetchval("SELECT user_id FROM users WHERE telegram_id = $1", telegram_id)
            pet_id = await conn.fetchval("SELECT pet_id FROM pets WHERE user_id = $1 AND name = $2", user_id, name)
            if pet_id == None:
                await message.answer(f"Такого питомца не существует")
                await state.finish()
            pet_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM medical_card WHERE pet_id = $1)", pet_id)
            if not pet_exists:
                await conn.execute(
                    """
                    INSERT INTO medical_card (pet_id, allergy)
                    VALUES ($1, $2)
                    """, pet_id, allergy
                )
                await message.answer(f"Аллергия '{allergy}' добавлена для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
            else:
                await conn.execute(
                """
                UPDATE medical_card
                SET allergy = $1
                WHERE pet_id = $2
                """, allergy, pet_id
                )
                await message.answer(f"Аллергия '{allergy}' добавлена для питомца с именем {name}.", await state.finish(), reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при добавлении аллергии: {e}")
        await message.answer("Произошла ошибка при добавлении аллергии. Попробуйте позже.", await state.finish(), reply_markup=get_main_menu())

# Обрабатываем имя питомца
@dp.callback_query_handler(lambda c: c.data, state="*")
async def process_chose_pet(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(pet = callback_query.data)
    await callback_query.answer("Теперь введите название напоминания:")
    await ReminderStates.waiting_for_text.set()

# Обрабатываем текст напоминания
@dp.message_handler(state=ReminderStates.waiting_for_text, content_types=types.ContentType.TEXT)
async def process_reminder_text(message: types.Message, state: FSMContext):
    await state.update_data(reminder_text=message.text)
    await message.answer("Отлично! Теперь укажите время для напоминания в формате (ГГГГ-ММ-ДД ЧЧ:ММ):")
    await ReminderStates.waiting_for_time.set()

# Обрабатываем время напоминания
@dp.message_handler(state=ReminderStates.waiting_for_time, content_types=types.ContentType.TEXT)
async def process_reminder_time(message: types.Message, state: FSMContext):
    try:
        reminder_time = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        current_time = datetime.now()

        if reminder_time <= current_time:
            await message.answer("Время напоминания должно быть в будущем. Попробуйте еще раз.")
            await ReminderStates.waiting_for_time()

        await state.update_data(reminder_time=reminder_time)
        # Переходим к выбору частоты повторения
        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Каждый день", callback_data="daily"),
            InlineKeyboardButton("Каждую неделю", callback_data="weekly"),
            InlineKeyboardButton("Каждый месяц", callback_data="monthly"),
            InlineKeyboardButton("Каждый год", callback_data="yearly"),
            InlineKeyboardButton("Без повторений", callback_data="none")
        )
        await message.answer("Выберите частоту повторения:", reply_markup=keyboard)
        await ReminderStates.waiting_for_frequency.set()

    except ValueError:
        await message.answer("Неправильный формат даты. Пожалуйста, используйте формат: ГГГГ-ММ-ДД ЧЧ:ММ")
        await ReminderStates.waiting_for_time()

# Обрабатываем частоту повторения
@dp.callback_query_handler(state=ReminderStates.waiting_for_frequency)
async def process_frequency(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(frequency=call.data)
    # Спрашиваем про окончание повторения
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("После определённой даты", callback_data="until_date"),
        InlineKeyboardButton("После определённого количества повторений", callback_data="repeat_count"),
        InlineKeyboardButton("Без окончания", callback_data="no_end")
    )
    await call.message.answer("Как завершить повторение?", reply_markup=keyboard)
    await ReminderStates.waiting_for_repeat_end.set()

# Обрабатываем вариант окончания повторений
@dp.callback_query_handler(state=ReminderStates.waiting_for_repeat_end)
async def process_repeat_end(call: types.CallbackQuery, state: FSMContext):
    if call.data == "until_date":
        await call.message.answer("Укажите дату окончания в формате (ГГГГ-ММ-ДД):")
        await ReminderStates.waiting_for_repeat_end.set()
        await state.update_data(repeat_end_type='date')

    elif call.data == "repeat_count":
        await call.message.answer("Укажите количество повторений:")
        await ReminderStates.waiting_for_repeat_end.set()
        await state.update_data(repeat_end_type='count')

    else:
        await state.update_data(repeat_end_type='none')
        await finalize_reminder(call.message, state)

# Обрабатываем дату окончания или количество повторений
@dp.message_handler(state=ReminderStates.waiting_for_repeat_end, content_types=types.ContentType.TEXT)
async def process_repeat_end_value(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    repeat_end_type = user_data.get('repeat_end_type')

    if repeat_end_type == 'date':
        try:
            repeat_until_date = datetime.strptime(message.text, '%Y-%m-%d')
            await state.update_data(repeat_until_date=repeat_until_date)
        except ValueError:
            await message.answer("Неправильный формат даты. Попробуйте еще раз.")
            return
    elif repeat_end_type == 'count':
        try:
            repeat_count = int(message.text)
            await state.update_data(repeat_count=repeat_count)
        except ValueError:
            await message.answer("Введите корректное число.")
            return
    
    await finalize_reminder(message, state)

# Финализируем создание напоминания
async def finalize_reminder(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    reminder_text = user_data['reminder_text']
    reminder_time = user_data['reminder_time']
    frequency = user_data.get('frequency', 'none')
    repeat_until_date = user_data.get('repeat_until_date', None)
    repeat_count = user_data.get('repeat_count', 0)

    # Сохраняем в БД
    await save_reminder(
        message.from_user.id,
        reminder_text,
        reminder_time,
        frequency,
        repeat_until_date,
        repeat_count
    )
    await message.answer(f"Напоминание установлено с частотой {frequency}.")
    await state.finish()

async def save_reminder(user_id: int, text: str, reminder_time: datetime, frequency: str, repeat_until_date: datetime, repeat_count: int):
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    await conn.execute(
        "INSERT INTO reminders (user_id, text, reminder_time, frequency, repeat_until_date, repeat_count) "
        "VALUES ($1, $2, $3, $4, $5, $6)",
        user_id, text, reminder_time, frequency, repeat_until_date, repeat_count
    )
    await conn.close()

async def check_reminders():
    while True:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        current_time = datetime.now()

        # Извлекаем все напоминания, время которых пришло
        rows = await conn.fetch(
            "SELECT id, user_id, text, reminder_time, frequency, times_repeated, repeat_until_date, repeat_count FROM reminders WHERE reminder_time <= $1",
            current_time
        )

        for row in rows:
            await bot.send_message(row['user_id'], f"Напоминание: {row['text']}")

            # Обновляем данные для следующего повторения, если есть частота повторения
            if row['frequency'] != 'none':
                next_reminder_time = calculate_next_reminder_time(row['reminder_time'], row['frequency'])

                # Проверяем условия окончания
                if (row['repeat_until_date'] and next_reminder_time > row['repeat_until_date']) or \
                   (row['repeat_count'] and row['times_repeated'] + 1 >= row['repeat_count']):
                    await conn.execute("DELETE FROM reminders WHERE id = $1", row['id'])
                else:
                    await conn.execute(
                        "UPDATE reminders SET reminder_time = $1, times_repeated = times_repeated + 1 WHERE id = $2",
                        next_reminder_time, row['id']
                    )
            else:
                await conn.execute("DELETE FROM reminders WHERE id = $1", row['id'])

        await conn.close()
        await asyncio.sleep(60)

def calculate_next_reminder_time(reminder_time, frequency):
    if frequency == 'daily':
        return reminder_time + timedelta(days=1)
    elif frequency == 'weekly':
        return reminder_time + timedelta(weeks=1)
    elif frequency == 'monthly':
        return reminder_time + timedelta(days=30)  # Упрощённый подсчет месяца
    elif frequency == 'yearly':
        return reminder_time + timedelta(days=365)


# Запуск бота
if __name__ == '__main__':
    async def on_startup(dp):
        global db_pool
        db_pool = await create_db_pool()
        print("Бот инициализирован")

    async def on_shutdown(dp):
        await db_pool.close()

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
