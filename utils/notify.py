from services.admins import list_admins
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def notify_admins(bot, entry):
    """
    Отправляет всем админам сообщение о новой заявке с кнопкой "Принять"
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{entry['id']}")]
        ]
    )

    text = (
        f"Новая заявка ({entry['type']}):\n\n"
        f"<b>Имя:</b> {entry['name']}\n"
        f"<b>Контакт:</b> {entry['contact']}\n"
        f"<i>{entry['timestamp']}</i>"
    )

    for admin_id in list_admins():
        try:
            await bot.send_message(admin_id, text, reply_markup=kb)
        except Exception:
            pass
