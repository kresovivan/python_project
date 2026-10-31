"""
GUI-парсер ConfigDumpInfo.xml (метаданные 1С).

Архитектура (ООП):

  Константы и настройки
    COLORS, FONTS, BASE_COLUMNS, ONLY_LABELS
    AppPaths      - вычисление путей (portable vs %APPDATA%)
    SettingsStore - чтение/запись settings.json
    MarkersStore  - чтение/запись config_markers.json

  Парсинг XML
    XmlParser     - обнаружение ns, подсчёт, потоковый парсинг

  Поиск
    QueryCompiler - компиляция шаблона ^/$,?/* в regex
    QueryMatcher  - проверка строки на соответствие regex

  Виджеты-помощники
    CopyableLabel  - tk.Label с копированием по клику/правой кнопке
    CardFrame      - рамка-«карточка» с рамкой и фоном панели
    ToolTipMixin   - миксин привязки колеса мыши к Canvas

  Диалоги
    HelpWindow      - окно инструкции
    ExportDialog    - выбор что экспортировать
    SettingsDialog  - редактор путей
    MarkersDialog   - редактор префиксов
    MergeCsvDialog  - объединение CSV-файлов

  Главное окно
    MainWindow     - собирает всё вместе

Только стандартная библиотека Python 3.8+.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# =========================================================================
#  Константы
# =========================================================================

# --- Палитра ---
COLORS: Dict[str, str] = {
    'bg':            '#f0f2f5',
    'panel':         '#ffffff',
    'panel_alt':     '#f7f8fa',
    'border':        '#d9dde3',
    'text':          '#1c1e21',
    'text_muted':    '#6b7280',
    'accent':        '#2e86de',
    'accent_hover':  '#54a0ff',
    'accent_dark':   '#1c6bc2',
    'warn_bg':       '#fff8e1',
    'warn_fg':       '#7a5b00',
    'highlight':     '#fff3cd',
    'pattern_fg':    '#0a8754',
    'scroll_bg':     '#5dade2',
    'scroll_hover':  '#3498db',
    'scroll_press':  '#2874a6',
    'scroll_trough': '#eaf4fb',
    'scroll_border': '#aed6f1',
    'scroll_arrow':  '#1b4f72',
}

# --- Шрифты ---
FONTS: Dict[str, tuple] = {
    'h2':       ('Times New Roman', 10, 'bold'),
    'body':     ('Times New Roman', 10),
    'body_sm':  ('Times New Roman', 9),
    'button':   ('Times New Roman', 10),
    'mono':     ('Times New Roman', 11, 'bold'),

    'title':    ('Times New Roman', 16, 'bold'),
    'section':  ('Times New Roman', 13, 'bold'),
    'step_num': ('Times New Roman', 10, 'bold'),
    'kv_key':   ('Times New Roman', 10, 'bold'),
    'dialog':   ('Times New Roman', 12, 'bold'),
    'hint':     ('Times New Roman', 10, 'bold'),
}

# --- Базовые колонки таблицы ---
BASE_COLUMNS: List[str] = [
    'ТипОбъекта',
    'ИмяОбъекта',
    'ВидЭлемента',
    'ИмяЭлемента',
    'ВидВложенногоЭлемента',
    'ИмяВложенногоЭлемента',
    'ПутьЭлемента',
    'ПризнакОбъекта',
]

# --- Константы приложения ---
APP_NAME = 'ConfigDumpParser'
SETTINGS_FILENAME = 'settings.json'
MARKERS_FILENAME = 'config_markers.json'
DEFAULT_MERGED_NAME = 'merged.csv'

DEFAULT_MARKERS = ['ПЛ_']
CUSTOM_TAG = 'Кастомный'
STD_TAG = 'Стандартный'
NONE_TAG = '-'

# Соответствие «человеческого» названия в комбобоксе и внутреннего кода
ONLY_LABELS: Dict[str, str] = {
    'Все': 'all',
    'Только кастомные': 'custom',
    'Только стандартные': 'std',
}


# =========================================================================
#  Словари переводов имён 1С
# =========================================================================

# Имя типа объекта в XML -> русское название
TYPE_TRANSLATIONS: Dict[str, str] = {
    'Catalog': 'Справочник',
    'Document': 'Документ',
    'Enum': 'Перечисление',
    'InformationRegister': 'РегистрСведений',
    'AccumulationRegister': 'РегистрНакопления',
    'AccountingRegister': 'РегистрБухгалтерии',
    'CalculationRegister': 'РегистрРасчёта',
    'BusinessProcess': 'БизнесПроцесс',
    'Task': 'Задача',
    'DataProcessor': 'Обработка',
    'Report': 'Отчёт',
    'ChartOfAccounts': 'ПланСчетов',
    'ChartOfCharacteristicTypes': 'ПланВидовХарактеристик',
    'ChartOfCalculationTypes': 'ПланВидовРасчёта',
    'ExchangePlan': 'ПланОбмена',
    'Constant': 'Константа',
    'FilterCriterion': 'КритерийОтбора',
    'Sequence': 'Последовательность',
    'DocumentJournal': 'ЖурналДокументов',

    'CommonModule': 'ОбщийМодуль',
    'CommonForm': 'ОбщаяФорма',
    'CommonCommand': 'ОбщаяКоманда',
    'CommonTemplate': 'ОбщийМакет',
    'CommonPicture': 'ОбщаяКартинка',
    'CommonAttribute': 'ОбщийРеквизит',
    'SessionParameter': 'ПараметрСеанса',
    'SettingsStorage': 'ХранилищеНастроек',
    'StyleItem': 'ЭлементСтиля',
    'Interface': 'Интерфейс',
    'DefinedType': 'ОпределяемыйТип',
    'Role': 'Роль',
    'Subsystem': 'Подсистема',

    'ScheduledJob': 'РегламентноеЗадание',
    'FunctionalOption': 'ФункциональнаяОпция',
    'FunctionalOptionsParameter': 'ПараметрФункциональнойОпции',
    'EventSubscription': 'ПодпискаНаСобытие',

    'HTTPService': 'HTTPСервис',
    'WebService': 'WebСервис',
    'IntegrationService': 'СервисИнтеграции',
    'XDTOPackage': 'ПакетXDTO',
    'ExternalDataSource': 'ВнешнийИсточникДанных',
    'Bot': 'Бот',

    'Table': 'Таблица',
    'Cube': 'Куб',
    'DimensionTable': 'ТаблицаИзмерений',
    'Measurement': 'Измерение',
}

# Имя вида элемента/вложенного элемента -> русское название
KIND_TRANSLATIONS: Dict[str, str] = {
    'Attribute': 'Реквизит',
    'TabularSection': 'ТабличнаяЧасть',
    'Form': 'Форма',
    'Command': 'Команда',
    'Template': 'Макет',
    'Help': 'Справка',
    'Column': 'Колонка',

    'Picture': 'Картинка',
    'Subsystem': 'Подсистема',
    'CommandInterface': 'КомандныйИнтерфейс',
    'Interface': 'Интерфейс',

    'Rights': 'Права',
    'Schedule': 'Расписание',
    'Package': 'Пакет',
    'Predefined': 'Предопределённое',
    'Property': 'Свойство',
    'URLTemplate': 'ШаблонURL',
    'Operation': 'Операция',

    'Dimension': 'Измерение',
    'Resource': 'Ресурс',
    'AccountingFlag': 'ПризнакУчёта',
    'ExtDimensionAccountingFlag': 'ПризнакУчётаСубконто',
    'AddressingAttribute': 'РеквизитАдресации',
    'EnumValue': 'ЗначениеПеречисления',

    'Module': 'Модуль',
    'ManagerModule': 'МодульМенеджера',
    'ObjectModule': 'МодульОбъекта',
    'RecordSetModule': 'МодульНабораЗаписей',
    'ValueManagerModule': 'МодульМенеджераЗначения',
    'ExternalConnectionModule': 'МодульВнешнегоСоединения',
    'ManagedFormModule': 'МодульУправляемойФормы',
    'OrdinaryFormModule': 'МодульОбычнойФормы',
    'CommandModule': 'МодульКоманды',
    'HTTPServiceModule': 'МодульHTTPСервиса',
    'WebServiceModule': 'МодульWebСервиса',
    'IntegrationServiceModule': 'МодульСервисаИнтеграции',
    'ExternalDataSourceModule': 'МодульВнешнегоИсточникаДанных',
    'ManagedApplicationModule': 'МодульУправляемогоПриложения',
    'OrdinaryApplicationModule': 'МодульОбычногоПриложения',
    'SessionModule': 'МодульСеанса',
    'ExternalConnection': 'ВнешнееСоединение',
    'FilterCriterionModule': 'МодульКритерияОтбора',
    'SequenceModule': 'МодульПоследовательности',
    'DocumentJournalModule': 'МодульЖурналаДокументов',
    'ConstantModule': 'МодульКонстанты',
    'CommonModuleModule': 'МодульОбщегоМодуля',
    'BusinessProcessModule': 'МодульБизнесПроцесса',
    'TaskModule': 'МодульЗадачи',
    'ReportModule': 'МодульОтчёта',
    'DataProcessorModule': 'МодульОбработки',
    'ChartOfAccountsModule': 'МодульПланаСчетов',
    'ChartOfCharacteristicTypesModule': 'МодульПланаВидовХарактеристик',
    'ChartOfCalculationTypesModule': 'МодульПланаВидовРасчёта',
    'ExchangePlanModule': 'МодульПланаОбмена',
    'InformationRegisterModule': 'МодульРегистраСведений',
    'AccumulationRegisterModule': 'МодульРегистраНакопления',
    'AccountingRegisterModule': 'МодульРегистраБухгалтерии',
    'CalculationRegisterModule': 'МодульРегистраРасчёта',

    'TabularSectionAttribute': 'РеквизитТабличнойЧасти',
}


# =========================================================================
#  Работа с путями и настройками
# =========================================================================

class AppPaths:
    """Вычисляет пути, которые использует программа.

    Определяет, где хранить settings.json и config_markers.json:
      - обычный .py            -> рядом со скриптом;
      - .exe и рядом есть      -> рядом с .exe (портативный режим);
        settings.json
      - .exe без settings.json -> %APPDATA%\\<APP_NAME>
    """

    @staticmethod
    def program_dir() -> str:
        """Папка, где лежит .exe или .py."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def appdata_dir() -> str:
        """%APPDATA%\\<APP_NAME> с гарантированным созданием."""
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        folder = os.path.join(base, APP_NAME)
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            pass
        return folder

    @classmethod
    def default_settings_dir(cls) -> str:
        """Папка по умолчанию для settings.json и config_markers.json."""
        prog = cls.program_dir()
        if not getattr(sys, 'frozen', False):
            return prog
        if os.path.exists(os.path.join(prog, SETTINGS_FILENAME)):
            return prog
        return cls.appdata_dir()

    @classmethod
    def settings_path(cls, settings_dir: Optional[str] = None) -> str:
        """Полный путь к settings.json в указанной (или дефолтной) папке."""
        if settings_dir is None:
            settings_dir = cls.default_settings_dir()
        return os.path.join(settings_dir, SETTINGS_FILENAME)

    @staticmethod
    def markers_path(data_dir: str) -> str:
        """Полный путь к config_markers.json в папке данных."""
        return os.path.join(data_dir, MARKERS_FILENAME)

    @staticmethod
    def open_folder(path: str) -> None:
        """Открывает папку в системном проводнике/файловом менеджере."""
        try:
            if os.name == 'nt':
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
        except Exception:
            pass


