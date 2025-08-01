from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from services.storage import DATA_FILE
from services.users import _load_users
from services.admins import add_admin, remove_admin
from config import ADMIN_PASSWORD
from services.storage import load_requests, _save_all
from services.admins import list_admins

router = Router()

# --- FSM состояния --- #
class AdminSearch(StatesGroup):
    waiting_query = State()

class AdminBroadcast(StatesGroup):
    waiting_text = State()

# --- Клавиатура админки --- #
def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🗂 Непринятые", callback_data="admin_unaccepted")],
        [InlineKeyboardButton(text="🗂 Клиенты", callback_data="admin_list_clients")],
        [InlineKeyboardButton(text="🗂 Специалисты", callback_data="admin_list_specialists")],
        [InlineKeyboardButton(text="📤 Экспорт", callback_data="admin_export")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🚪 Выйти", callback_data="admin_logout")],
    ])

# --- Вход в админку --- #
@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id in list_admins():
        await message.answer("Вы уже авторизованы", reply_markup=admin_menu_kb())
    else:
        await message.answer("Введите пароль:")

@router.message(Command("logout"))
async def admin_logout_cmd(message: types.Message):
    remove_admin(message.from_user.id)
    await message.answer("Вы вышли из админки.")

@router.message(lambda m: m.text == ADMIN_PASSWORD)
async def admin_check_password(message: types.Message):
    add_admin(message.from_user.id)
    await message.answer("Пароль верный. Добро пожаловать!", reply_markup=admin_menu_kb())

# --- Callback выхода --- #
@router.callback_query(F.data == "admin_logout")
async def admin_logout_cb(callback: types.CallbackQuery):
    remove_admin(callback.from_user.id)
    await callback.message.edit_text("Вы вышли из админки.")
    await callback.answer()

# --- Callback: Статистика --- #
@router.callback_query(F.data == "admin_stats")
async def admin_stats_cb(callback: types.CallbackQuery):
    data = load_requests()
    total = len(data["clients"]) + len(data["specialists"])
    unaccepted = sum(1 for arr in data.values() for x in arr if x["status"] == "new")
    text = (
        f"Всего заявок: {total}\n"
        f"Непринятых: {unaccepted}\n"
        f"Клиенты: {len(data['clients'])}\n"
        f"Специалисты: {len(data['specialists'])}"
    )
    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
    await callback.answer()

# --- Callback: непринятые заявки --- #
@router.callback_query(F.data == "admin_unaccepted")
async def admin_unaccepted_cb(callback: types.CallbackQuery):
    data = load_requests()
    new_entries = [x for arr in data.values() for x in arr if x["status"] == "new"]

    if not new_entries:
        await callback.message.edit_text("Нет непринятых заявок", reply_markup=admin_menu_kb())
    else:
        text = "Непринятые заявки:\n\n"
        for entry in new_entries[-10:]:
            text += f"• [{entry['type']}] {entry['name']} ({entry['contact']})\n"
            text += f"/accept_{entry['id']}\n\n"
        text += "\nЧтобы принять заявку, нажмите на соответствующую кнопку."
        await callback.message.edit_text(text, reply_markup=admin_menu_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("accept:"))
async def accept_request_cb(callback: types.CallbackQuery, bot: Bot):
    """
    Обработка нажатия кнопки "Принять" на заявке
    """
    entry_id = callback.data.split(":")[1]
    data = load_requests()

    found = None
    for arr in data.values():
        for entry in arr:
            if entry["id"] == entry_id:
                found = entry
                if entry["status"] == "new":
                    entry["status"] = "accepted"
                    entry["accepted_by"] = callback.from_user.username or str(callback.from_user.id)
                break

    if not found:
        await callback.answer("Заявка не найдена или уже обработана", show_alert=True)
        return

    _save_all(data)

    new_text = (
        f"Заявка ({found['type']}):\n\n"
        f"<b>Имя:</b> {found['name']}\n"
        f"<b>Контакт:</b> {found['contact']}\n"
        f"Статус: ✅ Принята ({found['accepted_by']})\n"
        f"<i>{found['timestamp']}</i>"
    )

    # всем админам отправляем обновление
    for admin_id in list_admins():
        try:
            await bot.send_message(admin_id, new_text)
        except Exception:
            pass

    await callback.answer("Заявка принята!")
    await callback.message.edit_text(new_text)
# --- Callback: клиенты --- #
@router.callback_query(F.data == "admin_list_clients")
async def admin_list_clients_cb(callback: types.CallbackQuery):
    data = load_requests()["clients"]
    if not data:
        await callback.message.edit_text("Нет заявок от клиентов", reply_markup=admin_menu_kb())
    else:
        text = "\n".join(
            [f"#{idx} - {entry.get('name')} | {entry.get('contact')} (статус: {entry['status']})"
             for idx, entry in enumerate(data[-10:], 1)]
        )
        await callback.message.edit_text(f"Последние 10 заявок от клиентов:\n\n{text}", reply_markup=admin_menu_kb())
    await callback.answer()

# --- Callback: специалисты --- #
@router.callback_query(F.data == "admin_list_specialists")
async def admin_list_specialists_cb(callback: types.CallbackQuery):
    data = load_requests()["specialists"]
    if not data:
        await callback.message.edit_text("Нет заявок от специалистов", reply_markup=admin_menu_kb())
    else:
        text = "\n".join(
            [f"#{idx} - {entry.get('name')} | {entry.get('contact')} (статус: {entry['status']})"
             for idx, entry in enumerate(data[-10:], 1)]
        )
        await callback.message.edit_text(f"Последние 10 заявок от специалистов:\n\n{text}", reply_markup=admin_menu_kb())
    await callback.answer()

# --- Callback: экспорт --- #
@router.callback_query(F.data == "admin_export")
async def admin_export_cb(callback: types.CallbackQuery):
    if not DATA_FILE.exists():
        await callback.message.answer("Файл отсутствует")
    else:
        await callback.message.answer_document(types.FSInputFile(DATA_FILE))
    await callback.answer()

# --- Callback: поиск --- #
@router.callback_query(F.data == "admin_search")
async def admin_search_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите строку для поиска (по имени или контакту):")
    await state.set_state(AdminSearch.waiting_query)
    await callback.answer()

@router.message(AdminSearch.waiting_query)
async def admin_do_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    data = load_requests()
    results = []
    for typ, arr in data.items():
        for entry in arr:
            if query in entry.get("name", "").lower() or query in entry.get("contact", "").lower():
                results.append((typ, entry))
    if not results:
        await message.answer("Ничего не найдено", reply_markup=admin_menu_kb())
    else:
        txt = "\n\n".join(
            [f"[{typ}] {x['name']} | {x['contact']} | {x.get('timestamp')} | статус: {x['status']}"
             for typ, x in results[:10]]
        )
        await message.answer(f"Найдено:\n\n{txt}", reply_markup=admin_menu_kb())
    await state.clear()

# --- Callback: рассылка --- #
class AdminBroadcast(StatesGroup):
    waiting_text = State()

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_cb(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст для рассылки:")
    await state.set_state(AdminBroadcast.waiting_text)
    await callback.answer()

@router.message(AdminBroadcast.waiting_text)
async def admin_do_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    text = message.text
    users = _load_users()
    sent = 0
    for uid in users.keys():
        try:
            await bot.send_message(int(uid), text)
            sent += 1
        except Exception:
            pass
    await message.answer(f"Рассылка завершена. Отправлено {sent} пользователям.", reply_markup=admin_menu_kb())
    await state.clear()
