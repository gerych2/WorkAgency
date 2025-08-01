import json
from pathlib import Path

ADMINS_FILE = Path("data/admins.json")

def _load_admins():
    if ADMINS_FILE.exists():
        try:
            return json.load(open(ADMINS_FILE, "r", encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []

def _save_admins(admins: list):
    ADMINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(admins, open(ADMINS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def add_admin(user_id: int):
    admins = _load_admins()
    if user_id not in admins:
        admins.append(user_id)
        _save_admins(admins)

def remove_admin(user_id: int):
    admins = _load_admins()
    if user_id in admins:
        admins.remove(user_id)
        _save_admins(admins)

def list_admins():
    return _load_admins()
