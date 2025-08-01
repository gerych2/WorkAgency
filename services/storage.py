import json
from datetime import datetime
from pathlib import Path
import uuid

DATA_FILE = Path("data/requests.json")


def _load_all():
    if DATA_FILE.exists():
        try:
            data = json.load(open(DATA_FILE, "r", encoding="utf-8"))
            if not isinstance(data, dict):
                return {"clients": [], "specialists": []}
            if "clients" not in data:
                data["clients"] = []
            if "specialists" not in data:
                data["specialists"] = []

            # добавляем новые поля для старых заявок
            for arr in data.values():
                for entry in arr:
                    if "status" not in entry:
                        entry["status"] = "new"
                    if "accepted_by" not in entry:
                        entry["accepted_by"] = None
            return data
        except json.JSONDecodeError:
            return {"clients": [], "specialists": []}
    return {"clients": [], "specialists": []}


def _save_all(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def save_request(req_type: str, data: dict):
    all_data = _load_all()
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "type": req_type,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "new",
        "accepted_by": None,
        **data
    }
    if req_type == "client":
        all_data["clients"].append(entry)
    else:
        all_data["specialists"].append(entry)

    _save_all(all_data)
    return entry


def load_requests():
    return _load_all()