class SettingsStore:
    """Чтение и запись settings.json.

    Хранимые ключи:
      settings_dir - где лежат settings.json и config_markers.json;
      data_dir     - где хранится список префиксов;
      xml_dir      - папка открытия XML по умолчанию;
      export_dir   - папка сохранения CSV по умолчанию.
    """

    DEFAULTS: Dict[str, str] = {
        'settings_dir': '',
        'data_dir': '',
        'xml_dir': '',
        'export_dir': '',
    }

    def __init__(self) -> None:
        self._settings = self._load()

    # --- публичный интерфейс ---

    def get(self, key: str, default: str = '') -> str:
        return self._settings.get(key, default)

    def set(self, key: str, value: str) -> None:
        self._settings[key] = value or ''

    def as_dict(self) -> Dict[str, str]:
        return dict(self._settings)

    def update(self, values: Dict[str, str]) -> None:
        self._settings.update(values)

    def save(self) -> None:
        """Сохраняет текущие настройки в settings.json."""
        path = AppPaths.settings_path(self._settings.get('settings_dir'))
        payload = {
            'settings_dir': self._settings.get('settings_dir', ''),
            'data_dir': self._settings.get('data_dir', ''),
            'xml_dir': self._settings.get('xml_dir', ''),
            'export_dir': self._settings.get('export_dir', ''),
        }
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except OSError:
            pass
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # --- внутренняя логика ---

    def _load(self) -> Dict[str, str]:
        default_dir = AppPaths.default_settings_dir()
        result = {
            'settings_dir': default_dir,
            'data_dir': default_dir,
            'xml_dir': '',
            'export_dir': '',
        }

        path = AppPaths.settings_path(default_dir)
        if not os.path.exists(path):
            return result

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return result
        except Exception:
            return result

        sd = data.get('settings_dir') or default_dir
        sd = os.path.abspath(os.path.expanduser(str(sd)))
        result['settings_dir'] = sd

        dd = data.get('data_dir') or sd
        dd = os.path.abspath(os.path.expanduser(str(dd)))
        result['data_dir'] = dd

        result['xml_dir'] = str(data.get('xml_dir') or '')
        result['export_dir'] = str(data.get('export_dir') or '')
        return result


class MarkersStore:
    """Чтение и запись config_markers.json (список префиксов)."""

    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self._markers: List[str] = self._load()

    # --- публичный интерфейс ---

    @property
    def items(self) -> List[str]:
        return list(self._markers)

    def set_items(self, markers: Sequence[str]) -> None:
        self._markers = [str(m) for m in markers if str(m).strip()]

    def is_custom_name(self, name: str) -> bool:
        """True, если имя начинается с одного из префиксов."""
        if not name:
            return False
        return any(name.startswith(m) for m in self._markers if m)

    def reload(self, new_data_dir: Optional[str] = None) -> None:
        """Перечитывает файл (при смене папки данных)."""
        if new_data_dir is not None:
            self.data_dir = new_data_dir
        self._markers = self._load()

    def save(self, target_dir: Optional[str] = None) -> None:
        """Записывает список префиксов в файл."""
        d = target_dir or self.data_dir
        os.makedirs(d, exist_ok=True)
        path = AppPaths.markers_path(d)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'markers': list(self._markers)}, f,
                      ensure_ascii=False, indent=2)

    # --- внутренняя логика ---

    def _load(self) -> List[str]:
        path = AppPaths.markers_path(self.data_dir)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get('markers'), list):
                return [str(x) for x in data['markers'] if str(x).strip()]
            if isinstance(data, list):
                return [str(x) for x in data if str(x).strip()]
        except Exception:
            pass
        return list(DEFAULT_MARKERS)


# =========================================================================
#  Парсинг XML
# =========================================================================

@dataclass
class MetadataRow:
    """Одна строка таблицы: разобранный элемент конфигурации.

    Поля хранятся в словаре `data` - это позволяет динамически
    добавлять колонки, которых не было в базовом наборе.
    """
    data: Dict[str, str] = field(default_factory=dict)

    def get(self, key: str, default: str = '') -> str:
        return self.data.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.data[key] = value


class XmlParser:
    """Потоковый парсер ConfigDumpInfo.xml."""

    def __init__(self, path: str,
                 on_count: Optional[Callable[[int], None]] = None,
                 on_progress: Optional[Callable[[int, int], None]] = None):
        """on_count(n) - вызывается редко, по мере подсчёта;
        on_progress(done, total) - вызывается при парсинге."""
        self.path = path
        self.on_count = on_count
        self.on_progress = on_progress
        self._ns_uri = ''
        self._total = 0
        self._tag_metadata = 'Metadata'

    # --- публичный интерфейс ---

    def run(self, markers: MarkersStore
            ) -> Tuple[List[MetadataRow], List[str]]:
        """Полный цикл: обнаружение ns, подсчёт, парсинг.
        Возвращает (строки, список колонок)."""
        self._detect_namespace()
        self._count()
        return self._parse(markers)

    # --- этапы ---

    def _detect_namespace(self) -> None:
        """Определяет URI пространства имён XML (если есть)."""
        ns = ''
        try:
            for _, elem in ET.iterparse(self.path, events=('start',)):
                t = elem.tag
                if t.startswith('{'):
                    ns = t[1:t.index('}')]
                break
        except Exception:
            ns = ''
        self._ns_uri = ns
        self._tag_metadata = f'{{{ns}}}Metadata' if ns else 'Metadata'

    def _count(self) -> None:
        """Считает общее число элементов Metadata."""
        total = 0
        with open(self.path, 'rb') as fh:
            for _, elem in ET.iterparse(fh, events=('end',)):
                if elem.tag == self._tag_metadata:
                    total += 1
                    elem.clear()
                    if self.on_count and total % 100_000 == 0:
                        self.on_count(total)
        self._total = total

    def _parse(self, markers: MarkersStore
               ) -> Tuple[List[MetadataRow], List[str]]:
        """Читает файл ещё раз, извлекая строки и колонки."""
        rows: List[MetadataRow] = []
        extra_cols: set = set()
        done = 0

        with open(self.path, 'rb') as fh:
            for _, elem in ET.iterparse(fh, events=('end',)):
                if elem.tag != self._tag_metadata:
                    continue

                row = self._build_row(elem, markers)
                extra_cols.update(elem.attrib)
                rows.append(row)

                elem.clear()
                done += 1
                if self.on_progress and done % 500 == 0:
                    self.on_progress(done, self._total)

        if self.on_progress:
            self.on_progress(done, self._total)

        columns = BASE_COLUMNS + sorted(
            c for c in extra_cols if c not in BASE_COLUMNS)
        return rows, columns

    @staticmethod
    def _build_row(elem: ET.Element, markers: MarkersStore) -> MetadataRow:
        """Строит MetadataRow из XML-элемента."""
        name = elem.get('name', '')
        parsed = XmlParser._split_name(name)
        parsed.update(elem.attrib)

        parsed['ПризнакОбъекта'] = (
            CUSTOM_TAG if markers.is_custom_name(parsed.get('ИмяОбъекта', ''))
            else STD_TAG
        )
        return MetadataRow(data=parsed)

    @staticmethod
    def _split_name(name: str) -> Dict[str, str]:
        """Разбирает строку name из XML в набор русских полей."""
        parts = name.split('.') if name else []
        parts += [''] * (6 - len(parts))

        type_ru = TYPE_TRANSLATIONS.get(parts[0], parts[0])
        kind1_ru = KIND_TRANSLATIONS.get(parts[2], parts[2])
        kind2_ru = KIND_TRANSLATIONS.get(parts[4], parts[4])

        path_parts = [type_ru, parts[1], kind1_ru, parts[3], kind2_ru, parts[5]]
        if len(parts) > 6:
            path_parts.extend(parts[6:])
        path = '.'.join(p for p in path_parts if p)

        return {
            'ТипОбъекта': type_ru,
            'ИмяОбъекта': parts[1],
            'ВидЭлемента': kind1_ru,
            'ИмяЭлемента': parts[3],
            'ВидВложенногоЭлемента': kind2_ru,
            'ИмяВложенногоЭлемента': parts[5],
            'ПутьЭлемента': path,
            'ПризнакОбъекта': NONE_TAG,
        }


# =========================================================================
#  Поиск
# =========================================================================

class QueryCompiler:
    """Преобразует строку шаблона в скомпилированный regex.

    Синтаксис: ^ начало, $ конец, ? один символ, * любое число.
    Если шаблон пустой - возвращает None.
    """

    @staticmethod
    def compile(pattern: str) -> Optional[re.Pattern]:
        if not pattern:
            return None

        p = pattern.strip()
        anchored_start = p.startswith('^') and len(p) > 1
        anchored_end = p.endswith('$') and len(p) > 1

        if anchored_start:
            p = p[1:]
        if anchored_end:
            p = p[:-1]

        p = re.escape(p)
        p = p.replace(r'\?', '.').replace(r'\*', '.*')

        regex = (('^' if anchored_start else '') + p +
                 ('$' if anchored_end else ''))
        return re.compile(regex, re.IGNORECASE)


class QueryMatcher:
    """Проверяет значение на соответствие скомпилированному regex.

    Специально сделан маленьким: одна функция - одна задача.
    """

    def __init__(self, regex: Optional[re.Pattern]) -> None:
        self.regex = regex

    def matches(self, value: object) -> bool:
        if self.regex is None:
            return False
        return self.regex.search(str(value)) is not None


# =========================================================================
#  Общие виджеты и миксины
# =========================================================================

class CopyableLabel(tk.Label):
    """Метка, значение которой можно скопировать.

    - правый клик -> контекстное меню (Копировать / Вставить в поиск);
    - двойной клик -> копирует значение в буфер.
    """

    def __init__(self, parent, text: str, app=None,
                 copy_value: Optional[str] = None, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self._full_text = text
        self._copy_text = text if copy_value is None else copy_value
        self._has_copy_value = copy_value is not None
        self._app = app
        self.bind('<Button-3>', self._context_menu)
        self.bind('<Double-Button-1>', lambda *_: self._copy())
        self.configure(cursor='hand2')

    # --- обработчики ---

    def _context_menu(self, event) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label='Копировать', command=self._copy)
        if self._has_copy_value:
            menu.add_command(label='Копировать строку целиком',
                             command=self._copy_full)
        if self._app is not None:
            menu.add_command(label='Копировать и вставить в поиск',
                             command=self._copy_and_paste)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # --- действия ---

    def _copy(self) -> None:
        self._clipboard_set(self._copy_text)

    def _copy_full(self) -> None:
        self._clipboard_set(self._full_text)

    def _copy_and_paste(self) -> None:
        self._copy()
        try:
            self._app._paste_to_search()
        except Exception:
            pass

    def _clipboard_set(self, value: str) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(value)
            self.update()
        except tk.TclError:
            pass


class CardFrame(tk.Frame):
    """Рамка-«карточка»: белый фон панели + тонкая граница."""

    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', COLORS['panel'])
        kwargs.setdefault('highlightthickness', 1)
        kwargs.setdefault('highlightbackground', COLORS['border'])
        super().__init__(parent, **kwargs)


class ScrollableMixin:
    """Миксин: привязывает колесо мыши к указанному Canvas.

    Используется диалогами, где содержимое может не помещаться.
    """

    _wheel_widgets: List[tk.Widget]

    def _bind_wheel_recursive(self, widget: tk.Widget) -> None:
        try:
            widget.bind('<MouseWheel>', self._on_wheel)
        except Exception:
            pass
        self._wheel_widgets.append(widget)
        for child in widget.winfo_children():
            self._bind_wheel_recursive(child)

    def _unbind_wheel_all(self) -> None:
        for w in self._wheel_widgets:
            try:
                w.unbind('<MouseWheel>')
            except Exception:
                pass
        self._wheel_widgets.clear()

    def _on_wheel(self, event) -> str:
        """Прокрутка Canvas только если содержимое не помещается."""
        try:
            first, last = self._scroll_canvas.yview()
            if first <= 0.0 and last >= 1.0:
                return 'break'
            self._scroll_canvas.yview_scroll(
                int(-1 * (event.delta / 120)), 'units')
        except Exception:
            pass
        return 'break'


# =========================================================================
#  Диалоги
# =========================================================================

