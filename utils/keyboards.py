from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.texts import load_texts
from services.users import get_user_lang

def main_menu_kb(lang=None, user_id=None):
    if user_id is not None:
        lang = get_user_lang(user_id)
    if lang is None:
        lang = "ru"
    t = load_texts(lang)
    kb = [
        [KeyboardButton(text=t["menu_about"])],
        [KeyboardButton(text=t["menu_company"])],
        [KeyboardButton(text=t["menu_specialist"])],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
