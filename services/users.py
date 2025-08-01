import json
from pathlib import Path

USERS_FILE = Path("data/users.json")

def _load_users():
    if USERS_FILE.exists():
        try:
            return json.load(open(USERS_FILE, "r", encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def _save_users(users: dict):
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(users, open(USERS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def get_user_lang(user_id: int) -> str:
    users = _load_users()
    return users.get(str(user_id), "ru")

def set_user_lang(user_id: int, lang: str):
    users = _load_users()
    users[str(user_id)] = lang
    _save_users(users)
