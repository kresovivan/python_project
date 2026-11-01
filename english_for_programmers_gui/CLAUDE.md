# English for Programmers - графическая версия

Тренажёр английского для русскоязычных программистов: карточки, выбор перевода, написание слова,
чтение ошибок Python, словарь, прогресс, озвучка. Подробное описание для человека - `README.md`.

- Запуск: `python main.py` (из этой папки). Exe: `python build_exe.py` (PyInstaller, режим
  `--onedir`, результат `dist/EnglishForProgrammers/`, плюс ярлык на рабочем столе).
  `--onefile` не использовать: запуск ~5 с против ~1 с.
- Пути: `main.py` передаёт `App(resource_dir(), user_data_dir())`. В exe ресурсы (`data/`,
  `assets/`) - в `sys._MEIPASS`, а `user_data/` - рядом с exe. Новые файлы-ресурсы добавлять
  в `--add-data` в `build_exe.py`.
- Значок: `tools/make_icon.py` рисует `assets/icon.ico` через numpy (Pillow не установлен).
- Зависимости: `customtkinter` 6.0 (интерфейс), `edge-tts` 7.3 (нейросетевые голоса). Python 3.10+.
- Данные: `data/*.txt` (3621 слово, 18 тем). Состояние пользователя: `user_data/` - не трогать
  и не удалять, там прогресс, настройки и кэш звука.

## Архитектура

`core/` - логика без окон, `gui/` - интерфейс. **Правила не нарушать:**

1. Логика - в `core/` (`Lesson`, `ChoiceQuestion`, `AnswerChecker`, `Progress`, порядок поиска
   в `Vocabulary.search`, оценка `Session.rating`). Страницы только показывают и передают.
   Любое новое правило - в `core/` и сначала падающий тест в `tests/unit/`.
2. Страница получает `AppContext` (`gui/context.py`): vocabulary, progress, settings, errors,
   voice, navigator. **Не** передавать страницам окно `App` и не обращаться к нему из страниц.
3. `App` (`gui/app.py`) только собирает части. Меню - `Sidebar`, страницы - `PageHost`,
   озвучка - `VoiceController`, сообщения - `Toast`, справка F1 - `HelpOverlay`.
   Зависимости передаются снаружи: `App(..., speaker=)`, `Speaker(..., system=, neural=)`,
   `Progress(path, today=)`. Тесты подставляют заглушки, `unittest.mock.patch` для этого не нужен.
4. Новая страница: наследник `Page` в `gui/pages/` + строка в `PAGE_CLASSES` (`gui/app.py`).
   Конструктор страницы: `__init__(self, master, context, number=0)` и `super().__init__(master, context, number)`.
   Номер в меню - атрибут объекта (`self.number`), его передаёт `PageHost`; в класс не записывать.
   Новый режим занятий: константа в `core/session.py` (+ `STUDY_MODES`), наследник `StudyPage`
   с `key` = эта константа (`build_body`, `render`, при нужде `handle_key`). Значения режимов
   `"cards"`, `"choice"`, `"typing"` не менять: они записаны в `state.json` пользователя.
   У страницы задать `key`, `title`, `tagline`, `description`; шапка - `self.build_header()`.
5. Счёт занятия меняет только `Session` (`record_answer`, `skip_word`). `Lesson.answer(is_right)`
   отвечает на текущее слово. Вопросы (`current_word`, `active`) ничего не меняют.
6. Файлы `user_data/*.json` пишет только `JsonStore` (`core/storage.py`): запись через `.tmp`
   и `os.replace`, испорченный файл откладывается как `*.broken-ДАТА.json`, окно предупреждает.
   `build_exe.py` уносит `dist/.../user_data` в `build/user_data_backup` на время сборки.
7. Клавиши - через `KeyPress` (`gui/hotkeys.py`). Буквы проверять `key.is_letter("F")`
   (по физической клавише, keycode) - иначе не работает в русской раскладке.
   Новое сочетание - описать в `HELP` в том же файле (это справка F1).
8. Цвета и шрифты - **только** из `gui/theme.py`, пары (светлая, тёмная). Для `tk.Canvas`
   и `tk.Text` - `theme.pick(...)`, для свечения - `theme.mix(...)`.

## Производительность (важно, было медленно)

