# -*- coding: utf-8 -*-
"""Собрать assets/categories.json из словарей тренажёра.

Источник: english_for_programmers_gui/data/*.txt - там слова уже
разложены по логическим блокам, у каждого файла строка "# topic:".
Мы только переносим эту разметку в питомца, ничего не выдумывая.

Запуск из папки проекта:

    python tools/build_categories.py

Результат: assets/categories.json
  categories - список блоков: id, русское название, группа меню;
  words - слово (en, нижний регистр) -> id блока.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT.parent / "english_for_programmers_gui" / "data"

# Группы для двухуровневого меню "Что учить".
GROUPS = {
    "topics": "Темы",
    "speech": "Части речи",
    "style": "Фразы и стиль",
}


def group_of(stem: str) -> str:
    number = int(stem.split("_")[0])
    if number <= 9:
        return "topics"
    if number <= 14:
        return "speech"
    return "style"


def main() -> None:
    categories = []
    words = {}
    for path in sorted(DATA.glob("*.txt")):
        title = path.stem
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("# topic:"):
                title = line.split(":", 1)[1].strip()
                continue
            if line.startswith("#"):
                continue
            en = line.split("|")[0].strip().lower()
            words.setdefault(en, path.stem)
        categories.append({
            "id": path.stem,
            "title": title,
            "group": group_of(path.stem),
        })

    out = {"categories": categories, "words": words}
    target = ROOT / "assets" / "categories.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"блоков: {len(categories)}, слов размечено: {len(words)}")
    print(f"записано: {target}")


if __name__ == "__main__":
    main()
