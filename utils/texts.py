import json
from pathlib import Path

def load_texts(lang="ru"):
    file = Path(f"data/texts_{lang}.json")
    if not file.exists():
        file = Path("data/texts_ru.json")
    return json.load(open(file, "r", encoding="utf-8"))
