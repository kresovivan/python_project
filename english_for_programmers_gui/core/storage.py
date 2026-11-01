# =============================================================================
# ХРАНИЛИЩЕ - надёжная запись данных программы в файл JSON
# =============================================================================
#
# Что это в жизни: "сейф" для одного файла на диске. Прогресс (progress.json)
# и настройки (state.json) кладут в него свои данные и достают их обратно.
# Сами Progress и Settings не знают, как устроен файл: они говорят только
# "сохрани" и "загрузи". Одна обязанность - один класс.
#
# Две защиты от потери данных:
#
#   1. Запись "через черновик". Сначала пишем во временный файл
#      progress.json.tmp, и только когда он целиком записан, подменяем им
#      настоящий файл (os.replace). Подмена в Windows и Linux происходит
#      целиком или не происходит вовсе. Если выключат компьютер посреди
#      записи, пострадает только черновик, а старый файл останется целым.
#      Раньше файл сначала обрезался до нуля, потом записывался заново:
#      сбой в этот момент оставлял пустой или обрезанный файл.
#
#   2. Испорченный файл не стирается. Если файл не читается как JSON,
#      программа начинает с пустых данных, но сам файл переименовывается в
#      progress.broken-20261102-011500.json. Раньше первый же ответ молча
#      перезаписывал испорченный файл, и весь прогресс пропадал навсегда.
#      Копию можно открыть в блокноте и восстановить вручную.
#
# Кто пользуется: core/progress.py (Progress), core/settings.py (Settings).

import json
import os
from datetime import datetime
from pathlib import Path


class JsonStore:
    """Один файл JSON на диске: загрузить словарь, сохранить словарь.

    Объект JsonStore - это не сами данные, а "адрес" файла и правила работы
    с ним. Данные живут в том, кто их загрузил (Progress, Settings).
    """

    def __init__(self, path: Path):
        self.path = path
        # Куда отложена испорченная копия файла (или None, если всё в порядке).
        # Окно программы смотрит сюда, чтобы предупредить пользователя.
        self.backup_path: Path | None = None

    def load(self) -> dict:
        """Прочитать данные. Нет файла или он испорчен - пустой словарь {}."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}  # первый запуск: файла ещё нет, это нормально
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if not isinstance(data, dict):  # не JSON или JSON, но не {...}
            self._keep_broken_file()
            return {}
        return data

    def save(self, data: dict) -> None:
        """Записать данные так, чтобы сбой не испортил старый файл."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # ensure_ascii=False - русские буквы пишутся как есть, а не ц.
        # indent=1 - по строке на значение: файл удобно читать глазами.
        text = json.dumps(data, ensure_ascii=False, indent=1)
        draft = self.path.with_name(self.path.name + ".tmp")
        try:
            draft.write_text(text, encoding="utf-8")
            os.replace(draft, self.path)  # подмена целиком или никак
        finally:
            draft.unlink(missing_ok=True)  # после удачной подмены черновика уже нет

    def _keep_broken_file(self) -> None:
        """Отложить испорченный файл в сторону под новым именем."""
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.stem}.broken-{stamp}{self.path.suffix}")
        os.replace(self.path, backup)
        self.backup_path = backup
