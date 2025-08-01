from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.keyboards import main_menu_kb
from services.storage import save_request
from utils.notify import notify_admins
from datetime import datetime
from pathlib import Path

router = Router()

RESUME_DIR = Path("data/resumes")
RESUME_DIR.mkdir(parents=True, exist_ok=True)

class SpecialistForm(StatesGroup):
    name = State()
    contact = State()
    skills = State()
    resume = State()

@router.message(F.text == "Я хочу предложить себя")
async def specialist_start(message: types.Message, state: FSMContext):
    await state.set_state(SpecialistForm.name)
    await message.answer("Введите ваше имя:")

@router.message(SpecialistForm.name)
async def specialist_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SpecialistForm.contact)
    await message.answer("Укажите ваш контакт (телефон или email):")

@router.message(SpecialistForm.contact)
async def specialist_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    await state.set_state(SpecialistForm.skills)
    await message.answer("Опишите навыки и опыт (коротко):")

@router.message(SpecialistForm.skills)
async def specialist_skills(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await state.set_state(SpecialistForm.resume)
    await message.answer("Если хотите, прикрепите резюме (PDF или DOC).\n"
                         "Или напишите 'Пропустить', чтобы отправить без резюме.")

# --- если прикреплен файл ---
@router.message(SpecialistForm.resume, F.document)
async def specialist_resume_file(message: types.Message, state: FSMContext, bot: Bot):
    doc = message.document
    data = await state.get_data()

    # Скачиваем резюме
    file_path = RESUME_DIR / f"{doc.file_id}_{doc.file_name}"
    await bot.download(doc, destination=file_path)

    data["resume_file"] = str(file_path)
    await finalize_specialist_request(message, bot, state, data, doc)

# --- если пользователь пропускает ---
@router.message(SpecialistForm.resume)
async def specialist_resume_skip(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    data["resume_file"] = None
    await finalize_specialist_request(message, bot, state, data, None)

async def finalize_specialist_request(message: types.Message, bot: Bot, state: FSMContext, data: dict, doc: types.Document | None):
    data["timestamp"] = datetime.utcnow().isoformat()

    entry = save_request("specialist", data)

    # Отправляем уведомление админам
    await notify_admins(bot, entry)

    # Если есть файл — пересылаем его всем админам
    if doc:
        from services.admins import list_admins
        for admin_id in list_admins():
            try:
                await bot.send_document(admin_id, types.FSInputFile(data["resume_file"]))
            except Exception:
                pass

    await message.answer(
        "Спасибо! Ваши данные отправлены.\n"
        "Мы свяжемся с вами при появлении подходящих вакансий.",
        reply_markup=main_menu_kb(user_id=message.from_user.id)
    )
    await state.clear()