- Прозрачная `CTkFrame` = холст на всю площадь, перерисовывается при растягивании.
  Для рамок раскладки - **`Box`** (`gui/widgets.py`, обычная tk.Frame с парой цветов).
- Длинные списки - не сотни CTk-виджетов, а `RichText` (одно `tk.Text` с тегами)
  или `tk.Canvas` (как `TopicBars`, `LearningDiagram`).
- Скрытые страницы убираются `grid_remove()` - не менять на `tkraise()`.
- Ориентиры: смена страницы до ~30 мс, шаг растягивания окна ~100-150 мс, кадр схемы ~3 мс.

## Подводные камни

- Масштаб 200%: CTk-виджеты масштабируются сами, `tk.Canvas`/`tk.Text` - нет. Размеры умножать
  на `ctk.ScalingTracker.get_widget_scaling(widget)`, шрифты задавать в пикселях (`-size`).
- В `CTkEntry` `Ctrl+H` по умолчанию стирает символ - перехвачено в `TypingPage`.
- `text_color_disabled` у кнопок по умолчанию серый - задавать явно (выбор перевода).
- Озвучка (`core/speech.py`): edge-tts иногда отвечает пустотой - 3 попытки, запись через
  `.part`-файл; звук проигрывается через MCI (`ctypes`, winmm) **только из главного потока**,
  скачивание - в фоновом потоке, результаты через очередь и `Speaker.poll()`.
  Голос Windows (Zira) - запасной. ElevenLabs недоступен из региона пользователя.
- Окно под монитор: `gui/screen.py`. До `super().__init__()` в `App`: `Screens.make_dpi_aware()`,
  выбор монитора, `plan_window()`, затем `ctk.set_widget_scaling`/`set_window_scaling` (масштаб
  интерфейса 0.7-1.2) - ДО создания виджетов. В `geometry()` CTk ширина/высота логические,
  x/y - пиксели монитора. Сохраняется `settings["window"] = {"geometry", "maximized"}`.
  У пользователя 2 монитора: 4K (основной) и 3072x1920 справа выше (y = -484), оба 200%.
- Шрифтов сайта-образца (Inter, JetBrains Mono) в системе нет: используются Segoe UI Variable
  и Cascadia Mono. Полужирные начертания - отдельные семейства (`"Segoe UI Variable Display Semib"`).
- При закрытии окна `App.on_close` отменяет все `after` командой Tcl `self.tk.call("after", "cancel", id)`.
  **Не** через `self.after_cancel(id)`: он удаляет служебные команды чужих виджетов, потом их
  `destroy()` падает с "can't delete Tcl command", окно не закрывается и программа висит.
  Проверять закрытие запуском `main.py` отдельным процессом и сообщением WM_CLOSE окну.

## Стиль оформления

По сайту irreplaceable-ai.ru: фон `#0a0a0b`, голубой акцент `#a6c2f5`, мятный/красный/оранжевый
для статусов, метки разделов моноширинным шрифтом `03 / ВЫБОР ПЕРЕВОДА`, заголовок из двух частей
со второй частью курсивом в цвет акцента, кнопки-"таблетки". Таблица цветов - в `README.md`.

## Как проверять изменения

Тесты в стиле TDD: один тест - одно правило, шаги "подготовка - действие - проверка",
русские комментарии. Новое правило или исправление ошибки - сначала падающий тест.
Быстрые тесты логики: `python -m unittest discover -s tests/unit -t .` (доли секунды),
все: `python -m unittest discover -s tests -t .` (около 1,5 минуты, норма `OK (skipped=12)`).
Папки `unit/`, `gui/` (окно с заглушкой голоса `FakeSpeaker`, `gui/base.py`), `system/`,
`manual/` и правила написания тестов - в `tests/README.md`.

1. `python -c "import gui.app"` и `py_compile` всех файлов.
2. Запустить окно из скрипта во временной папке (скопировать `data/`, не трогать `user_data/`),
   вызвать методы страниц, подать нажатия через `app._on_key(SimpleNamespace(keysym=..., keycode=..., state=...))`.
   В русской раскладке буква приходит с другим keysym, но тем же keycode (P = 80, F = 70).
3. Снимок окна через PowerShell `CopyFromScreen` и посмотреть его.
4. Логику (`Lesson`, `AnswerChecker`, `Progress`) можно проверять вообще без окна.

Консольная версия того же тренажёра - `../english_for_programmers/` (свой README, старый стиль символов).