class HelpWindow(tk.Toplevel):
    """Окно инструкции пользователя."""

    # Содержимое разбито на разделы; каждый раздел - список блоков.
    # Типы блоков: text, code, steps, samples, kv.
    SECTIONS: List[Tuple[str, List[Dict]]] = [
        ('Что это за программа', [
            {'type': 'text',
             'text': 'Это просмотрщик файла ConfigDumpInfo.xml - того '
                     'самого, который выгружает Конфигуратор 1С. '
                     'Программа показывает все объекты конфигурации '
                     'списком, позволяет искать по ним, отделять свои '
                     '(кастомные) объекты от типовых и сохранять '
                     'результат в CSV, который открывается в Excel.'},
        ]),

        ('Как начать работу', [
            {'type': 'steps', 'items': [
                'Нажмите "Открыть XML" и выберите файл ConfigDumpInfo.xml. '
                'Дождитесь, пока прогресс-бар дойдет до 100%.',
                'В таблице появится список всех объектов конфигурации.',
                'При необходимости настройте список своих префиксов '
                'кнопкой "Префиксы" (по умолчанию - ПЛ_).',
                'Введите запрос в поле "Поиск" - таблица отфильтруется.',
                'Нажмите "Экспорт в CSV", чтобы сохранить результат.',
            ]},
        ]),

        ('Что видно в таблице', [
            {'type': 'text',
             'text': 'Каждая строка - один элемент конфигурации. '
                     'Основные колонки:'},
            {'type': 'kv', 'items': [
                ('ТипОбъекта', 'Справочник, Документ, РегистрСведений и т. п.'),
                ('ИмяОбъекта', 'Имя самого объекта, например ФизическиеЛица.'),
                ('ВидЭлемента', 'Что это внутри объекта: Реквизит, '
                                'ТабличнаяЧасть, Форма, Команда и т. д.'),
                ('ИмяЭлемента', 'Имя этого реквизита, формы или команды.'),
                ('ПутьЭлемента', 'Полный путь по-русски, например: '
                                 'Справочник.ФизическиеЛица.Реквизит.ФИО.'),
                ('ПризнакОбъекта', 'Кастомный - если имя начинается '
                                   'с вашего префикса, иначе Стандартный.'),
            ]},
            {'type': 'text',
             'text': 'Ширину колонок можно менять мышью, потянув за '
                     'границу в заголовке. Двойной клик по границе - '
                     'подгон под самое длинное значение. Клик по '
                     'заголовку - сортировка.'},
        ]),

        ('Как отделить свои объекты от типовых', [
            {'type': 'text',
             'text': 'Программа считает объект кастомным, если его имя '
                     'начинается с одного из ваших префиксов. Список '
                     'префиксов хранится в файле config_markers.json '
                     'и редактируется кнопкой "Префиксы".'},
            {'type': 'steps', 'items': [
                'Нажмите "Префиксы" на верхней панели.',
                'Введите префикс (например, ПЛ_) и нажмите Enter.',
                'Повторите для всех нужных префиксов.',
                'Нажмите "Сохранить" - программа сразу пересчитает '
                'признак у всех строк.',
            ]},
            {'type': 'text',
             'text': 'После этого в фильтре "Признак объекта" можно '
                     'выбрать "Только кастомные" или "Только стандартные".'},
        ]),

        ('Поиск', [
            {'type': 'text',
             'text': 'Обычный текст ищется как подстрока, регистр не важен. '
                     'Например, запрос "ФИО" найдет и "ФИО", и "фИо", '
                     'и "ПолноеФИО".'},
            {'type': 'text',
             'text': 'Если нужно точнее, используйте четыре знака:'},
            {'type': 'kv', 'items': [
                ('^', 'в начале запроса - поле начинается с ...'),
                ('$', 'в конце запроса - поле заканчивается на ...'),
                ('?', 'ровно один любой символ'),
                ('*', 'любое количество любых символов'),
            ]},
            {'type': 'text', 'text': 'Примеры:'},
            {'type': 'samples', 'items': [
                ('ФИО', 'найдется везде, где встречается ФИО'),
                ('^ФИО', 'поле начинается с ФИО'),
                ('ФИО$', 'поле заканчивается на ФИО'),
                ('^ФИО$', 'поле ровно ФИО, без лишних символов'),
                ('Ф?О', 'между Ф и О ровно одна буква'),
                ('Ф*О', 'между Ф и О любое число букв'),
            ]},
            {'type': 'text',
             'text': 'По умолчанию поиск идет по всем колонкам. Если '
                     'это слишком широко - выберите "Только по выбранным" '
                     'и отметьте нужные колонки галочками.'},
            {'type': 'text',
             'text': 'Вставить текст в поле поиска можно через Ctrl+V '
                     'или правой кнопкой мыши. Кнопка "Очистить поиск" '
                     'сбрасывает запрос.'},
        ]),

        ('Фильтр по признаку объекта', [
            {'type': 'text',
             'text': 'Выпадающий список "Признак объекта" позволяет '
                     'показать только кастомные строки, только '
                     'стандартные или все сразу.'},
        ]),

        ('Экспорт в CSV', [
            {'type': 'text',
             'text': 'Файл сохраняется в кодировке UTF-8 с BOM и '
                     'разделителем ";" - Excel и LibreOffice открывают '
                     'его без дополнительных настроек.'},
            {'type': 'steps', 'items': [
                'Нажмите "Экспорт в CSV".',
                'Выберите: сохранить все строки или только те, '
                'что подсветились при поиске.',
                'Укажите имя файла и папку.',
                'Готово - программа покажет, сколько записей сохранено.',
            ]},
        ]),

        ('Объединение нескольких CSV', [
            {'type': 'text',
             'text': 'Если вы сделали несколько выгрузок и хотите '
                     'свести их в один файл - используйте кнопку '
                     '"Объединить CSV".'},
            {'type': 'steps', 'items': [
                'Выберите папку с CSV-файлами.',
                'Отметьте галочками те, которые нужно объединить.',
                'Введите имя итогового файла (по умолчанию merged.csv).',
                'Нажмите "Объединить".',
            ]},
            {'type': 'text',
             'text': 'Колонки берутся из первого файла в списке, '
                     'пустые файлы пропускаются. Порядок файлов - '
                     'по алфавиту; если нужен другой порядок, '
                     'переименуйте файлы с числовыми префиксами: '
                     '01_..., 02_...'},
        ]),

        ('Настройки', [
            {'type': 'text',
             'text': 'Кнопка "Настройки" открывает окно с путями, '
                     'которые программа использует по умолчанию.'},
            {'type': 'kv', 'items': [
                ('Папка настроек', 'где лежат settings.json и '
                                   'config_markers.json'),
                ('Папка данных', 'где хранится список префиксов'),
                ('Папка XML', 'откуда открывается ConfigDumpInfo.xml'),
                ('Папка экспорта', 'куда сохраняются CSV-файлы'),
            ]},
            {'type': 'text',
             'text': 'По умолчанию настройки лежат в '
                     '%APPDATA%\\ConfigDumpParser. Если положить '
                     'settings.json рядом с программой, она перейдет '
                     'в портативный режим и будет хранить настройки '
                     'рядом с собой.'},
        ]),
    ]

    # Якорь -> индекс раздела для быстрого перехода к нужной части
    ANCHORS: Dict[str, int] = {
        'start': 0,
        'open': 1,
        'columns': 2,
        'markers': 3,
        'search': 4,
    }

    def __init__(self, parent: tk.Misc, anchor: str = 'start'):
        super().__init__(parent)
        self.title('Инструкция')
        self.geometry('1040x780')
        self.minsize(720, 480)
        self.transient(parent)
        self.configure(bg=COLORS['bg'])

        # Ссылка на родителя нужна CopyableLabel для вставки в поиск
        self._parent = parent
        # Внутренние ссылки на Canvas и содержимое
        self._canvas: Optional[tk.Canvas] = None
        self._content: Optional[tk.Frame] = None
        self._content_window_id: Optional[int] = None
        self._wheel_bound = False

        # Порядок сборки: header сверху, footer снизу, body растягивается
        self._build_header()
        self._build_body()
        self._build_footer()

        # Размещение относительно родителя
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 1040) // 2
        y = parent.winfo_rooty() + 40
        self.geometry(f'1040x780+{max(0, x)}+{max(0, y)}')

        self.bind('<Escape>', lambda *_: self._close())
        self.protocol('WM_DELETE_WINDOW', self._close)

        # Автопрокрутка к указанному разделу
        self.after(50, lambda: self._scroll_to(anchor))

    # --- сборка окна ---

    def _build_header(self) -> None:
        """Шапка: заголовок + пояснение + разделитель."""
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=24, pady=18)

        tk.Label(hdr, text='Инструкция',
                 font=FONTS['title'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(
            hdr,
            text='Коротко о том, что делает программа и как ей '
                 'пользоваться. Если что-то непонятно - смотрите '
                 'соответствующий раздел.',
            font=FONTS['body'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT,
        ).pack(anchor='w', pady=(6, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(fill=tk.X)

    def _build_body(self) -> None:
        """Тело: Canvas + вертикальный скролл + Frame контента."""
        container = tk.Frame(self, bg=COLORS['bg'])
        container.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(container, highlightthickness=0,
                                 bg=COLORS['bg'])
        vsb = ttk.Scrollbar(container, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_window_id = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        # Растягиваем контент по ширине Canvas и обновляем scrollregion
        self._content.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))

        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(
                self._content_window_id, width=e.width))

        self._render_sections()

        # Колесо мыши привязываем ко всему окну (bind_all)
        self._canvas.bind_all('<MouseWheel>', self._on_wheel)
        self._wheel_bound = True

    def _build_footer(self) -> None:
        """Подвал: разделитель + кнопка Закрыть."""
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(fill=tk.X)

        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=24, pady=12)

        ttk.Button(ftr, text='Закрыть', style='Secondary.TButton',
                   command=self._close).pack(side=tk.RIGHT)

    # --- отрисовка разделов ---

    def _render_sections(self) -> None:
        """Пробегает по всем разделам и рисует их."""
        for idx, (title, blocks) in enumerate(self.SECTIONS):
            self._render_section(idx, title, blocks)

    def _render_section(self, idx: int, title: str,
                        blocks: List[Dict]) -> None:
        """Отрисовывает один раздел: заголовок + блоки."""
        outer = tk.Frame(self._content, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=20, pady=(16, 6))

        head = tk.Frame(outer, bg=COLORS['bg'])
        head.pack(fill=tk.X)

        tk.Label(head, text=title,
                 font=FONTS['section'],
                 fg=COLORS['accent'], bg=COLORS['bg']
                 ).pack(anchor='w')

        tk.Frame(outer, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(6, 10))

        for block in blocks:
            self._render_block(outer, block)

    def _render_block(self, parent: tk.Frame, block: Dict) -> None:
        """Рисует один блок: text / code / steps / samples / kv."""
        btype = block.get('type')

        if btype == 'text':
            tk.Label(
                parent, text=block.get('text', ''),
                font=FONTS['body'],
                fg=COLORS['text'], bg=COLORS['bg'],
                justify=tk.LEFT, anchor='w',
                wraplength=940,
            ).pack(anchor='w', fill=tk.X, pady=(0, 6))

        elif btype == 'code':
            box = CardFrame(parent)
            box.pack(fill=tk.X, pady=(4, 8))
            CopyableLabel(
                box, block.get('text', ''),
                app=self._parent,
                font=FONTS['mono'],
                fg=COLORS['pattern_fg'], bg=COLORS['panel'],
                justify=tk.LEFT, anchor='w',
            ).pack(anchor='w', padx=12, pady=10)

        elif btype == 'steps':
            for i, step in enumerate(block.get('items', []), 1):
                row = tk.Frame(parent, bg=COLORS['bg'])
                row.pack(fill=tk.X, pady=2)
                tk.Label(row, text=f'{i}.',
                         font=FONTS['step_num'],
                         fg=COLORS['accent'], bg=COLORS['bg'],
                         width=3, anchor='nw'
                         ).pack(side=tk.LEFT)
                CopyableLabel(
                    row, step,
                    app=self._parent,
                    font=FONTS['body'],
                    fg=COLORS['text'], bg=COLORS['bg'],
                    justify=tk.LEFT, anchor='w',
                    wraplength=920,
                ).pack(side=tk.LEFT, fill=tk.X)

        elif btype == 'samples':
            for sample, note in block.get('items', []):
                self._render_sample_row(parent, sample, note)

        elif btype == 'kv':
            for key, val in block.get('items', []):
                self._render_kv_row(parent, key, val)

    def _render_sample_row(self, parent: tk.Frame, sample: str,
                           note: str) -> None:
        """Строка «шаблон - пояснение» для раздела Поиск."""
        row = CardFrame(parent)
        row.pack(fill=tk.X, pady=2)

        inner = tk.Frame(row, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=12, pady=6)
        inner.columnconfigure(0, minsize=180, weight=0)
        inner.columnconfigure(1, weight=1)

        CopyableLabel(
            inner, sample,
            app=self._parent,
            copy_value=sample,
            font=FONTS['mono'],
            fg=COLORS['pattern_fg'], bg=COLORS['panel'],
            anchor='w', justify=tk.LEFT,
        ).grid(row=0, column=0, sticky='nw', padx=(0, 16))

        CopyableLabel(
            inner, note,
            app=self._parent,
            font=FONTS['body'],
            fg=COLORS['text'], bg=COLORS['panel'],
            anchor='w', justify=tk.LEFT, wraplength=680,
        ).grid(row=0, column=1, sticky='ew')

    def _render_kv_row(self, parent: tk.Frame, key: str, val: str) -> None:
        """Строка «ключ - значение» в две колонки."""
        row = CardFrame(parent)
        row.pack(fill=tk.X, pady=2)

        inner = tk.Frame(row, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=12, pady=8)
        inner.columnconfigure(0, minsize=240, weight=0)
        inner.columnconfigure(1, weight=1)

        CopyableLabel(
            inner, key,
            app=self._parent,
            font=FONTS['kv_key'],
            fg=COLORS['accent_dark'], bg=COLORS['panel'],
            anchor='nw', justify=tk.LEFT,
        ).grid(row=0, column=0, sticky='nw', padx=(0, 12))

        CopyableLabel(
            inner, val,
            app=self._parent,
            font=FONTS['body'],
            fg=COLORS['text'], bg=COLORS['panel'],
            anchor='w', justify=tk.LEFT, wraplength=680,
        ).grid(row=0, column=1, sticky='ew')

    # --- служебные ---

    def _scroll_to(self, anchor: str) -> None:
        """Прокрутка к разделу по якорю (start/open/columns/...)."""
        if not self._canvas:
            return
        idx = self.ANCHORS.get(anchor, 0)
        total = max(1, len(self.SECTIONS))
        self._canvas.yview_moveto(idx / total)

    def _on_wheel(self, event) -> None:
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                      'units')
        except Exception:
            pass

    def _close(self) -> None:
        """Снимает bind_all и возвращает фокус родителю."""
        if self._wheel_bound:
            try:
                self.unbind_all('<MouseWheel>')
            except Exception:
                pass
            self._wheel_bound = False
        try:
            self._parent.focus_set()
        except Exception:
            pass
        self.destroy()


class ExportDialog(tk.Toplevel):
    """Диалог выбора: экспортировать всё или только подсвеченное."""

    def __init__(self, parent: tk.Misc, has_query: bool,
                 n_all: int, n_matched: int):
        super().__init__(parent)
        self.title('Экспорт в CSV')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: 'all' / 'matched' / None (отмена)
        self.result: Optional[str] = None
        self.mode = tk.StringVar(value='matched' if has_query else 'all')

        card = CardFrame(self)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        tk.Label(inner, text='Что выгружать в CSV?',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w', pady=(0, 12))

        # Две радиокнопки. Вторая доступна только при активном поиске.
        self._radio(inner, f'Все строки ({self._fmt(n_all)})', 'all')
        self._radio(inner, f'Только подсвеченные ({self._fmt(n_matched)})',
                    'matched', enabled=has_query)

        btns = tk.Frame(inner, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(18, 0))
        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Экспорт', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        self._center_on_parent(parent, 380, 260)
        self.bind('<Return>', lambda *_: self._ok())
        self.bind('<Escape>', lambda *_: self._cancel())
        self.focus_set()

    @staticmethod
    def _fmt(n: int) -> str:
        """Число с пробелами как разделителями тысяч."""
        return f'{n:,}'.replace(',', ' ')

    def _radio(self, parent: tk.Frame, text: str, value: str,
               enabled: bool = True) -> None:
        rb = ttk.Radiobutton(parent, text=text,
                             variable=self.mode, value=value,
                             style='Card.TRadiobutton')
        rb.pack(anchor='w', pady=3, fill=tk.X)
        if not enabled:
            rb.state(['disabled'])

    def _center_on_parent(self, parent: tk.Misc, w: int, h: int) -> None:
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + 150
        self.geometry(f'{w}x{h}+{x}+{y}')

    def _ok(self) -> None:
        self.result = self.mode.get()
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


class SettingsDialog(tk.Toplevel, ScrollableMixin):
    """Окно настроек: редактор четырёх путей.

    Содержимое может не помещаться - тогда включается вертикальный
    скролл. Колесо мыши работает только внутри окна.
    """

    BTN_WIDTH = 12

    def __init__(self, parent: tk.Misc, settings: Dict[str, str]):
        super().__init__(parent)
        self.title('Настройки')
        self.minsize(680, 460)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: словарь новых значений / None (отмена)
        self.result: Optional[Dict[str, str]] = None
        self._settings = dict(settings)
        self.vars: Dict[str, tk.StringVar] = {}
        self._wheel_widgets = []

        self._canvas: Optional[tk.Canvas] = None
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._content: Optional[tk.Frame] = None
        self._content_win_id: Optional[int] = None

        self._place_window(parent, 800, 620)
        self._build_ui()

        self.bind('<Configure>', lambda e: self._refresh_scrollregion())
        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

        self.after(50, self._refresh_scrollregion)

    # --- размещение ---

    def _place_window(self, parent: tk.Misc, w: int, h: int) -> None:
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
        except Exception:
            sw, sh = 1280, 800

        w = min(w, sw - 80)
        h = min(h, sh - 120)
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 3)
        x = max(20, min(x, sw - w - 20))
        y = max(20, min(y, sh - h - 40))
        self.geometry(f'{w}x{h}+{x}+{y}')

    # --- сборка ---

    def _build_ui(self) -> None:
        # Footer крепим первым, чтобы он всегда был виден
        self._build_footer()
        self._build_header()
        self._build_body()

    def _build_footer(self) -> None:
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=18, pady=12)

        ttk.Button(ftr, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(ftr, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(side=tk.TOP, fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=18, pady=(16, 8))

        tk.Label(hdr, text='Настройки программы',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(
            hdr,
            text=('Здесь задаются пути, которые программа использует '
                  'по умолчанию. Пути можно менять в любой момент, '
                  'они сохраняются в settings.json.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT, anchor='w', wraplength=660,
        ).pack(anchor='w', fill=tk.X, pady=(4, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(
            side=tk.TOP, fill=tk.X)

    def _build_body(self) -> None:
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(body, highlightthickness=0,
                                 bg=COLORS['bg'])
        self._scroll_canvas = self._canvas  # для ScrollableMixin
        vsb = ttk.Scrollbar(body, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_win_id = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        self._content.bind('<Configure>',
                           lambda e: self._refresh_scrollregion())
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        # Карточка с полями
        card = CardFrame(self._content)
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        # Четыре строки настроек
        self._add_row(inner, 'settings_dir', 'Папка настроек',
                      'Где хранятся settings.json и config_markers.json. '
                      'По умолчанию - %APPDATA%\\' + APP_NAME + '.')
        self._add_row(inner, 'data_dir', 'Папка данных',
                      'Где хранится config_markers.json (список префиксов). '
                      'Обычно совпадает с папкой настроек.')
        self._add_row(inner, 'xml_dir', 'Папка XML по умолчанию',
                      'Откуда открывается ConfigDumpInfo.xml. '
                      'Можно оставить пустой - тогда программа запомнит '
                      'последнюю выбранную папку.')
        self._add_row(inner, 'export_dir', 'Папка экспорта по умолчанию',
                      'Куда сохраняются CSV-файлы и откуда берутся файлы '
                      'для объединения. Пусто - последняя выбранная папка.')

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._content)

    def _add_row(self, parent: tk.Frame, key: str, title: str,
                 hint: str) -> None:
        """Строка настройки: заголовок, пояснение, поле, кнопки."""
        tk.Label(parent, text=title, font=FONTS['kv_key'],
                 fg=COLORS['accent_dark'], bg=COLORS['panel'],
                 anchor='w').pack(anchor='w', pady=(10, 0))

        tk.Label(parent, text=hint, font=FONTS['body_sm'],
                 fg=COLORS['text_muted'], bg=COLORS['panel'],
                 anchor='w', justify=tk.LEFT,
                 wraplength=620).pack(anchor='w', fill=tk.X)

        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(4, 0))

        ttk.Button(row, text='Открыть', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=lambda k=key: self._open_typed(self.vars[k].get())
                   ).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=lambda k=key: self._pick_dir(k)
                   ).pack(side=tk.RIGHT)

        var = tk.StringVar(value=self._settings.get(key, ''))
        self.vars[key] = var
        tk.Entry(row, textvariable=var, font=FONTS['body'],
                 bg=COLORS['panel'], fg=COLORS['text'],
                 insertbackground=COLORS['accent']
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

    # --- скролл ---

    def _on_canvas_configure(self, event) -> None:
        if self._content_win_id is not None:
            self._canvas.itemconfigure(self._content_win_id,
                                       width=event.width)
        self._refresh_scrollregion()

    def _refresh_scrollregion(self) -> None:
        """Обновляет scrollregion; если содержимое помещается - скрывает."""
        try:
            self._content.update_idletasks()
            bbox = self._canvas.bbox('all')
            if not bbox:
                self._canvas.configure(scrollregion=(0, 0, 0, 0))
                return
            content_h = bbox[3] - bbox[1]
            canvas_h = self._canvas.winfo_height()
            if content_h <= canvas_h:
                self._canvas.configure(scrollregion=(0, 0, 0, 0))
                self._canvas.yview_moveto(0)
            else:
                self._canvas.configure(scrollregion=bbox)
        except Exception:
            pass

    # --- действия ---

    def _open_typed(self, path: str) -> None:
        path = (path or '').strip()
        if path and os.path.isdir(path):
            AppPaths.open_folder(path)
        elif path:
            messagebox.showinfo('Открыть',
                                'Папка не найдена:\n' + path, parent=self)

    def _pick_dir(self, key: str) -> None:
        initial = self.vars[key].get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Выберите папку',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self.vars[key].set(os.path.abspath(chosen))

    def _ok(self) -> None:
        result: Dict[str, str] = {}
        for k, v in self.vars.items():
            val = (v.get() or '').strip()
            if val:
                val = os.path.abspath(os.path.expanduser(val))
            result[k] = val

        if not result.get('settings_dir'):
            messagebox.showerror('Настройки',
                                 'Папка настроек не может быть пустой.',
                                 parent=self)
            return

        self.result = result
        self._cleanup_and_close()

    def _cancel(self) -> None:
        self.result = None
        self._cleanup_and_close()

    def _cleanup_and_close(self) -> None:
        self._unbind_wheel_all()
        try:
            self.destroy()
        except Exception:
            pass


class MarkersDialog(tk.Toplevel):
    """Редактор списка префиксов кастомных объектов."""

    def __init__(self, parent: tk.Misc, markers: Sequence[str],
                 data_dir: str,
                 on_change_dir: Optional[Callable[[str], bool]] = None):
        super().__init__(parent)
        self.title('Префиксы кастомных объектов')
        self.geometry('620x620')
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        # result: {'markers': [...], 'data_dir': '...'} / None
        self.result: Optional[Dict] = None
        self._markers = list(markers)
        self._data_dir = data_dir
        self._on_change_dir = on_change_dir

        self._build_ui()
        self._refresh()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 620) // 2
        y = parent.winfo_rooty() + 80
        self.geometry(f'620x620+{max(0, x)}+{max(0, y)}')

        self.entry.focus_set()
        self.bind('<Escape>', lambda *_: self._cancel())

    # --- сборка ---

    def _build_ui(self) -> None:
        card = CardFrame(self)
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        # Заголовок + пояснение
        tk.Label(inner, text='Префиксы имён кастомных объектов',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(
            inner,
            text=('Объект считается кастомным, если "ИмяОбъекта" '
                  'начинается с одного из префиксов.\n'
                  'Пример: ПЛ_, АБ_, Моё_.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT, anchor='w', wraplength=560,
        ).pack(anchor='w', fill=tk.X, pady=(4, 8))

        # Блок с путём к файлу префиксов
        self._build_path_box(inner)

        # Строка добавления нового префикса
        self._build_add_row(inner)

        # Список префиксов с прокруткой
        self._build_listbox(inner)

        # Кнопки удаления и очистки
        self._build_delete_row(inner)

        # Нижние кнопки Отмена/Сохранить
        self._build_actions(inner)

    def _build_path_box(self, parent: tk.Frame) -> None:
        path_box = tk.Frame(parent, bg=COLORS['panel_alt'],
                            highlightthickness=1,
                            highlightbackground=COLORS['border'])
        path_box.pack(fill=tk.X, pady=(0, 10))

        path_inner = tk.Frame(path_box, bg=COLORS['panel_alt'])
        path_inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(path_inner, text='Файл префиксов:',
                 font=FONTS['kv_key'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel_alt'], anchor='w'
                 ).pack(anchor='w')

        self._path_var = tk.StringVar(value=AppPaths.markers_path(self._data_dir))
        tk.Label(path_inner, textvariable=self._path_var,
                 font=FONTS['body_sm'], fg=COLORS['text'],
                 bg=COLORS['panel_alt'], anchor='w', justify=tk.LEFT,
                 wraplength=540
                 ).pack(anchor='w', fill=tk.X, pady=(2, 6))

        path_btns = tk.Frame(path_inner, bg=COLORS['panel_alt'])
        path_btns.pack(fill=tk.X)

        ttk.Button(path_btns, text='Открыть папку', style='Small.TButton',
                   command=self._open_folder).pack(side=tk.LEFT)
        ttk.Button(path_btns, text='Изменить путь...', style='Small.TButton',
                   command=self._change_dir).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(path_btns, text='Копировать путь', style='Small.TButton',
                   command=self._copy_path).pack(side=tk.LEFT, padx=(6, 0))

    def _build_add_row(self, parent: tk.Frame) -> None:
        add_row = tk.Frame(parent, bg=COLORS['panel'])
        add_row.pack(fill=tk.X, pady=(0, 8))

        self.entry = tk.Entry(add_row, font=FONTS['body'],
                              bg=COLORS['panel'], fg=COLORS['text'],
                              insertbackground=COLORS['accent'])
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind('<Return>', lambda *_: self._add())

        ttk.Button(add_row, text='Добавить', style='Small.TButton',
                   command=self._add).pack(side=tk.LEFT, padx=(8, 0))

    def _build_listbox(self, parent: tk.Frame) -> None:
        list_wrap = tk.Frame(parent, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_wrap, font=FONTS['mono'],
            bg=COLORS['panel'], fg=COLORS['text'],
            selectbackground=COLORS['accent'], selectforeground='white',
            activestyle='none', bd=0, highlightthickness=0,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=1, pady=1)

        sb = ttk.Scrollbar(list_wrap, orient='vertical',
                           command=self.listbox.yview,
                           style='Cyan.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=sb.set)

    def _build_delete_row(self, parent: tk.Frame) -> None:
        del_row = tk.Frame(parent, bg=COLORS['panel'])
        del_row.pack(fill=tk.X, pady=(8, 0))

        ttk.Button(del_row, text='Удалить выделенное', style='Small.TButton',
                   command=self._remove_selected).pack(side=tk.LEFT)
        ttk.Button(del_row, text='Очистить всё', style='Small.TButton',
                   command=self._clear).pack(side=tk.LEFT, padx=(8, 0))

    def _build_actions(self, parent: tk.Frame) -> None:
        btns = tk.Frame(parent, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(14, 0))

        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

    # --- действия ---

    def _open_folder(self) -> None:
        if os.path.isdir(self._data_dir):
            AppPaths.open_folder(self._data_dir)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + self._data_dir,
                                parent=self)

    def _copy_path(self) -> None:
        try:
            self.clipboard_clear()
            self.clipboard_append(self._path_var.get())
            self.update()
        except tk.TclError:
            pass

    def _change_dir(self) -> None:
        if self._on_change_dir is None:
            return
        chosen = filedialog.askdirectory(
            parent=self, title='Папка для config_markers.json',
            initialdir=(self._data_dir
                        if os.path.isdir(self._data_dir) else None))
        if not chosen:
            return
        chosen = os.path.abspath(chosen)
        try:
            ok = self._on_change_dir(chosen)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 'Не удалось сменить папку:\n' + str(e),
                                 parent=self)
            return
        if ok:
            self._data_dir = chosen
            self._path_var.set(AppPaths.markers_path(self._data_dir))
            self._markers = MarkersStore(self._data_dir).items
            self._refresh()

    def _refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        for m in self._markers:
            self.listbox.insert(tk.END, m)

    def _add(self) -> None:
        val = self.entry.get().strip()
        if not val:
            return
        if val in self._markers:
            self.entry.delete(0, tk.END)
            return
        self._markers.append(val)
        self.entry.delete(0, tk.END)
        self._refresh()

    def _remove_selected(self) -> None:
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            del self._markers[i]
        self._refresh()

    def _clear(self) -> None:
        if messagebox.askyesno('Очистить', 'Удалить все префиксы?',
                               parent=self):
            self._markers = []
            self._refresh()

    def _ok(self) -> None:
        self.result = {
            'markers': list(self._markers),
            'data_dir': self._data_dir,
        }
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


class MergeCsvDialog(tk.Toplevel, ScrollableMixin):
    """Окно объединения нескольких CSV в один."""

    BTN_WIDTH = 12

    def __init__(self, parent: tk.Misc, initial_dir: str = ''):
        super().__init__(parent)
        self.title('Объединение CSV')
        self.minsize(720, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result: Optional[Dict] = None
        self._initial_dir = (
            initial_dir if initial_dir and os.path.isdir(initial_dir)
            else os.path.expanduser('~'))

        # Список пар (путь, BooleanVar) - по одной на файл
        self._files: List[Tuple[str, tk.BooleanVar]] = []
        self._wheel_widgets = []

        self._canvas: Optional[tk.Canvas] = None
        self._scroll_canvas: Optional[tk.Canvas] = None
        self._list_frame: Optional[tk.Frame] = None
        self._list_win: Optional[int] = None

        self._place_window(parent, 900, 640)
        self._build_ui()
        self._reload_files()

        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

    # --- размещение ---

    def _place_window(self, parent: tk.Misc, w: int, h: int) -> None:
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
        except Exception:
            sw, sh = 1280, 800
        w = min(w, sw - 80)
        h = min(h, sh - 120)
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - h) // 3)
        x = max(20, min(x, sw - w - 20))
        y = max(20, min(y, sh - h - 40))
        self.geometry(f'{w}x{h}+{x}+{y}')

    # --- сборка ---

    def _build_ui(self) -> None:
        self._build_footer()
        self._build_header()
        self._build_body()

    def _build_footer(self) -> None:
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=18, pady=12)

        ttk.Button(ftr, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(ftr, text='Объединить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        tk.Label(ftr, text='Итоговый файл:', font=FONTS['body'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(side=tk.LEFT)

        self._out_name_var = tk.StringVar(value=DEFAULT_MERGED_NAME)
        tk.Entry(ftr, textvariable=self._out_name_var,
                 font=FONTS['body'], bg=COLORS['panel'],
                 fg=COLORS['text'], insertbackground=COLORS['accent'],
                 width=36).pack(side=tk.LEFT, padx=(8, 0), ipady=3)

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS['panel'])
        header.pack(side=tk.TOP, fill=tk.X)

        hdr = tk.Frame(header, bg=COLORS['panel'])
        hdr.pack(fill=tk.X, padx=18, pady=(16, 8))

        tk.Label(hdr, text='Объединение CSV-файлов',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(
            hdr,
            text=('Выберите папку, отметьте нужные файлы и укажите '
                  'имя итогового файла. Файлы читаются в UTF-8 с BOM, '
                  'разделитель - ";". Колонки берутся из первого '
                  'файла в списке, пустые файлы пропускаются.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'], bg=COLORS['panel'],
            justify=tk.LEFT, anchor='w', wraplength=820,
        ).pack(anchor='w', fill=tk.X, pady=(4, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(
            side=tk.TOP, fill=tk.X)

    def _build_body(self) -> None:
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._build_dir_row(body)
        self._build_bulk_row(body)
        self._build_list(body)

    def _build_dir_row(self, parent: tk.Frame) -> None:
        dir_row = tk.Frame(parent, bg=COLORS['bg'])
        dir_row.pack(fill=tk.X, padx=18, pady=(12, 6))

        tk.Label(dir_row, text='Папка с CSV:', font=FONTS['kv_key'],
                 fg=COLORS['accent_dark'], bg=COLORS['bg']
                 ).pack(side=tk.LEFT, padx=(0, 8))

        self._dir_var = tk.StringVar(value=self._initial_dir)
        tk.Entry(dir_row, textvariable=self._dir_var, font=FONTS['body'],
                 bg=COLORS['panel'], fg=COLORS['text'],
                 insertbackground=COLORS['accent']
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        ttk.Button(dir_row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._pick_dir).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(dir_row, text='Обновить', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._reload_files).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(dir_row, text='Открыть', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._open_dir).pack(side=tk.LEFT, padx=(4, 0))

    def _build_bulk_row(self, parent: tk.Frame) -> None:
        bulk = tk.Frame(parent, bg=COLORS['bg'])
        bulk.pack(fill=tk.X, padx=18, pady=(2, 6))

        ttk.Button(bulk, text='Выделить все', style='Small.TButton',
                   command=lambda: self._set_all(True)).pack(side=tk.LEFT)
        ttk.Button(bulk, text='Снять все', style='Small.TButton',
                   command=lambda: self._set_all(False)
                   ).pack(side=tk.LEFT, padx=(6, 0))

        self._count_var = tk.StringVar(value='Файлов: 0')
        tk.Label(bulk, textvariable=self._count_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg']).pack(side=tk.RIGHT)

    def _build_list(self, parent: tk.Frame) -> None:
        list_wrap = tk.Frame(parent, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        self._canvas = tk.Canvas(list_wrap, highlightthickness=0,
                                 bg=COLORS['panel'])
        self._scroll_canvas = self._canvas
        vsb = ttk.Scrollbar(list_wrap, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=1, pady=1)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._list_frame = tk.Frame(self._canvas, bg=COLORS['panel'])
        self._list_win = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor='nw')

        self._list_frame.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))
        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(self._list_win,
                                                 width=e.width))

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    # --- файлы ---

    def _pick_dir(self) -> None:
        initial = self._dir_var.get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Папка с CSV',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self._dir_var.set(os.path.abspath(chosen))
            self._reload_files()

    def _open_dir(self) -> None:
        d = self._dir_var.get()
        if d and os.path.isdir(d):
            AppPaths.open_folder(d)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + d, parent=self)

    def _reload_files(self) -> None:
        """Перечитывает список CSV-файлов в выбранной папке."""
        self._unbind_wheel_all()

        for w in self._list_frame.winfo_children():
            w.destroy()
        self._files.clear()

        folder = self._dir_var.get()
        if not os.path.isdir(folder):
            self._count_var.set('Файлов: 0 (папка не найдена)')
            self._bind_wheel_recursive(self._canvas)
            self._bind_wheel_recursive(self._list_frame)
            return

        try:
            names = sorted(
                f for f in os.listdir(folder)
                if f.lower().endswith('.csv')
                and os.path.isfile(os.path.join(folder, f))
            )
        except OSError as e:
            messagebox.showerror('Чтение папки', str(e), parent=self)
            self._bind_wheel_recursive(self._canvas)
            self._bind_wheel_recursive(self._list_frame)
            return

        for name in names:
            self._add_file_row(os.path.join(folder, name), name)

        self._count_var.set(f'Файлов: {len(self._files)}')

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    def _add_file_row(self, full_path: str, name: str) -> None:
        """Одна строка списка файлов: чекбокс + имя + размер."""
        var = tk.BooleanVar(value=True)
        self._files.append((full_path, var))

        row = tk.Frame(self._list_frame, bg=COLORS['panel'])
        row.pack(fill=tk.X, padx=6, pady=1)

        ttk.Checkbutton(row, text=name, variable=var,
                        style='Card.TCheckbutton'
                        ).pack(side=tk.LEFT, anchor='w')

        try:
            size_txt = self._human_size(os.path.getsize(full_path))
        except OSError:
            size_txt = ''

        tk.Label(row, text=size_txt, font=FONTS['body_sm'],
                 fg=COLORS['text_muted'], bg=COLORS['panel']
                 ).pack(side=tk.RIGHT)

    @staticmethod
    def _human_size(n: float) -> str:
        for unit in ('Б', 'КБ', 'МБ', 'ГБ'):
            if n < 1024:
                return (f'{n:.0f} {unit}'
                        if unit == 'Б' else f'{n:.1f} {unit}')
            n /= 1024
        return f'{n:.1f} ТБ'

    def _set_all(self, value: bool) -> None:
        for _, var in self._files:
            var.set(value)

    # --- объединение ---

    def _ok(self) -> None:
        folder = self._dir_var.get()
        if not os.path.isdir(folder):
            messagebox.showerror('Объединение',
                                 'Папка не найдена:\n' + folder,
                                 parent=self)
            return

        selected = [p for p, var in self._files if var.get()]
        if not selected:
            messagebox.showinfo('Объединение',
                                'Не выбрано ни одного файла.',
                                parent=self)
            return

        out_name = (self._out_name_var.get() or '').strip() \
            or DEFAULT_MERGED_NAME
        if not out_name.lower().endswith('.csv'):
            out_name += '.csv'

        out_path = os.path.join(folder, out_name)
        if os.path.exists(out_path) and not messagebox.askyesno(
                'Перезапись',
                f'Файл уже существует:\n{out_path}\nПерезаписать?',
                parent=self):
            return

        try:
            files_count, rows_count, columns = self._merge(
                selected, out_path)
        except Exception as e:
            messagebox.showerror('Ошибка объединения', str(e), parent=self)
            return

        self.result = {
            'path': out_path,
            'files': files_count,
            'rows': rows_count,
            'columns': columns,
        }
        self._cleanup_and_close()

    def _merge(self, paths: List[str], out_path: str
               ) -> Tuple[int, int, List[str]]:
        """Объединяет CSV-файлы в один.

        Колонки берутся из первого непустого файла, порядок колонок
        сохраняется. Пустые файлы пропускаются.
        Возвращает (файлов, строк данных, колонки).
        """
        prepared: List[Tuple[str, List[str], List[List[str]]]] = []
        columns: Optional[List[str]] = None

        for path in paths:
            header, rows = self._read_file(path)
            if not header and not rows:
                continue
            if not rows:
                continue
            if columns is None:
                columns = list(header)
            prepared.append((path, header, rows))

        if not prepared or not columns:
            raise RuntimeError('Все выбранные файлы пусты.')

        # Индекс колонки в результирующем файле
        idx = {c: i for i, c in enumerate(columns)}

        total_rows = 0
        files_count = 0

        with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(columns)

            for path, header, rows in prepared:
                # Индекс колонки в исходном файле -> её имя
                src = {i: name for i, name in enumerate(header)}

                for row in rows:
                    if not row:
                        continue
                    if all((x or '').strip() == '' for x in row):
                        continue
                    out = [''] * len(columns)
                    for i, val in enumerate(row):
                        name = src.get(i)
                        if name is None:
                            continue
                        j = idx.get(name)
                        if j is None:
                            continue
                        out[j] = val
                    writer.writerow(out)
                    total_rows += 1
                files_count += 1

        return files_count, total_rows, columns

    @staticmethod
    def _read_file(path: str
                   ) -> Tuple[List[str], List[List[str]]]:
        """Читает CSV-файл, возвращает (заголовки, строки)."""
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f, delimiter=';')
            try:
                header = next(reader)
            except StopIteration:
                return [], []
            rows = [r for r in reader]
        return header, rows

    def _cancel(self) -> None:
        self.result = None
        self._cleanup_and_close()

    def _cleanup_and_close(self) -> None:
        self._unbind_wheel_all()
        try:
            self.destroy()
        except Exception:
            pass


# =========================================================================
#  Главное окно
# =========================================================================

class MainWindow(tk.Tk):
    """Главное окно приложения.

    Собирает всё вместе: панель кнопок, строку поиска, панель
    фильтров, таблицу с данными и статусную строку.
    """

    def __init__(self):
        super().__init__()
        self.title('Анализ метаданных 1С')
        self.geometry('1450x900')
        self.minsize(900, 600)
        self.configure(bg=COLORS['bg'])

        # --- Состояние ---
        self.rows: List[MetadataRow] = []
        self.columns: List[str] = []
        self.filtered: List[MetadataRow] = []
        self.tree: Optional[ttk.Treeview] = None

        # Настройки и префиксы
        self.settings = SettingsStore()
        self.markers = MarkersStore(self.settings.get('data_dir'))

        # Состояние поиска
        self.search_mode_var = tk.StringVar(value='all')
        self.only_label_var = tk.StringVar(value='Все')
        self.search_columns: Dict[str, tk.BooleanVar] = {}
        self.column_checkboxes: List[ttk.Checkbutton] = []
        self._matcher = QueryMatcher(None)
        self.search_entry: Optional[tk.Entry] = None

        # Список виджетов, доступных только после загрузки
        self._loading_controls: List[tk.Widget] = []
        self._data_loaded = False
        self._help_window: Optional[HelpWindow] = None

        # Виджеты-контейнеры, которые нужно скрывать/показывать
        self._search_settings_outer: Optional[tk.Frame] = None
        self._table_outer: Optional[tk.Frame] = None

        self._setup_styles()
        self._build_ui()
        self._set_data_loaded(False)

    # ------------------------------------------------------------------
    #  Стили
    # ------------------------------------------------------------------

    def _setup_styles(self) -> None:
        """Настраивает ttk-стили для всех виджетов приложения."""
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        self._setup_scrollbars(style)
        self._setup_buttons(style)
        self._setup_radio_check(style)
        self._setup_progressbar(style)
        self._setup_treeview(style)
        self._setup_combobox(style)

    def _setup_scrollbars(self, style: ttk.Style) -> None:
        for orient in ('Vertical', 'Horizontal'):
            name = f'Cyan.{orient}.TScrollbar'
            style.configure(
                name, gripcount=0,
                background=COLORS['scroll_bg'],
                darkcolor=COLORS['scroll_hover'],
                lightcolor='#85c1e9',
                troughcolor=COLORS['scroll_trough'],
                bordercolor=COLORS['scroll_border'],
                arrowcolor=COLORS['scroll_arrow'],
                relief='flat',
            )
            style.map(name,
                      background=[('active', COLORS['scroll_hover']),
                                  ('pressed', COLORS['scroll_press'])])

    def _setup_buttons(self, style: ttk.Style) -> None:
        style.configure(
            'Accent.TButton', font=FONTS['button'], foreground='white',
            background=COLORS['accent'], borderwidth=0, focusthickness=0,
            padding=(14, 7), relief='flat',
        )
        style.map(
            'Accent.TButton',
            background=[('active', COLORS['accent_hover']),
                        ('pressed', COLORS['accent_dark']),
                        ('disabled', '#a9c4e5')],
            foreground=[('disabled', '#eef3f8')],
        )

        style.configure(
            'Secondary.TButton', font=FONTS['button'],
            foreground=COLORS['text'], background='#e8eaee',
            borderwidth=0, focusthickness=0,
            padding=(14, 7), relief='flat',
        )
        style.map(
            'Secondary.TButton',
            background=[('active', '#d5d8dd'),
                        ('pressed', '#c2c6cc'),
                        ('disabled', '#f1f3f5')],
            foreground=[('disabled', '#a6adb8')],
        )

        style.configure(
            'Small.TButton', font=FONTS['button'],
            foreground=COLORS['text'], background='#e8eaee',
            borderwidth=0, focusthickness=0,
            padding=(10, 4), relief='flat',
        )
        style.map(
            'Small.TButton',
            background=[('active', '#d5d8dd'), ('disabled', '#f1f3f5')],
            foreground=[('disabled', '#a6adb8')],
        )

    def _setup_radio_check(self, style: ttk.Style) -> None:
        """Стандартные радиокнопки и чекбоксы на панели карточки.

        indicatorcolor не задаём - в теме clam это ломает вид.
        """
        style.configure('Card.TRadiobutton',
                        font=FONTS['body'],
                        background=COLORS['panel'],
                        foreground=COLORS['text'],
                        focuscolor=COLORS['panel'], padding=2)
        style.map('Card.TRadiobutton',
                  background=[('active', COLORS['panel']),
                              ('selected', COLORS['panel'])],
                  foreground=[('disabled', COLORS['text_muted'])])

        style.configure('Card.TCheckbutton',
                        font=FONTS['body'],
                        background=COLORS['panel'],
                        foreground=COLORS['text'],
                        focuscolor=COLORS['panel'], padding=2)
        style.map('Card.TCheckbutton',
                  background=[('active', COLORS['panel']),
                              ('selected', COLORS['panel'])],
                  foreground=[('disabled', COLORS['text_muted'])])

    def _setup_progressbar(self, style: ttk.Style) -> None:
        style.configure('Custom.Horizontal.TProgressbar',
                        troughcolor=COLORS['border'],
                        background=COLORS['accent'],
                        bordercolor=COLORS['border'],
                        lightcolor=COLORS['accent'],
                        darkcolor=COLORS['accent'],
                        thickness=8)

    def _setup_treeview(self, style: ttk.Style) -> None:
        style.configure('Custom.Treeview',
                        font=FONTS['body'], rowheight=26,
                        background=COLORS['panel'],
                        fieldbackground=COLORS['panel'],
                        foreground=COLORS['text'], borderwidth=0)
        style.map('Custom.Treeview',
                  background=[('selected', COLORS['accent'])],
                  foreground=[('selected', 'white')])
        style.configure('Custom.Treeview.Heading',
                        font=FONTS['h2'], background='#eef1f5',
                        foreground=COLORS['text'], relief='flat',
                        padding=(8, 6))
        style.map('Custom.Treeview.Heading',
                  background=[('active', '#dde3ea')])

    def _setup_combobox(self, style: ttk.Style) -> None:
        style.configure('Card.TCombobox',
                        foreground=COLORS['text'],
                        fieldbackground=COLORS['panel'],
                        background=COLORS['panel'],
                        arrowcolor=COLORS['accent'],
                        bordercolor=COLORS['border'],
                        lightcolor=COLORS['border'],
                        darkcolor=COLORS['border'], padding=4)
        style.map('Card.TCombobox',
                  fieldbackground=[('readonly', COLORS['panel']),
                                   ('disabled', COLORS['panel_alt'])],
                  foreground=[('disabled', COLORS['text_muted'])],
                  selectbackground=[('readonly', COLORS['panel'])],
                  selectforeground=[('readonly', COLORS['text'])],
                  arrowcolor=[('disabled', COLORS['text_muted'])])

        self.option_add('*TCombobox*Listbox.font', FONTS['body'])
        self.option_add('*TCombobox*Listbox.background', COLORS['panel'])
        self.option_add('*TCombobox*Listbox.foreground', COLORS['text'])
        self.option_add('*TCombobox*Listbox.selectBackground',
                        COLORS['accent'])
        self.option_add('*TCombobox*Listbox.selectForeground', 'white')

    # ------------------------------------------------------------------
    #  Сборка интерфейса
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Собирает главное окно по частям."""
        self._build_top_panel()
        self._build_search_hint()
        self._build_search_settings_panel()
        self._build_table_frame()
        self._build_status_bar()

    # --- верхняя панель ---

    def _build_top_panel(self) -> None:
        """Верхняя панель: кнопки, поиск, прогресс."""
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(12, 6))
        self._top_panel_outer = outer

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)
        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=12)

        self._build_action_buttons(inner)
        self._build_search_block(inner)
        self._build_progress(outer)

    def _build_action_buttons(self, parent: tk.Frame) -> None:
        self.btn_open = ttk.Button(parent, text='Открыть XML',
                                   style='Accent.TButton',
                                   command=self.open_file)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_export = ttk.Button(parent, text='Экспорт в CSV',
                                     style='Secondary.TButton',
                                     command=self.export_csv)
        self.btn_export.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_merge = ttk.Button(parent, text='Объединить CSV',
                                    style='Secondary.TButton',
                                    command=self.open_merge_dialog)
        self.btn_merge.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_markers = ttk.Button(parent, text='Префиксы',
                                      style='Secondary.TButton',
                                      command=self.open_markers_dialog)
        self.btn_markers.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_settings = ttk.Button(parent, text='Настройки',
                                       style='Secondary.TButton',
                                       command=self.open_settings_dialog)
        self.btn_settings.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_help = ttk.Button(
            parent, text='Инструкция', style='Secondary.TButton',
            command=lambda: self.open_user_help(anchor='start'))
        self.btn_help.pack(side=tk.RIGHT)

    def _build_search_block(self, parent: tk.Frame) -> None:
        """Поле поиска + кнопка очистки."""
        block = tk.Frame(parent, bg=COLORS['panel'])
        block.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(24, 24))

        self.lbl_search = tk.Label(block, text='Поиск:',
                                   font=FONTS['body'], fg=COLORS['text'],
                                   bg=COLORS['panel'])
        self.lbl_search.pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            'write',
            lambda *_: (self.apply_filter(), self._update_search_hint()))

        entry_wrap = tk.Frame(block, bg=COLORS['border'])
        entry_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.search_entry = tk.Entry(
            entry_wrap, textvariable=self.search_var,
            font=FONTS['body'], bd=0, relief='flat',
            bg=COLORS['panel'], fg=COLORS['text'],
            insertbackground=COLORS['accent'], width=30,
            disabledbackground=COLORS['panel_alt'],
            disabledforeground=COLORS['text_muted'])
        self.search_entry.pack(padx=1, pady=1, ipady=5, fill=tk.X,
                               expand=True)

        self._bind_search_context_menu()
        self._bind_search_shortcuts()

        self.btn_clear_search = ttk.Button(
            block, text='Очистить поиск', style='Secondary.TButton',
            command=self._clear_search)
        self.btn_clear_search.pack(side=tk.LEFT, padx=(8, 0))

        self._loading_controls.extend([
            self.btn_export, self.btn_markers,
            self.search_entry, self.btn_clear_search,
        ])

    def _bind_search_context_menu(self) -> None:
        """Правый клик по полю поиска -> меню Копировать/Вставить."""
        self._search_menu = tk.Menu(self.search_entry, tearoff=0)
        self._search_menu.add_command(label='Вставить',
                                      command=self._paste_to_search)
        self._search_menu.add_command(label='Копировать',
                                      command=self._copy_from_search)
        self._search_menu.add_command(label='Вырезать',
                                      command=self._cut_from_search)
        self._search_menu.add_separator()
        self._search_menu.add_command(label='Очистить',
                                      command=self._clear_search)

        def _popup(event):
            try:
                self._search_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._search_menu.grab_release()

        self.search_entry.bind('<Button-3>', _popup)

    def _bind_search_shortcuts(self) -> None:
        """Ctrl+V / Ctrl+C / Ctrl+X / Ctrl+A в поле поиска."""
        for seq in ('<Control-v>', '<Control-V>'):
            self.search_entry.bind(seq, lambda e: self._paste_to_search())
        for seq in ('<Control-c>', '<Control-C>'):
            self.search_entry.bind(seq, lambda e: self._copy_from_search())
        for seq in ('<Control-x>', '<Control-X>'):
            self.search_entry.bind(seq, lambda e: self._cut_from_search())
        for seq in ('<Control-a>', '<Control-A>'):
            self.search_entry.bind(seq, lambda e: self._select_all_search())

    def _build_progress(self, parent: tk.Frame) -> None:
        prog_wrap = tk.Frame(parent, bg=COLORS['bg'])
        prog_wrap.pack(fill=tk.X, pady=(8, 0))

        self.progress = ttk.Progressbar(
            prog_wrap, mode='determinate', maximum=100,
            style='Custom.Horizontal.TProgressbar')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_var = tk.StringVar(value='')
        tk.Label(prog_wrap, textvariable=self.progress_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg'], width=24, anchor='e'
                 ).pack(side=tk.LEFT, padx=(8, 0))

    # --- панель полей поиска ---

    def _build_search_settings_panel(self) -> None:
        """Панель «Поля поиска» + фильтр по признаку.

        Панель изначально скрыта и появляется только после загрузки XML.
        """
        outer = tk.Frame(self, bg=COLORS['bg'])
        self._search_settings_outer = outer
        outer.pack_forget()  # скрыто до загрузки

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)
        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(inner, text='Поля поиска', font=FONTS['h2'],
                 fg=COLORS['text'], bg=COLORS['panel']).pack(anchor='w')

        self._build_search_mode_row(inner)
        self._build_columns_frame(inner)
        self._build_only_combo_row(inner)

    def _build_search_mode_row(self, parent: tk.Frame) -> None:
        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(8, 0))

        self.rb_all_fields = ttk.Radiobutton(
            row, text='По всем полям',
            variable=self.search_mode_var, value='all',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change)
        self.rb_all_fields.pack(side=tk.LEFT, padx=(0, 16))

        self.rb_selected_fields = ttk.Radiobutton(
            row, text='Только по выбранным',
            variable=self.search_mode_var, value='selected',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change)
        self.rb_selected_fields.pack(side=tk.LEFT)

        self.btn_uncheck_all = ttk.Button(
            row, text='Снять все', style='Small.TButton',
            command=lambda: self._set_all_columns(False))
        self.btn_uncheck_all.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_check_all = ttk.Button(
            row, text='Отметить все', style='Small.TButton',
            command=lambda: self._set_all_columns(True))
        self.btn_check_all.pack(side=tk.RIGHT)

    def _build_columns_frame(self, parent: tk.Frame) -> None:
        self.columns_frame = tk.Frame(parent, bg=COLORS['panel'])
        self.columns_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Frame(parent, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(12, 0))

    def _build_only_combo_row(self, parent: tk.Frame) -> None:
        row = tk.Frame(parent, bg=COLORS['panel'])
        row.pack(fill=tk.X, pady=(10, 0))

        self.lbl_obj = tk.Label(row, text='Признак объекта:',
                                font=FONTS['h2'], fg=COLORS['text'],
                                bg=COLORS['panel'])
        self.lbl_obj.pack(side=tk.LEFT, padx=(0, 10))

        self.only_combo = ttk.Combobox(
            row, textvariable=self.only_label_var,
            values=list(ONLY_LABELS.keys()),
            state='readonly', width=24,
            font=FONTS['body'], style='Card.TCombobox')
        self.only_combo.pack(side=tk.LEFT)
        self.only_combo.bind('<<ComboboxSelected>>',
                             lambda *_: self.apply_filter())

        self._loading_controls.extend([
            self.rb_all_fields, self.rb_selected_fields,
            self.btn_check_all, self.btn_uncheck_all, self.only_combo,
        ])

    # --- подсказка о поиске ---

    def _build_search_hint(self) -> None:
        """Жёлтая полоса-подсказка, появляется при вводе в поиск."""
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 6),
                   after=self._top_panel_outer)
        self._search_hint_outer = outer
        outer.pack_forget()

        bar = tk.Frame(outer, bg=COLORS['warn_bg'],
                       highlightthickness=1,
                       highlightbackground='#f0d998')
        bar.pack(fill=tk.X)

        inner = tk.Frame(bar, bg=COLORS['warn_bg'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(inner, text='Как искать:', font=FONTS['hint'],
                 fg='#b8860b', bg=COLORS['warn_bg']
                 ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            inner,
            text=('Пишите слово как обычно - оно найдется везде, где есть.   '
                  'Если нужно точнее, добавьте знаки:   '
                  '^ в начале - "начинается с",   '
                  '$ в конце - "заканчивается на",   '
                  '? вместо одной буквы,   '
                  '* вместо нескольких.'),
            font=FONTS['body'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'], justify=tk.LEFT, anchor='w'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _update_search_hint(self) -> None:
        if self.search_var.get().strip():
            self._search_hint_outer.pack(fill=tk.X, padx=12, pady=(0, 6),
                                         after=self._top_panel_outer)
        else:
            self._search_hint_outer.pack_forget()

    # --- таблица и статусбар ---

    def _build_table_frame(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
        self._table_outer = outer

        panel = CardFrame(outer)
        panel.pack(fill=tk.BOTH, expand=True)

        self.table_frame = tk.Frame(panel, bg=COLORS['panel'])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_status_bar(self) -> None:
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 10))

        panel = CardFrame(outer)
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=6)

        self.status_var = tk.StringVar(value='Готов. Откройте XML.')
        tk.Label(inner, textvariable=self.status_var,
                 font=FONTS['body'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], anchor='w', justify=tk.LEFT
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # ------------------------------------------------------------------
    #  Состояние «загружено / не загружено»
    # ------------------------------------------------------------------

    def _set_data_loaded(self, loaded: bool) -> None:
        """Включает/выключает элементы, зависящие от данных."""
        self._data_loaded = loaded

        # Кнопки и поля поиска
        for w in self._loading_controls:
            try:
                w.state(['!disabled'] if loaded else ['disabled'])
            except Exception:
                try:
                    w.configure(state='normal' if loaded else 'disabled')
                except Exception:
                    pass

        # Подписи полей - «тускнеют», если данных нет
        for lbl in (self.lbl_search, self.lbl_obj):
            try:
                lbl.configure(fg=COLORS['text'] if loaded
                              else COLORS['text_muted'])
            except Exception:
                pass

        # Панель «Поля поиска» скрыта до загрузки
        if loaded:
            self._search_settings_outer.pack(
                fill=tk.X, padx=12, pady=(0, 6), before=self._table_outer)
        else:
            self._search_settings_outer.pack_forget()

        # Чекбоксы колонок - обновляем состояние
        self._update_checkboxes_state()

    # ------------------------------------------------------------------
    #  Чекбоксы колонок
    # ------------------------------------------------------------------

    def _rebuild_column_checkboxes(self) -> None:
        """Пересобирает чекбоксы колонок под текущий набор колонок."""
        for w in self.columns_frame.winfo_children():
            w.destroy()
        self.search_columns.clear()
        self.column_checkboxes.clear()

        for col in self.columns:
            var = tk.BooleanVar(value=True)
            self.search_columns[col] = var

            cb = ttk.Checkbutton(self.columns_frame, text=col,
                                 variable=var,
                                 style='Card.TCheckbutton',
                                 command=self.apply_filter)
            cb.pack(side=tk.LEFT, padx=(0, 12), pady=2)
            self.column_checkboxes.append(cb)

        self._update_checkboxes_state()

    def _update_checkboxes_state(self) -> None:
        """Включает чекбоксы только в режиме «Только по выбранным»."""
        enabled = self._data_loaded and self.search_mode_var.get() == 'selected'

        for cb in self.column_checkboxes:
            cb.state(['!disabled'] if enabled else ['disabled'])

        for btn in (getattr(self, 'btn_check_all', None),
                    getattr(self, 'btn_uncheck_all', None)):
            if btn is not None:
                btn.state(['!disabled'] if enabled else ['disabled'])

    def _set_all_columns(self, value: bool) -> None:
        """Ставит/снимает галочки на всех чекбоксах колонок."""
        if not self._data_loaded:
            return
        if self.search_mode_var.get() != 'selected':
            return
        for var in self.search_columns.values():
            var.set(value)
        self.apply_filter()

    def _on_search_mode_change(self) -> None:
        self._update_checkboxes_state()
        self.apply_filter()

    def _active_search_columns(self) -> List[str]:
        """Возвращает список колонок, по которым реально идёт поиск."""
        if self.search_mode_var.get() == 'all':
            return self.columns
        return [c for c, var in self.search_columns.items() if var.get()]

    # ------------------------------------------------------------------
    #  Инструкция
    # ------------------------------------------------------------------

    def open_user_help(self, anchor: str = 'start') -> None:
        """Открывает окно инструкции (единственный экземпляр)."""
        if self._help_window is not None:
            try:
                if self._help_window.winfo_exists():
                    self._help_window.deiconify()
                    self._help_window.lift()
                    self._help_window.focus_force()
                    return
            except tk.TclError:
                pass
        self._help_window = HelpWindow(self, anchor=anchor)

    # ------------------------------------------------------------------
    #  Работа с буфером обмена в поле поиска
    # ------------------------------------------------------------------

    def _paste_to_search(self) -> None:
        try:
            text = self.clipboard_get()
        except tk.TclError:
            return
        if not self.search_entry or not self._data_loaded:
            return
        try:
            self.search_entry.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.search_entry.insert('insert', text)
        self.search_entry.focus_set()

    def _copy_from_search(self) -> None:
        if not self.search_entry:
            return
        try:
            text = self.search_entry.selection_get()
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _cut_from_search(self) -> None:
        if not self.search_entry:
            return
        try:
            text = self.search_entry.selection_get()
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        try:
            self.search_entry.delete('sel.first', 'sel.last')
        except tk.TclError:
            pass
        self.update()

    def _select_all_search(self) -> str:
        if self.search_entry:
            self.search_entry.select_range(0, tk.END)
            self.search_entry.icursor(tk.END)
        return 'break'

    def _clear_search(self) -> None:
        self.search_var.set('')
        if self.search_entry and self._data_loaded:
            self.search_entry.focus_set()

    # ------------------------------------------------------------------
    #  Загрузка XML
    # ------------------------------------------------------------------

    def open_file(self) -> None:
        """Открывает диалог выбора файла и запускает парсер в потоке."""
        initial_dir = self.settings.get('xml_dir') or None
        if initial_dir and not os.path.isdir(initial_dir):
            initial_dir = None

        path = filedialog.askopenfilename(
            title='Выберите ConfigDumpInfo.xml',
            filetypes=[('XML files', '*.xml'), ('All files', '*.*')],
            initialdir=initial_dir)
        if not path:
            return

        # Сохраняем папку открытого файла в настройках
        self.settings.set('xml_dir', os.path.dirname(os.path.abspath(path)))
        try:
            self.settings.save()
        except Exception:
            pass

        self.progress['value'] = 0
        self.progress_var.set('0%')
        self.status_var.set(f'Файл: {os.path.basename(path)}')

        # Парсинг в отдельном потоке, чтобы GUI не подвисал
        threading.Thread(target=self._worker_parse,
                         args=(path,), daemon=True).start()

    def _worker_parse(self, path: str) -> None:
        """Тело фонового потока: подсчёт + парсинг."""
        try:
            parser = XmlParser(
                path,
                on_count=self._on_count,
                on_progress=self._on_parse_progress,
            )
            rows, cols = parser.run(self.markers)

            # Возвращаемся в главный поток
            self.after(0, lambda: self._after_load(rows, cols))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror('Ошибка', str(e)))
            self.after(0, self._reset_progress)

    # --- колбэки прогресса (в фоновом потоке) ---

    def _on_count(self, n: int) -> None:
        self.after(0, lambda: self._update_progress(
            '', f'Подсчёт: {self._fmt(n)}'))

    def _on_parse_progress(self, done: int, total: int) -> None:
        pct = int(done * 100 / total) if total else 100
        text = f'{pct}%  ({self._fmt(done)} из {self._fmt(total)})'
        self.after(0, lambda: self._update_progress(pct, text))

    # --- обновление прогресса (в главном потоке) ---

    def _update_progress(self, pct, label: str) -> None:
        if pct != '':
            self.progress['value'] = pct
        self.progress_var.set(label)

    def _reset_progress(self) -> None:
        self.progress.configure(value=0)
        self.progress_var.set('')

    @staticmethod
    def _fmt(n: int) -> str:
        return f'{n:,}'.replace(',', ' ')

    # --- после загрузки ---

    def _after_load(self, rows: List[MetadataRow],
                    cols: List[str]) -> None:
        """Обновляет интерфейс после успешного парсинга."""
        self.rows = rows
        self.columns = cols

        self.progress['value'] = 100
        self.progress_var.set('100%')

        self._rebuild_table()
        self._rebuild_column_checkboxes()
        self._set_data_loaded(True)

        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Загружено {self._fmt(len(self.rows))} записей, '
            f'колонок: {len(self.columns)}, '
            f'кастомных: {self._fmt(n_custom)}')

        self.apply_filter()

    # ------------------------------------------------------------------
    #  Таблица
    # ------------------------------------------------------------------

    def _rebuild_table(self) -> None:
        """Пересобирает Treeview под текущий набор колонок."""
        for w in self.table_frame.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns,
            show='headings', selectmode='browse',
            style='Custom.Treeview')

        for c in self.columns:
            self.tree.heading(c, text=c,
                              command=lambda col=c: self.sort_by(col))
            self.tree.column(c, width=150, anchor='w',
                             minwidth=40, stretch=False)

        # Стартовые ширины для базовых колонок
        for col, w in (('ТипОбъекта', 140), ('ИмяОбъекта', 200),
                       ('ВидЭлемента', 150), ('ИмяЭлемента', 220),
                       ('ВидВложенногоЭлемента', 190),
                       ('ИмяВложенногоЭлемента', 200),
                       ('ПутьЭлемента', 400), ('ПризнакОбъекта', 130),
                       ('name', 400)):
            if col in self.columns:
                self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(self.table_frame, orient='vertical',
                            command=self.tree.yview,
                            style='Cyan.Vertical.TScrollbar')
        hsb = ttk.Scrollbar(self.table_frame, orient='horizontal',
                            command=self.tree.xview,
                            style='Cyan.Horizontal.TScrollbar')

        self.tree.configure(yscrollcommand=vsb.set,
                            xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.table_frame.rowconfigure(0, weight=1)
        self.table_frame.columnconfigure(0, weight=1)

        # Чередование цветов + жёлтая подсветка найденного
        self.tree.tag_configure('odd', background=COLORS['panel'])
        self.tree.tag_configure('even', background=COLORS['panel_alt'])
        self.tree.tag_configure('match', background=COLORS['highlight'])

        self.tree.bind('<Double-Button-1>', self._on_double_click_header)

    def _on_double_click_header(self, event) -> None:
        """Двойной клик по границе заголовка - автоподбор ширины."""
        region = self.tree.identify_region(event.x, event.y)
        if region != 'separator':
            return

        col_id = self.tree.identify_column(event.x)
        if not col_id:
            return
        try:
            col_index = int(col_id[1:]) - 1
        except ValueError:
            return
        if col_index < 0 or col_index >= len(self.columns):
            return

        col_name = self.columns[col_index]
        max_len = len(col_name)
        for r in self.filtered[:2000]:
            v = str(r.get(col_name, ''))
            if len(v) > max_len:
                max_len = len(v)
        self.tree.column(col_name, width=max(60, min(700, max_len * 8)))

    # ------------------------------------------------------------------
    #  Фильтрация и рендеринг
    # ------------------------------------------------------------------

    def apply_filter(self) -> None:
        """Применяет поиск и фильтр по признаку, обновляет таблицу."""
        if not self._data_loaded:
            return

        pattern = self.search_var.get().strip()
        cols = self._active_search_columns()

        self._matcher = QueryMatcher(QueryCompiler.compile(pattern))
        only = ONLY_LABELS.get(self.only_label_var.get(), 'all')

        # Если выбран режим «только по выбранным» и ни одна колонка
        # не отмечена - показываем подсказку и пустую таблицу
        if (pattern and self.search_mode_var.get() == 'selected'
                and not cols):
            self.filtered = []
            self.status_var.set(
                'Режим "Только по выбранным", но ни одна колонка '
                'не отмечена. Поставьте галочки в панели "Поля поиска".')
            self.render_table()
            return

        if not pattern:
            self.filtered = [r for r in self.rows
                             if self._obj_matches(r, only)]
        else:
            self.filtered = [r for r in self.rows
                             if self._obj_matches(r, only)
                             and self._row_matches(r, cols)]

        self.render_table()

    @staticmethod
    def _obj_matches(row: MetadataRow, only: str) -> bool:
        if only == 'custom':
            return row.get('ПризнакОбъекта') == CUSTOM_TAG
        if only == 'std':
            return row.get('ПризнакОбъекта') == STD_TAG
        return True

    def _row_matches(self, row: MetadataRow, cols: Sequence[str]) -> bool:
        return any(self._matcher.matches(row.get(c, '')) for c in cols)

    def _is_match(self, row: MetadataRow) -> bool:
        """Совпадает ли строка с текущим поиском (для подсветки)."""
        if self._matcher.regex is None:
            return False
        return self._row_matches(row, self._active_search_columns())

    def render_table(self) -> None:
        if not self.tree:
            return

        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.filtered):
            is_match = self._is_match(r)
            tags = ['match'] if is_match else ['odd' if i % 2 else 'even']
            self.tree.insert(
                '', tk.END,
                values=tuple(str(r.get(c, '')) for c in self.columns),
                tags=tuple(tags))

        self.status_var.set(
            f'Показано {self._fmt(len(self.filtered))} '
            f'(всего: {self._fmt(len(self.rows))})')

    def sort_by(self, col: str) -> None:
        self.filtered.sort(key=lambda r: str(r.get(col, '')).lower())
        self.render_table()

    # ------------------------------------------------------------------
    #  Префиксы
    # ------------------------------------------------------------------

    def open_markers_dialog(self) -> None:
        dlg = MarkersDialog(self, self.markers.items,
                            self.settings.get('data_dir'),
                            on_change_dir=self._change_data_dir)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        # Смена папки данных (если пользователь её поменял)
        self.settings.set('data_dir', dlg.result['data_dir'])
        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Сохранение',
                                 f'Не удалось сохранить settings.json:\n{e}')

        # Обновляем список префиксов и сохраняем файл
        self.markers.set_items(dlg.result['markers'])
        try:
            self.markers.save()
        except Exception as e:
            messagebox.showerror(
                'Сохранение',
                f'Не удалось сохранить список префиксов:\n{e}')

        self._recompute_markers()
        self.apply_filter()

        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Префиксов: {len(self.markers.items)}. '
            f'Кастомных строк: {n_custom}')

    def _change_data_dir(self, new_dir: str) -> bool:
        """Меняет папку данных, перенося туда файл префиксов."""
        new_dir = os.path.abspath(new_dir)
        try:
            os.makedirs(new_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось создать папку:\n{e}')
            return False

        try:
            self.markers.save(target_dir=new_dir)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось записать префиксы:\n{e}')
            return False

        self.settings.set('data_dir', new_dir)
        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return False

        self.markers.reload(new_dir)
        return True

    def _recompute_markers(self) -> None:
        """Пересчитывает ПризнакОбъекта у всех строк."""
        for r in self.rows:
            name = r.get('ИмяОбъекта', '')
            r.set('ПризнакОбъекта',
                  CUSTOM_TAG if self.markers.is_custom_name(name)
                  else STD_TAG)

    # ------------------------------------------------------------------
    #  Настройки
    # ------------------------------------------------------------------

    def open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self, self.settings.as_dict())
        self.wait_window(dlg)
        if dlg.result is None:
            return

        old_data_dir = self.settings.get('data_dir')
        new = dlg.result

        # Проверка и создание папки настроек
        new_settings_dir = new.get('settings_dir', '')
        if (new_settings_dir
                and new_settings_dir != self.settings.get('settings_dir')):
            try:
                os.makedirs(new_settings_dir, exist_ok=True)
            except OSError as e:
                messagebox.showerror(
                    'Настройки',
                    f'Не удалось создать папку настроек:\n{e}')
                return

        self.settings.update({
            'settings_dir': new_settings_dir,
            'data_dir': new.get('data_dir') or new_settings_dir,
            'xml_dir': new.get('xml_dir', ''),
            'export_dir': new.get('export_dir', ''),
        })

        # Если папка данных изменилась - переносим туда файл префиксов
        if old_data_dir != self.settings.get('data_dir'):
            try:
                os.makedirs(self.settings.get('data_dir'), exist_ok=True)
                self.markers.save(target_dir=self.settings.get('data_dir'))
            except Exception as e:
                messagebox.showerror(
                    'Настройки',
                    f'Не удалось перенести префиксы в новую папку:\n{e}')

        try:
            self.settings.save()
        except Exception as e:
            messagebox.showerror('Настройки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return

        self.markers.reload(self.settings.get('data_dir'))
        self._recompute_markers()
        self.apply_filter()
        self.status_var.set(
            f'Настройки сохранены. Папка данных: '
            f'{self.settings.get("data_dir")}')

    # ------------------------------------------------------------------
    #  Объединение CSV
    # ------------------------------------------------------------------

    def open_merge_dialog(self) -> None:
        initial = self.settings.get('export_dir') or ''
        if initial and not os.path.isdir(initial):
            initial = ''

        dlg = MergeCsvDialog(self, initial_dir=initial)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        r = dlg.result
        messagebox.showinfo(
            'Объединение',
            f'Готово.\n'
            f'Файл: {r["path"]}\n'
            f'Файлов объединено: {r["files"]}\n'
            f'Строк данных: {self._fmt(r["rows"])}\n'
            f'Колонок: {len(r["columns"])}',
            parent=self)

        self.settings.set('export_dir', os.path.dirname(r['path']))
        try:
            self.settings.save()
        except Exception:
            pass

    # ------------------------------------------------------------------
    #  Экспорт в CSV
    # ------------------------------------------------------------------

    def export_csv(self) -> None:
        if not self.rows:
            messagebox.showwarning('Экспорт', 'Сначала загрузите XML.')
            return

        pattern = self.search_var.get().strip()
        has_query = bool(pattern)

        matches = ([r for r in self.filtered if self._is_match(r)]
                   if has_query else [])

        dlg = ExportDialog(self, has_query, len(self.rows), len(matches))
        self.wait_window(dlg)
        if not dlg.result:
            return

        mode = dlg.result
        if mode == 'all':
            data: List[MetadataRow] = self.rows
            name = 'export_all.csv'
        else:
            safe_q = re.sub(r'[^\w\u0400-\u04FF\-]', '_',
                            pattern) or 'result'
            data = matches
            name = f'export_{safe_q}.csv'

        if not data:
            messagebox.showinfo('Экспорт', 'Нет строк для выгрузки.')
            return

        initial_dir = self.settings.get('export_dir') or None
        if initial_dir and not os.path.isdir(initial_dir):
            initial_dir = None

        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv')],
            initialfile=name,
            initialdir=initial_dir)
        if not path:
            return

        self.settings.set('export_dir', os.path.dirname(os.path.abspath(path)))
        try:
            self.settings.save()
        except Exception:
            pass

        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=self.columns,
                               delimiter=';', extrasaction='ignore')
            w.writeheader()
            for r in data:
                w.writerow(r.data)

        messagebox.showinfo(
            'Экспорт',
            f'Сохранено: {path}\n'
            f'Записей: {self._fmt(len(data))}')


# =========================================================================
#  Точка входа
# =========================================================================

def main() -> None:
    MainWindow().mainloop()


if __name__ == '__main__':
    main()