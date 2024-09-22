from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class MedicalCardForm(StatesGroup):
    chronic_disease = State()
    allergy = State()
