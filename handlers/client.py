from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.keyboards import main_menu_kb
from services.storage import save_request
from utils.notify import notify_admins

router = Router()

class ClientForm(StatesGroup):
    name = State()
    contact = State()
    requirements = State()
    budget = State()

@router.message(F.text == "Я ищу специалистов")
async def client_start(message: types.Message, state: FSMContext):
    await state.set_state(ClientForm.name)
    await message.answer("Введите ваше имя и должность:")

@router.message(ClientForm.name)
async def client_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ClientForm.contact)
    await message.answer("Укажите контакт (телефон или email):")

@router.message(ClientForm.contact)
async def client_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(ClientForm.requirements)
    await message.answer("Кого вы ищете? (стек, кол-во людей, сроки):")

@router.message(ClientForm.requirements)
async def client_requirements(message: types.Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await state.set_state(ClientForm.budget)
    await message.answer("Какой бюджет или другие комментарии:")

@router.message(ClientForm.budget)
async def client_finish(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(budget=message.text)
    data = await state.get_data()

    entry = save_request("client", data)
    await notify_admins(bot, entry)

    await message.answer(
        "Спасибо! Ваша заявка сохранена.\n"
        "Мы свяжемся с вами в ближайшее время.",
        reply_markup=main_menu_kb(user_id=message.from_user.id)
    )
    await state.clear()
