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
    parts = stem.split("_")
    try:
        number = int(parts[0])
    except (IndexError, ValueError):
        # Файлы без числового префикса (README, заметки) - просто
        # кидаем в последнюю группу вместо падения.
        return "style"
    if number <= 9:
        return "topics"
    if number <= 14:
        return "speech"
    return "style"


def main() -> None:
    if not DATA.is_dir() or not list(DATA.glob("*.txt")):
        print(f"нет файлов словаря в {DATA} — прерываю, чтобы не затeреть categories.json")
        return
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
    # Сохранить блоки азбуки (abc_). build_basics.py добавляет их
    # после нас, и повторный запуск build_categories.py не должен
    # затирать их — склеиваем.
    if target.exists():
        try:
            old = json.loads(target.read_text(encoding="utf-8"))
            abc_cats = [c for c in old["categories"] if c["id"].startswith("abc_")]
            abc_words = {k: v for k, v in old["words"].items() if v.startswith("abc_")}
            categories = abc_cats + categories
            words.update(abc_words)
        except (OSError, json.JSONDecodeError, KeyError):
            pass
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"блоков: {len(categories)}, слов размечено: {len(words)}")
    print(f"записано: {target}")


if __name__ == "__main__":
    main()
