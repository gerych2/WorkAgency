from aiogram import Router, types, F
from aiogram.filters import Command
from utils.keyboards import main_menu_kb
from utils.texts import load_texts
from services.users import set_user_lang, get_user_lang

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Русский")],
                  [types.KeyboardButton(text="English")]],
        resize_keyboard=True
    )
    await message.answer("Выберите язык / Choose language:", reply_markup=kb)

@router.message(F.text.in_(["Русский", "English"]))
async def choose_language(message: types.Message):
    lang = "ru" if message.text == "Русский" else "en"
    set_user_lang(message.from_user.id, lang)
    t = load_texts(lang)
    await message.answer(t["start"], reply_markup=main_menu_kb(lang))

@router.message(lambda m: m.text in ["О компании", "About company"])
async def about_company(message: types.Message):
    lang = get_user_lang(message.from_user.id)
    t = load_texts(lang)
    await message.answer(t["about"])
