"""
GUI-парсер ConfigDumpInfo.xml (метаданные 1С).

Возможности:
- открытие XML через диалог;
- потоковый парсинг больших файлов с прогрессом;
- динамические колонки: 8 базовых (русских) + все атрибуты XML;
- русские значения ТипОбъекта, ВидЭлемента, ВидВложенногоЭлемента;
- колонка ПутьЭлемента в терминах 1С;
- колонка ПризнакОбъекта: Кастомный / Стандартный по списку префиксов;
- список префиксов хранится в config_markers.json рядом с настройками
  и редактируется через кнопку "Префиксы";
- фильтр по признаку объекта выпадающим списком;
- поиск по всем полям или только по выбранным чекбоксами;
- шаблоны поиска: ^ (начало), $ (конец), ? (один символ), * (любое число);
- подсветка найденного жёлтым, зебра строк;
- колонки растягиваются мышью, не сжимая соседей;
- двойной клик по границе заголовка - автоподгон ширины;
- экспорт в CSV: всё / только подсвеченные;
- объединение нескольких CSV-файлов в один с выбором папки,
  списка файлов и имени итогового файла;
- короткая инструкция пользователя;
- вставка из буфера по Ctrl+V, правым кликом по полю поиска;
- кнопка "Очистить поиск" рядом с полем поиска;
- статусная строка вынесена вниз окна отдельной полосой;
- панель настроек поиска и фильтр по признаку объекта скрыты
  до загрузки XML и появляются только после успешного парсинга;
- зависимые от данных элементы выключены до загрузки XML;
- настройки программы (папка данных, папка XML по умолчанию,
  папка экспорта по умолчанию) хранятся в settings.json;
- по умолчанию - %APPDATA%\\ConfigDumpParser, с возможностью
  сменить путь вручную через окно "Настройки";
- поддержка портативного режима: settings.json рядом с программой;
- окно "Настройки" прокручивается и не ломается при малых размерах;
- окно "Объединение CSV" имеет прокрутку списка и не ломается
  при малых размерах;
- все чекбоксы, радиокнопки и выпадающие списки - стандартные
  ttk-виджеты, оформленные единообразно.

Только стандартная библиотека Python 3.8+.
"""
import os
import sys
import re
import csv
import json
import threading
import subprocess
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# --- Палитра и шрифты ---
COLORS = {
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

FONTS = {
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
BASE_COLUMNS = [
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

ONLY_LABELS = {
    'Все': 'all',
    'Только кастомные': 'custom',
    'Только стандартные': 'std',
}


# --- Определение путей (portable vs %APPDATA%) ---
def _program_dir():
    """Папка, где лежит .exe или .py."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def _appdata_dir():
    """%APPDATA%\\<APP_NAME> с гарантированным созданием."""
    base = os.environ.get('APPDATA') or os.path.expanduser('~')
    folder = os.path.join(base, APP_NAME)
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass
    return folder


def _default_settings_dir():
    """Куда по умолчанию класть settings.json и config_markers.json.

    Логика:
      - обычный .py            -> рядом со скриптом;
      - .exe и рядом есть      -> рядом с .exe (портативный режим);
        settings.json
      - .exe без settings.json -> %APPDATA%\\<APP_NAME>
    """
    prog = _program_dir()
    if not getattr(sys, 'frozen', False):
        return prog
    if os.path.exists(os.path.join(prog, SETTINGS_FILENAME)):
        return prog
    return _appdata_dir()


# --- Чтение / запись settings.json ---
def _settings_path(settings_dir=None):
    if settings_dir is None:
        settings_dir = _default_settings_dir()
    return os.path.join(settings_dir, SETTINGS_FILENAME)


def load_settings():
    default_dir = _default_settings_dir()
    settings = {
        'settings_dir': default_dir,
        'data_dir': default_dir,
        'xml_dir': '',
        'export_dir': '',
    }

    path = os.path.join(default_dir, SETTINGS_FILENAME)
    if not os.path.exists(path):
        return settings

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return settings
    except Exception:
        return settings

    sd = data.get('settings_dir') or default_dir
    sd = os.path.abspath(os.path.expanduser(str(sd)))
    settings['settings_dir'] = sd

    dd = data.get('data_dir') or sd
    dd = os.path.abspath(os.path.expanduser(str(dd)))
    settings['data_dir'] = dd

    settings['xml_dir'] = str(data.get('xml_dir') or '')
    settings['export_dir'] = str(data.get('export_dir') or '')
    return settings


def save_settings(settings):
    path = _settings_path(settings.get('settings_dir'))
    payload = {
        'settings_dir': settings.get('settings_dir', ''),
        'data_dir': settings.get('data_dir', ''),
        'xml_dir': settings.get('xml_dir', ''),
        'export_dir': settings.get('export_dir', ''),
    }
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# --- Префиксы ---
def markers_path(data_dir):
    return os.path.join(data_dir, MARKERS_FILENAME)


def load_markers(data_dir):
    path = markers_path(data_dir)
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


def save_markers(data_dir, markers):
    os.makedirs(data_dir, exist_ok=True)
    path = markers_path(data_dir)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'markers': list(markers)}, f,
                  ensure_ascii=False, indent=2)


def is_custom_name(name, markers):
    if not name:
        return False
    for m in markers:
        if m and name.startswith(m):
            return True
    return False


# --- Словари переводов ---
TYPE_TRANSLATIONS = {
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

KIND_TRANSLATIONS = {
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


# --- Парсинг ---
def detect_namespace(path):
    for _, elem in ET.iterparse(path, events=('start',)):
        t = elem.tag
        return t[1:t.index('}')] if t.startswith('{') else ''
    return ''


def count_metadata(path, ns_uri, progress_cb=None):
    tag = f'{{{ns_uri}}}Metadata' if ns_uri else 'Metadata'
    total = 0
    with open(path, 'rb') as fh:
        for _, elem in ET.iterparse(fh, events=('end',)):
            if elem.tag == tag:
                total += 1
                elem.clear()
                if progress_cb and total % 100_000 == 0:
                    progress_cb(total)
    return total


def split_name(name):
    p = name.split('.') if name else []
    p += [''] * (6 - len(p))

    type_ru = TYPE_TRANSLATIONS.get(p[0], p[0])
    kind1_ru = KIND_TRANSLATIONS.get(p[2], p[2])
    kind2_ru = KIND_TRANSLATIONS.get(p[4], p[4])

    path_parts = [
        type_ru, p[1],
        kind1_ru, p[3],
        kind2_ru, p[5],
    ]
    if len(p) > 6:
        path_parts.extend(p[6:])

    path = '.'.join(part for part in path_parts if part)

    return {
        'ТипОбъекта': type_ru,
        'ИмяОбъекта': p[1],
        'ВидЭлемента': kind1_ru,
        'ИмяЭлемента': p[3],
        'ВидВложенногоЭлемента': kind2_ru,
        'ИмяВложенногоЭлемента': p[5],
        'ПутьЭлемента': path,
        'ПризнакОбъекта': NONE_TAG,
    }


def parse_xml(path, ns_uri, total, progress_cb=None, markers=None):
    if markers is None:
        markers = []
    rows, extra = [], set()
    tag = f'{{{ns_uri}}}Metadata' if ns_uri else 'Metadata'

    with open(path, 'rb') as fh:
        done = 0
        for _, elem in ET.iterparse(fh, events=('end',)):
            if elem.tag != tag:
                continue
            row = split_name(elem.get('name', ''))
            row.update(elem.attrib)
            extra.update(elem.attrib)

            row['ПризнакОбъекта'] = (
                CUSTOM_TAG
                if is_custom_name(row.get('ИмяОбъекта', ''), markers)
                else STD_TAG
            )

            rows.append(row)
            elem.clear()
            done += 1
            if progress_cb and done % 500 == 0:
                progress_cb(done, total)

    if progress_cb:
        progress_cb(done, total)

    cols = BASE_COLUMNS + sorted(c for c in extra
                                 if c not in BASE_COLUMNS)
    return rows, cols


# --- Поиск ---
def compile_query(pattern):
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


def match_query(regex, value):
    if regex is None:
        return False
    return regex.search(str(value)) is not None


def open_folder(path):
    try:
        if os.name == 'nt':
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        pass


# --- Копируемая метка ---
class CopyableLabel(tk.Label):
    def __init__(self, parent, text, app=None, copy_value=None, **kwargs):
        super().__init__(parent, text=text, **kwargs)
        self._full_text = text
        self._copy_text = text if copy_value is None else copy_value
        self._has_copy_value = copy_value is not None
        self._app = app
        self.bind('<Button-3>', self._context_menu)
        self.bind('<Double-Button-1>', lambda *_: self._copy())
        self.configure(cursor='hand2')

    def _context_menu(self, event):
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

    def _copy(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._copy_text)
            self.update()
        except tk.TclError:
            pass

    def _copy_full(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._full_text)
            self.update()
        except tk.TclError:
            pass

    def _copy_and_paste(self):
        self._copy()
        try:
            self._app._paste_to_search()
        except Exception:
            pass


# --- Окно инструкции ---
class HelpWindow(tk.Toplevel):
    SECTIONS = [
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

    ANCHORS = {
        'start': 0,
        'open': 1,
        'columns': 2,
        'markers': 3,
        'search': 4,
    }

    def __init__(self, parent, anchor='start'):
        super().__init__(parent)
        self.title('Инструкция')
        self.geometry('1040x780')
        self.minsize(720, 480)
        self.transient(parent)
        self.configure(bg=COLORS['bg'])

        self._parent = parent
        self._canvas = None
        self._content = None
        self._content_window_id = None
        self._wheel_bound = False

        self._build_header()
        self._build_body()
        self._build_footer()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 1040) // 2
        y = parent.winfo_rooty() + 40
        self.geometry(f'1040x780+{max(0, x)}+{max(0, y)}')

        self.bind('<Escape>', lambda *_: self._close())
        self.protocol('WM_DELETE_WINDOW', self._close)

        self.after(50, lambda: self._scroll_to(anchor))

    def _build_header(self):
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

    def _build_body(self):
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

        self._content.bind(
            '<Configure>',
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox('all')))

        self._canvas.bind(
            '<Configure>',
            lambda e: self._canvas.itemconfigure(
                self._content_window_id, width=e.width))

        self._render_sections()

        self._canvas.bind_all('<MouseWheel>', self._on_wheel)
        self._wheel_bound = True

    def _render_sections(self):
        for idx, (title, blocks) in enumerate(self.SECTIONS):
            self._render_section(idx, title, blocks)

    def _render_section(self, idx, title, blocks):
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
            btype = block.get('type')

            if btype == 'text':
                tk.Label(
                    outer, text=block.get('text', ''),
                    font=FONTS['body'],
                    fg=COLORS['text'], bg=COLORS['bg'],
                    justify=tk.LEFT, anchor='w',
                    wraplength=940,
                ).pack(anchor='w', fill=tk.X, pady=(0, 6))

            elif btype == 'code':
                box = tk.Frame(outer, bg=COLORS['panel'],
                               highlightthickness=1,
                               highlightbackground=COLORS['border'])
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
                    row = tk.Frame(outer, bg=COLORS['bg'])
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
                    row = tk.Frame(outer, bg=COLORS['panel'],
                                   highlightthickness=1,
                                   highlightbackground=COLORS['border'])
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

            elif btype == 'kv':
                for key, val in block.get('items', []):
                    row = tk.Frame(outer, bg=COLORS['panel'],
                                   highlightthickness=1,
                                   highlightbackground=COLORS['border'])
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

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(fill=tk.X)

        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=24, pady=12)

        ttk.Button(ftr, text='Закрыть', style='Secondary.TButton',
                   command=self._close).pack(side=tk.RIGHT)

    def _scroll_to(self, anchor):
        idx = self.ANCHORS.get(anchor, 0)
        total = max(1, len(self.SECTIONS))
        frac = idx / total
        self._canvas.yview_moveto(frac)

    def _on_wheel(self, event):
        try:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                      'units')
        except Exception:
            pass

    def _close(self):
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


# --- Диалог экспорта ---
class ExportDialog(tk.Toplevel):
    def __init__(self, parent, has_query, n_all, n_matched):
        super().__init__(parent)
        self.title('Экспорт в CSV')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result = None
        self.mode = tk.StringVar(value='matched' if has_query else 'all')

        card = tk.Frame(self, bg=COLORS['panel'],
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=18)

        tk.Label(inner, text='Что выгружать в CSV?',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w', pady=(0, 12))

        def radio(text, value, enabled=True):
            rb = ttk.Radiobutton(
                inner, text=text, variable=self.mode, value=value,
                style='Card.TRadiobutton',
            )
            rb.pack(anchor='w', pady=3, fill=tk.X)
            if not enabled:
                rb.state(['disabled'])

        radio(f'Все строки ({n_all:,})'.replace(',', ' '), 'all')
        radio(f'Только подсвеченные ({n_matched:,})'.replace(',', ' '),
              'matched', enabled=has_query)

        btns = tk.Frame(inner, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(18, 0))

        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Экспорт', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 380) // 2
        y = parent.winfo_rooty() + 150
        self.geometry(f'380x260+{x}+{y}')

        self.bind('<Return>', lambda *_: self._ok())
        self.bind('<Escape>', lambda *_: self._cancel())
        self.focus_set()

    def _ok(self):
        self.result = self.mode.get()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# --- Диалог настроек ---
class SettingsDialog(tk.Toplevel):
    """Редактор путей: папка настроек, папка данных, папка XML,
    папка экспорта.

    Окно изменяемого размера. Прокрутка включается только тогда,
    когда содержимое реально не помещается в видимую область.
    Колесо мыши работает только внутри диалога.
    """

    BTN_WIDTH = 12

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title('Настройки')
        self.minsize(680, 460)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result = None
        self._settings = dict(settings)
        self.vars = {}

        self._canvas = None
        self._content = None
        self._content_win_id = None
        self._wheel_bound_widgets = []

        self._place_window(parent, 800, 620)
        self._build_ui()

        self.bind('<Configure>', self._on_configure)
        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

        self.after(50, self._refresh_scrollregion)

    def _place_window(self, parent, w, h):
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

    def _build_ui(self):
        self._build_footer()
        self._build_header()
        self._build_body()

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=18, pady=12)

        ttk.Button(ftr, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(ftr, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

    def _build_header(self):
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
            justify=tk.LEFT, anchor='w',
            wraplength=660,
        ).pack(anchor='w', fill=tk.X, pady=(4, 0))

        tk.Frame(self, height=1, bg=COLORS['border']).pack(
            side=tk.TOP, fill=tk.X)

    def _build_body(self):
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(body, highlightthickness=0,
                                 bg=COLORS['bg'])
        vsb = ttk.Scrollbar(body, orient='vertical',
                            command=self._canvas.yview,
                            style='Cyan.Vertical.TScrollbar')
        self._canvas.configure(yscrollcommand=vsb.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._vsb = vsb

        self._content = tk.Frame(self._canvas, bg=COLORS['bg'])
        self._content_win_id = self._canvas.create_window(
            (0, 0), window=self._content, anchor='nw')

        self._content.bind('<Configure>', self._on_content_configure)
        self._canvas.bind('<Configure>', self._on_canvas_configure)

        card = tk.Frame(self._content, bg=COLORS['panel'],
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        self._add_row(
            inner, 'settings_dir', 'Папка настроек',
            'Где хранятся settings.json и config_markers.json. '
            'По умолчанию - %APPDATA%\\' + APP_NAME + '.',
        )
        self._add_row(
            inner, 'data_dir', 'Папка данных',
            'Где хранится config_markers.json (список префиксов). '
            'Обычно совпадает с папкой настроек.',
        )
        self._add_row(
            inner, 'xml_dir', 'Папка XML по умолчанию',
            'Откуда открывается ConfigDumpInfo.xml. '
            'Можно оставить пустой - тогда программа запомнит '
            'последнюю выбранную папку.',
        )
        self._add_row(
            inner, 'export_dir', 'Папка экспорта по умолчанию',
            'Куда сохраняются CSV-файлы и откуда берутся файлы '
            'для объединения. Пусто - последняя выбранная папка.',
        )

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._content)

    def _add_row(self, parent, key, title, hint):
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
                   command=lambda k=key: self._open_typed(
                       self.vars[k].get())
                   ).pack(side=tk.RIGHT, padx=(6, 0))

        ttk.Button(row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=lambda k=key: self._pick_dir(k)
                   ).pack(side=tk.RIGHT)

        var = tk.StringVar(value=self._settings.get(key, ''))
        self.vars[key] = var
        entry = tk.Entry(row, textvariable=var, font=FONTS['body'],
                         bg=COLORS['panel'], fg=COLORS['text'],
                         insertbackground=COLORS['accent'])
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

    # --- прокрутка ---
    def _bind_wheel_recursive(self, widget):
        try:
            widget.bind('<MouseWheel>', self._on_wheel)
        except Exception:
            pass
        self._wheel_bound_widgets.append(widget)
        for child in widget.winfo_children():
            self._bind_wheel_recursive(child)

    def _on_wheel(self, event):
        try:
            first, last = self._canvas.yview()
            if first <= 0.0 and last >= 1.0:
                return 'break'
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                      'units')
        except Exception:
            pass
        return 'break'

    def _on_content_configure(self, _event=None):
        self._refresh_scrollregion()

    def _on_canvas_configure(self, event=None):
        if event is not None and self._content_win_id is not None:
            self._canvas.itemconfigure(self._content_win_id,
                                       width=event.width)
        self._refresh_scrollregion()

    def _on_configure(self, event=None):
        if event is not None and event.widget is self:
            self._refresh_scrollregion()

    def _refresh_scrollregion(self):
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
    def _open_typed(self, path):
        path = (path or '').strip()
        if path and os.path.isdir(path):
            open_folder(path)
        elif path:
            messagebox.showinfo('Открыть',
                                'Папка не найдена:\n' + path, parent=self)

    def _pick_dir(self, key):
        initial = self.vars[key].get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Выберите папку',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self.vars[key].set(os.path.abspath(chosen))

    def _ok(self):
        result = {}
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

    def _cancel(self):
        self.result = None
        self._cleanup_and_close()

    def _cleanup_and_close(self):
        for w in self._wheel_bound_widgets:
            try:
                w.unbind('<MouseWheel>')
            except Exception:
                pass
        self._wheel_bound_widgets.clear()
        try:
            self.destroy()
        except Exception:
            pass


# --- Диалог управления префиксами ---
class MarkersDialog(tk.Toplevel):
    """Редактор списка префиксов кастомных объектов."""

    def __init__(self, parent, markers, data_dir, on_change_dir=None):
        super().__init__(parent)
        self.title('Префиксы кастомных объектов')
        self.geometry('620x620')
        self.minsize(560, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result = None
        self._markers = list(markers)
        self._data_dir = data_dir
        self._on_change_dir = on_change_dir

        card = tk.Frame(self, bg=COLORS['panel'],
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        tk.Label(inner, text='Префиксы имён кастомных объектов',
                 font=FONTS['dialog'],
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        desc = tk.Label(
            inner,
            text=('Объект считается кастомным, если "ИмяОбъекта" '
                  'начинается с одного из префиксов.\n'
                  'Пример: ПЛ_, АБ_, Моё_.'),
            font=FONTS['body_sm'],
            fg=COLORS['text_muted'],
            bg=COLORS['panel'],
            justify=tk.LEFT,
            anchor='w',
            wraplength=560,
        )
        desc.pack(anchor='w', fill=tk.X, pady=(4, 8))

        path_box = tk.Frame(inner, bg=COLORS['panel_alt'],
                            highlightthickness=1,
                            highlightbackground=COLORS['border'])
        path_box.pack(fill=tk.X, pady=(0, 10))

        path_inner = tk.Frame(path_box, bg=COLORS['panel_alt'])
        path_inner.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(path_inner, text='Файл префиксов:',
                 font=FONTS['kv_key'], fg=COLORS['accent_dark'],
                 bg=COLORS['panel_alt'], anchor='w'
                 ).pack(anchor='w')

        self._path_var = tk.StringVar(value=markers_path(self._data_dir))
        self._path_label = tk.Label(
            path_inner, textvariable=self._path_var,
            font=FONTS['body_sm'], fg=COLORS['text'],
            bg=COLORS['panel_alt'], anchor='w', justify=tk.LEFT,
            wraplength=540,
        )
        self._path_label.pack(anchor='w', fill=tk.X, pady=(2, 6))

        path_btns = tk.Frame(path_inner, bg=COLORS['panel_alt'])
        path_btns.pack(fill=tk.X)

        ttk.Button(path_btns, text='Открыть папку',
                   style='Small.TButton',
                   command=self._open_folder
                   ).pack(side=tk.LEFT)
        ttk.Button(path_btns, text='Изменить путь...',
                   style='Small.TButton',
                   command=self._change_dir
                   ).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(path_btns, text='Копировать путь',
                   style='Small.TButton',
                   command=self._copy_path
                   ).pack(side=tk.LEFT, padx=(6, 0))

        add_row = tk.Frame(inner, bg=COLORS['panel'])
        add_row.pack(fill=tk.X, pady=(0, 8))

        self.entry = tk.Entry(add_row, font=FONTS['body'],
                              bg=COLORS['panel'], fg=COLORS['text'],
                              insertbackground=COLORS['accent'])
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind('<Return>', lambda *_: self._add())

        ttk.Button(add_row, text='Добавить', style='Small.TButton',
                   command=self._add).pack(side=tk.LEFT, padx=(8, 0))

        list_wrap = tk.Frame(inner, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(
            list_wrap, font=FONTS['mono'],
            bg=COLORS['panel'], fg=COLORS['text'],
            selectbackground=COLORS['accent'],
            selectforeground='white',
            activestyle='none', bd=0, highlightthickness=0,
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                          padx=1, pady=1)

        sb = ttk.Scrollbar(list_wrap, orient='vertical',
                           command=self.listbox.yview,
                           style='Cyan.Vertical.TScrollbar')
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=sb.set)

        del_row = tk.Frame(inner, bg=COLORS['panel'])
        del_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(del_row, text='Удалить выделенное',
                   style='Small.TButton',
                   command=self._remove_selected).pack(side=tk.LEFT)
        ttk.Button(del_row, text='Очистить всё',
                   style='Small.TButton',
                   command=self._clear).pack(side=tk.LEFT, padx=(8, 0))

        btns = tk.Frame(inner, bg=COLORS['panel'])
        btns.pack(fill=tk.X, pady=(14, 0))

        ttk.Button(btns, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text='Сохранить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        self._refresh()

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 620) // 2
        y = parent.winfo_rooty() + 80
        self.geometry(f'620x620+{max(0, x)}+{max(0, y)}')

        self.entry.focus_set()
        self.bind('<Escape>', lambda *_: self._cancel())

    def _open_folder(self):
        d = self._data_dir
        if os.path.isdir(d):
            open_folder(d)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + d, parent=self)

    def _copy_path(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._path_var.get())
            self.update()
        except tk.TclError:
            pass

    def _change_dir(self):
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
            self._path_var.set(markers_path(self._data_dir))
            self._markers = load_markers(self._data_dir)
            self._refresh()

    def _refresh(self):
        self.listbox.delete(0, tk.END)
        for m in self._markers:
            self.listbox.insert(tk.END, m)

    def _add(self):
        val = self.entry.get().strip()
        if not val:
            return
        if val in self._markers:
            self.entry.delete(0, tk.END)
            return
        self._markers.append(val)
        self.entry.delete(0, tk.END)
        self._refresh()

    def _remove_selected(self):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            del self._markers[i]
        self._refresh()

    def _clear(self):
        if messagebox.askyesno('Очистить',
                               'Удалить все префиксы?',
                               parent=self):
            self._markers = []
            self._refresh()

    def _ok(self):
        self.result = {
            'markers': list(self._markers),
            'data_dir': self._data_dir,
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# --- Диалог объединения CSV ---
class MergeCsvDialog(tk.Toplevel):
    """Объединение нескольких CSV-файлов из папки в один.

    Ожидается формат, который выдаёт программа: UTF-8 с BOM, ';',
    первая строка - заголовки. Колонки всегда берутся из первого
    файла в списке. Файлы без строк данных пропускаются.

    Папка и имя итогового файла задаются пользователем. По умолчанию
    папка - export_dir из settings.json, имя - merged.csv.
    """

    BTN_WIDTH = 12

    def __init__(self, parent, initial_dir=''):
        super().__init__(parent)
        self.title('Объединение CSV')
        self.minsize(720, 520)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result = None
        self._initial_dir = (initial_dir
                             if initial_dir and os.path.isdir(initial_dir)
                             else os.path.expanduser('~'))
        self._files = []
        self._wheel_widgets = []
        self._canvas = None
        self._list_frame = None
        self._list_win = None

        self._place_window(parent, 900, 640)
        self._build_ui()
        self._reload_files()

        self.bind('<Escape>', lambda *_: self._cancel())
        self.protocol('WM_DELETE_WINDOW', self._cancel)

    def _place_window(self, parent, w, h):
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

    # --- интерфейс ---
    def _build_ui(self):
        self._build_footer()
        self._build_header()
        self._build_body()

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS['panel'])
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Frame(footer, height=1, bg=COLORS['border']).pack(fill=tk.X)

        ftr = tk.Frame(footer, bg=COLORS['panel'])
        ftr.pack(fill=tk.X, padx=18, pady=12)

        ttk.Button(ftr, text='Отмена', style='Secondary.TButton',
                   command=self._cancel).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(ftr, text='Объединить', style='Accent.TButton',
                   command=self._ok).pack(side=tk.RIGHT)

        tk.Label(ftr, text='Итоговый файл:',
                 font=FONTS['body'], fg=COLORS['text'],
                 bg=COLORS['panel']
                 ).pack(side=tk.LEFT)

        self._out_name_var = tk.StringVar(value=DEFAULT_MERGED_NAME)
        tk.Entry(ftr, textvariable=self._out_name_var,
                 font=FONTS['body'], bg=COLORS['panel'],
                 fg=COLORS['text'], insertbackground=COLORS['accent'],
                 width=36
                 ).pack(side=tk.LEFT, padx=(8, 0), ipady=3)

    def _build_header(self):
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

    def _build_body(self):
        body = tk.Frame(self, bg=COLORS['bg'])
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Папка.
        dir_row = tk.Frame(body, bg=COLORS['bg'])
        dir_row.pack(fill=tk.X, padx=18, pady=(12, 6))

        tk.Label(dir_row, text='Папка с CSV:',
                 font=FONTS['kv_key'], fg=COLORS['accent_dark'],
                 bg=COLORS['bg']).pack(side=tk.LEFT, padx=(0, 8))

        self._dir_var = tk.StringVar(value=self._initial_dir)
        entry = tk.Entry(dir_row, textvariable=self._dir_var,
                         font=FONTS['body'], bg=COLORS['panel'],
                         fg=COLORS['text'],
                         insertbackground=COLORS['accent'])
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        ttk.Button(dir_row, text='Обзор...', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._pick_dir).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(dir_row, text='Обновить', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._reload_files
                   ).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(dir_row, text='Открыть', style='Small.TButton',
                   width=self.BTN_WIDTH,
                   command=self._open_dir
                   ).pack(side=tk.LEFT, padx=(4, 0))

        # Массовые кнопки.
        bulk = tk.Frame(body, bg=COLORS['bg'])
        bulk.pack(fill=tk.X, padx=18, pady=(2, 6))
        ttk.Button(bulk, text='Выделить все', style='Small.TButton',
                   command=lambda: self._set_all(True)
                   ).pack(side=tk.LEFT)
        ttk.Button(bulk, text='Снять все', style='Small.TButton',
                   command=lambda: self._set_all(False)
                   ).pack(side=tk.LEFT, padx=(6, 0))
        self._count_var = tk.StringVar(value='Файлов: 0')
        tk.Label(bulk, textvariable=self._count_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg']).pack(side=tk.RIGHT)

        # Список файлов.
        list_wrap = tk.Frame(body, bg=COLORS['border'])
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        self._canvas = tk.Canvas(list_wrap, highlightthickness=0,
                                 bg=COLORS['panel'])
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
            lambda e: self._canvas.itemconfigure(
                self._list_win, width=e.width))

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    # --- колесо ---
    def _bind_wheel_recursive(self, widget):
        try:
            widget.bind('<MouseWheel>', self._on_wheel)
        except Exception:
            pass
        self._wheel_widgets.append(widget)
        for child in widget.winfo_children():
            self._bind_wheel_recursive(child)

    def _on_wheel(self, event):
        try:
            first, last = self._canvas.yview()
            if first <= 0.0 and last >= 1.0:
                return 'break'
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)),
                                      'units')
        except Exception:
            pass
        return 'break'

    # --- работа с файлами ---
    def _pick_dir(self):
        initial = self._dir_var.get() or os.path.expanduser('~')
        chosen = filedialog.askdirectory(
            parent=self, title='Папка с CSV',
            initialdir=initial if os.path.isdir(initial) else None)
        if chosen:
            self._dir_var.set(os.path.abspath(chosen))
            self._reload_files()

    def _open_dir(self):
        d = self._dir_var.get()
        if d and os.path.isdir(d):
            open_folder(d)
        else:
            messagebox.showinfo('Открыть папку',
                                'Папка не найдена:\n' + d, parent=self)

    def _reload_files(self):
        for w in self._wheel_widgets:
            try:
                w.unbind('<MouseWheel>')
            except Exception:
                pass
        self._wheel_widgets = []

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
        except Exception as e:
            messagebox.showerror('Чтение папки', str(e), parent=self)
            self._bind_wheel_recursive(self._canvas)
            self._bind_wheel_recursive(self._list_frame)
            return

        for name in names:
            full = os.path.join(folder, name)
            var = tk.BooleanVar(value=True)
            self._files.append((full, var))

            row = tk.Frame(self._list_frame, bg=COLORS['panel'])
            row.pack(fill=tk.X, padx=6, pady=1)

            cb = ttk.Checkbutton(
                row, text=name, variable=var,
                style='Card.TCheckbutton',
            )
            cb.pack(side=tk.LEFT, anchor='w')

            try:
                size_txt = self._human_size(os.path.getsize(full))
            except Exception:
                size_txt = ''

            tk.Label(row, text=size_txt, font=FONTS['body_sm'],
                     fg=COLORS['text_muted'], bg=COLORS['panel']
                     ).pack(side=tk.RIGHT)

        self._count_var.set(f'Файлов: {len(self._files)}')

        self._bind_wheel_recursive(self._canvas)
        self._bind_wheel_recursive(self._list_frame)

    @staticmethod
    def _human_size(n):
        for unit in ('Б', 'КБ', 'МБ', 'ГБ'):
            if n < 1024:
                return (f'{n:.0f} {unit}'
                        if unit == 'Б' else f'{n:.1f} {unit}')
            n /= 1024
        return f'{n:.1f} ТБ'

    def _set_all(self, value):
        for _, var in self._files:
            var.set(value)

    # --- объединение ---
    def _ok(self):
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
        if os.path.exists(out_path):
            if not messagebox.askyesno(
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

    def _merge(self, paths, out_path):
        """Читает CSV и пишет объединённый файл.

        Колонки - из первого файла. Пустые файлы пропускаются.
        Возвращает (кол-во файлов, кол-во строк данных, список колонок).
        """

        def read_file(path):
            with open(path, 'r', encoding='utf-8-sig',
                      newline='') as f:
                reader = csv.reader(f, delimiter=';')
                try:
                    header = next(reader)
                except StopIteration:
                    return [], []
                rows = [r for r in reader]
            return header, rows

        prepared = []
        columns = None
        for path in paths:
            header, rows = read_file(path)
            if not header and not rows:
                continue
            if not rows:
                continue
            if columns is None:
                columns = list(header)
            prepared.append((path, header, rows))

        if not prepared or not columns:
            raise RuntimeError('Все выбранные файлы пусты.')

        idx = {c: i for i, c in enumerate(columns)}

        total_rows = 0
        files_count = 0

        with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(columns)

            for path, header, rows in prepared:
                src = {i: name for i, name in enumerate(header)}

                for r in rows:
                    if not r:
                        continue
                    if all((x or '').strip() == '' for x in r):
                        continue
                    out = [''] * len(columns)
                    for i, val in enumerate(r):
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

    # --- закрытие ---
    def _cancel(self):
        self.result = None
        self._cleanup_and_close()

    def _cleanup_and_close(self):
        for w in self._wheel_widgets:
            try:
                w.unbind('<MouseWheel>')
            except Exception:
                pass
        self._wheel_widgets = []
        try:
            self.destroy()
        except Exception:
            pass


# --- Главное окно ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Анализ метаданных 1С')
        self.geometry('1450x900')
        self.minsize(900, 600)
        self.configure(bg=COLORS['bg'])

        self.rows, self.columns, self.tree = [], [], None
        self.filtered = []

        self.settings = load_settings()
        self.markers = load_markers(self.settings['data_dir'])

        self.search_mode_var = tk.StringVar(value='all')
        self.only_label_var = tk.StringVar(value='Все')
        self.search_columns = {}
        self.column_checkboxes = []
        self._regex = None
        self.search_entry = None

        self._loading_controls = []
        self._data_loaded = False
        self._help_window = None

        self._search_settings_outer = None
        self._table_outer = None

        self._setup_styles()
        self._build_ui()
        self._set_data_loaded(False)

    # --- Стили ---
    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

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

        style.configure(
            'Accent.TButton',
            font=FONTS['button'],
            foreground='white',
            background=COLORS['accent'],
            borderwidth=0, focusthickness=0,
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
            'Secondary.TButton',
            font=FONTS['button'],
            foreground=COLORS['text'],
            background='#e8eaee',
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
            'Small.TButton',
            font=FONTS['button'],
            foreground=COLORS['text'],
            background='#e8eaee',
            borderwidth=0, focusthickness=0,
            padding=(10, 4), relief='flat',
        )
        style.map(
            'Small.TButton',
            background=[('active', '#d5d8dd'),
                        ('disabled', '#f1f3f5')],
            foreground=[('disabled', '#a6adb8')],
        )

        # Стандартные радиокнопки (без indicatorcolor -
        # чтобы тема clam рисовала обычные точки).
        style.configure(
            'Card.TRadiobutton',
            font=FONTS['body'],
            background=COLORS['panel'],
            foreground=COLORS['text'],
            focuscolor=COLORS['panel'],
            padding=2,
        )
        style.map(
            'Card.TRadiobutton',
            background=[('active', COLORS['panel']),
                        ('selected', COLORS['panel'])],
            foreground=[('disabled', COLORS['text_muted'])],
        )

        # Стандартные чекбоксы (без indicatorcolor -
        # чтобы тема clam рисовала обычные галочки).
        style.configure(
            'Card.TCheckbutton',
            font=FONTS['body'],
            background=COLORS['panel'],
            foreground=COLORS['text'],
            focuscolor=COLORS['panel'],
            padding=2,
        )
        style.map(
            'Card.TCheckbutton',
            background=[('active', COLORS['panel']),
                        ('selected', COLORS['panel'])],
            foreground=[('disabled', COLORS['text_muted'])],
        )

        style.configure(
            'Custom.Horizontal.TProgressbar',
            troughcolor=COLORS['border'],
            background=COLORS['accent'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['accent'],
            darkcolor=COLORS['accent'],
            thickness=8,
        )

        style.configure(
            'Custom.Treeview',
            font=FONTS['body'],
            rowheight=26,
            background=COLORS['panel'],
            fieldbackground=COLORS['panel'],
            foreground=COLORS['text'],
            borderwidth=0,
        )
        style.map(
            'Custom.Treeview',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', 'white')],
        )
        style.configure(
            'Custom.Treeview.Heading',
            font=FONTS['h2'],
            background='#eef1f5',
            foreground=COLORS['text'],
            relief='flat', padding=(8, 6),
        )
        style.map(
            'Custom.Treeview.Heading',
            background=[('active', '#dde3ea')],
        )

        style.configure(
            'Card.TCombobox',
            foreground=COLORS['text'],
            fieldbackground=COLORS['panel'],
            background=COLORS['panel'],
            arrowcolor=COLORS['accent'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border'],
            padding=4,
        )
        style.map(
            'Card.TCombobox',
            fieldbackground=[('readonly', COLORS['panel']),
                             ('disabled', COLORS['panel_alt'])],
            foreground=[('disabled', COLORS['text_muted'])],
            selectbackground=[('readonly', COLORS['panel'])],
            selectforeground=[('readonly', COLORS['text'])],
            arrowcolor=[('disabled', COLORS['text_muted'])],
        )

        self.option_add('*TCombobox*Listbox.font', FONTS['body'])
        self.option_add('*TCombobox*Listbox.background', COLORS['panel'])
        self.option_add('*TCombobox*Listbox.foreground', COLORS['text'])
        self.option_add('*TCombobox*Listbox.selectBackground',
                        COLORS['accent'])
        self.option_add('*TCombobox*Listbox.selectForeground', 'white')

    # --- Интерфейс ---
    def _build_ui(self):
        self._build_top_panel()
        self._build_search_hint()
        self._build_search_settings_panel()
        self._build_table_frame()
        self._build_status_bar()

    def _build_top_panel(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(12, 6))
        self._top_panel_outer = outer

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=12)

        self.btn_open = ttk.Button(inner, text='Открыть XML',
                                   style='Accent.TButton',
                                   command=self.open_file)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_export = ttk.Button(inner, text='Экспорт в CSV',
                                     style='Secondary.TButton',
                                     command=self.export_csv)
        self.btn_export.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_merge = ttk.Button(inner, text='Объединить CSV',
                                    style='Secondary.TButton',
                                    command=self.open_merge_dialog)
        self.btn_merge.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_markers = ttk.Button(inner, text='Префиксы',
                                      style='Secondary.TButton',
                                      command=self.open_markers_dialog)
        self.btn_markers.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_settings = ttk.Button(inner, text='Настройки',
                                       style='Secondary.TButton',
                                       command=self.open_settings_dialog)
        self.btn_settings.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_help = ttk.Button(
            inner, text='Инструкция', style='Secondary.TButton',
            command=lambda: self.open_user_help(anchor='start'),
        )
        self.btn_help.pack(side=tk.RIGHT)

        search_block = tk.Frame(inner, bg=COLORS['panel'])
        search_block.pack(side=tk.LEFT, fill=tk.X, expand=True,
                          padx=(24, 24))

        self.lbl_search = tk.Label(search_block, text='Поиск:',
                                   font=FONTS['body'], fg=COLORS['text'],
                                   bg=COLORS['panel'])
        self.lbl_search.pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            'write',
            lambda *_: (self.apply_filter(), self._update_search_hint()),
        )

        entry_wrap = tk.Frame(search_block, bg=COLORS['border'])
        entry_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry = tk.Entry(
            entry_wrap, textvariable=self.search_var,
            font=FONTS['body'], bd=0, relief='flat',
            bg=COLORS['panel'], fg=COLORS['text'],
            insertbackground=COLORS['accent'], width=30,
            disabledbackground=COLORS['panel_alt'],
            disabledforeground=COLORS['text_muted'],
        )
        self.search_entry.pack(padx=1, pady=1, ipady=5, fill=tk.X,
                               expand=True)

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

        def _show_search_menu(event):
            try:
                self._search_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._search_menu.grab_release()

        self.search_entry.bind('<Button-3>', _show_search_menu)

        for seq in ('<Control-v>', '<Control-V>'):
            self.search_entry.bind(seq, lambda e: self._paste_to_search())
        for seq in ('<Control-c>', '<Control-C>'):
            self.search_entry.bind(seq, lambda e: self._copy_from_search())
        for seq in ('<Control-x>', '<Control-X>'):
            self.search_entry.bind(seq, lambda e: self._cut_from_search())
        for seq in ('<Control-a>', '<Control-A>'):
            self.search_entry.bind(seq, lambda e: self._select_all_search())

        self.btn_clear_search = ttk.Button(search_block,
                                           text='Очистить поиск',
                                           style='Secondary.TButton',
                                           command=self._clear_search)
        self.btn_clear_search.pack(side=tk.LEFT, padx=(8, 0))

        prog_wrap = tk.Frame(outer, bg=COLORS['bg'])
        prog_wrap.pack(fill=tk.X, pady=(8, 0))

        self.progress = ttk.Progressbar(
            prog_wrap, mode='determinate', maximum=100,
            style='Custom.Horizontal.TProgressbar',
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_var = tk.StringVar(value='')
        tk.Label(prog_wrap, textvariable=self.progress_var,
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['bg'], width=24, anchor='e'
                 ).pack(side=tk.LEFT, padx=(8, 0))

        self._loading_controls.extend([
            self.btn_export,
            self.btn_markers,
            self.search_entry,
            self.btn_clear_search,
        ])

    def _build_search_settings_panel(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 6))
        self._search_settings_outer = outer
        outer.pack_forget()

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=10)

        tk.Label(inner, text='Поля поиска',
                 font=FONTS['h2'], fg=COLORS['text'],
                 bg=COLORS['panel']
                 ).pack(anchor='w')

        mode_row = tk.Frame(inner, bg=COLORS['panel'])
        mode_row.pack(fill=tk.X, pady=(8, 0))

        self.rb_all_fields = ttk.Radiobutton(
            mode_row, text='По всем полям',
            variable=self.search_mode_var, value='all',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change,
        )
        self.rb_all_fields.pack(side=tk.LEFT, padx=(0, 16))

        self.rb_selected_fields = ttk.Radiobutton(
            mode_row, text='Только по выбранным',
            variable=self.search_mode_var, value='selected',
            style='Card.TRadiobutton',
            command=self._on_search_mode_change,
        )
        self.rb_selected_fields.pack(side=tk.LEFT)

        self.btn_uncheck_all = ttk.Button(
            mode_row, text='Снять все', style='Small.TButton',
            command=lambda: self._set_all_columns(False))
        self.btn_uncheck_all.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_check_all = ttk.Button(
            mode_row, text='Отметить все', style='Small.TButton',
            command=lambda: self._set_all_columns(True))
        self.btn_check_all.pack(side=tk.RIGHT)

        self.columns_frame = tk.Frame(inner, bg=COLORS['panel'])
        self.columns_frame.pack(fill=tk.X, pady=(8, 0))

        tk.Frame(inner, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(12, 0))

        obj_row = tk.Frame(inner, bg=COLORS['panel'])
        obj_row.pack(fill=tk.X, pady=(10, 0))

        self.lbl_obj = tk.Label(obj_row, text='Признак объекта:',
                                font=FONTS['h2'], fg=COLORS['text'],
                                bg=COLORS['panel'])
        self.lbl_obj.pack(side=tk.LEFT, padx=(0, 10))

        self.only_combo = ttk.Combobox(
            obj_row, textvariable=self.only_label_var,
            values=list(ONLY_LABELS.keys()),
            state='readonly', width=24,
            font=FONTS['body'], style='Card.TCombobox',
        )
        self.only_combo.pack(side=tk.LEFT)
        self.only_combo.bind('<<ComboboxSelected>>',
                             lambda *_: self.apply_filter())

        self._loading_controls.extend([
            self.rb_all_fields,
            self.rb_selected_fields,
            self.btn_check_all,
            self.btn_uncheck_all,
            self.only_combo,
        ])

    def _build_search_hint(self):
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

        tk.Label(inner, text='Как искать:',
                 font=FONTS['hint'], fg='#b8860b',
                 bg=COLORS['warn_bg']
                 ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            inner,
            text=(
                'Пишите слово как обычно - оно найдется везде, где есть.   '
                'Если нужно точнее, добавьте знаки:   '
                '^ в начале - "начинается с",   '
                '$ в конце - "заканчивается на",   '
                '? вместо одной буквы,   '
                '* вместо нескольких.'
            ),
            font=FONTS['body'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'], justify=tk.LEFT, anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _update_search_hint(self):
        if not hasattr(self, '_search_hint_outer'):
            return
        if self.search_var.get().strip():
            self._search_hint_outer.pack(fill=tk.X, padx=12, pady=(0, 6),
                                         after=self._top_panel_outer)
        else:
            self._search_hint_outer.pack_forget()

    def _build_table_frame(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
        self._table_outer = outer

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.BOTH, expand=True)

        self.table_frame = tk.Frame(panel, bg=COLORS['panel'])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_status_bar(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 10))

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=6)

        self.status_var = tk.StringVar(value='Готов. Откройте XML.')
        self.lbl_status = tk.Label(
            inner, textvariable=self.status_var,
            font=FONTS['body'], fg=COLORS['text_muted'],
            bg=COLORS['panel'], anchor='w', justify=tk.LEFT,
        )
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _set_data_loaded(self, loaded):
        self._data_loaded = loaded

        for w in self._loading_controls:
            try:
                w.state(['!disabled'] if loaded else ['disabled'])
            except Exception:
                try:
                    w.configure(state='normal' if loaded else 'disabled')
                except Exception:
                    pass

        try:
            self.lbl_search.configure(
                fg=COLORS['text'] if loaded else COLORS['text_muted'])
        except Exception:
            pass
        try:
            self.lbl_obj.configure(
                fg=COLORS['text'] if loaded else COLORS['text_muted'])
        except Exception:
            pass

        if self._search_settings_outer is not None:
            if loaded:
                before_widget = self._table_outer
                if before_widget is not None:
                    self._search_settings_outer.pack(
                        fill=tk.X, padx=12, pady=(0, 6),
                        before=before_widget)
                else:
                    self._search_settings_outer.pack(
                        fill=tk.X, padx=12, pady=(0, 6))
            else:
                self._search_settings_outer.pack_forget()

        if loaded:
            self._update_checkboxes_state()
        else:
            for cb in self.column_checkboxes:
                cb.state(['disabled'])
            for btn in (getattr(self, 'btn_check_all', None),
                        getattr(self, 'btn_uncheck_all', None)):
                if btn is not None:
                    btn.state(['disabled'])

    def _rebuild_column_checkboxes(self):
        for w in self.columns_frame.winfo_children():
            w.destroy()
        self.search_columns.clear()
        self.column_checkboxes.clear()

        for col in self.columns:
            var = tk.BooleanVar(value=True)
            self.search_columns[col] = var

            cb = ttk.Checkbutton(
                self.columns_frame, text=col, variable=var,
                style='Card.TCheckbutton',
                command=self.apply_filter,
            )
            cb.pack(side=tk.LEFT, padx=(0, 12), pady=2)
            self.column_checkboxes.append(cb)

        self._update_checkboxes_state()

    def _on_search_mode_change(self):
        self._update_checkboxes_state()
        self.apply_filter()

    def _update_checkboxes_state(self):
        if not self._data_loaded:
            for cb in self.column_checkboxes:
                cb.state(['disabled'])
            for btn in (getattr(self, 'btn_check_all', None),
                        getattr(self, 'btn_uncheck_all', None)):
                if btn is not None:
                    btn.state(['disabled'])
            return

        enabled = self.search_mode_var.get() == 'selected'
        for cb in self.column_checkboxes:
            cb.state(['!disabled'] if enabled else ['disabled'])
        for btn in (getattr(self, 'btn_check_all', None),
                    getattr(self, 'btn_uncheck_all', None)):
            if btn is not None:
                btn.state(['!disabled'] if enabled else ['disabled'])

    def _set_all_columns(self, value):
        if not self._data_loaded:
            return
        if self.search_mode_var.get() != 'selected':
            return
        for var in self.search_columns.values():
            var.set(value)
        self.apply_filter()

    def _active_search_columns(self):
        if self.search_mode_var.get() == 'all':
            return self.columns
        return [c for c, var in self.search_columns.items() if var.get()]

    # --- Инструкция ---
    def open_user_help(self, anchor='start'):
        help_win = getattr(self, '_help_window', None)
        if help_win is not None:
            try:
                if help_win.winfo_exists():
                    help_win.deiconify()
                    help_win.lift()
                    help_win.focus_force()
                    return
            except tk.TclError:
                pass

        self._help_window = HelpWindow(self, anchor=anchor)
        try:
            self._help_window.protocol('WM_DELETE_WINDOW',
                                       self._close_help_window)
        except tk.TclError:
            pass

    def _close_help_window(self):
        help_win = getattr(self, '_help_window', None)
        if help_win is None:
            return
        try:
            help_win.destroy()
        except tk.TclError:
            pass
        self._help_window = None
        if getattr(self, 'search_entry', None) and self._data_loaded:
            self.search_entry.focus_set()

    # --- Поиск: буфер ---
    def _paste_to_search(self):
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

    def _copy_from_search(self):
        if not self.search_entry:
            return
        try:
            text = self.search_entry.selection_get()
        except tk.TclError:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _cut_from_search(self):
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

    def _select_all_search(self):
        if not self.search_entry:
            return
        self.search_entry.select_range(0, tk.END)
        self.search_entry.icursor(tk.END)
        return 'break'

    def _clear_search(self):
        self.search_var.set('')
        if self.search_entry and self._data_loaded:
            self.search_entry.focus_set()

    # --- Префиксы ---
    def open_markers_dialog(self):
        dlg = MarkersDialog(self, self.markers,
                            self.settings['data_dir'],
                            on_change_dir=self._change_data_dir)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        new_dir = dlg.result['data_dir']
        self.settings['data_dir'] = new_dir
        try:
            save_settings(self.settings)
        except Exception as e:
            messagebox.showerror('Сохранение',
                                 f'Не удалось сохранить settings.json:\n{e}')

        self.markers = dlg.result['markers']
        try:
            save_markers(self.settings['data_dir'], self.markers)
        except Exception as e:
            messagebox.showerror('Сохранение',
                                 f'Не удалось сохранить список префиксов:\n{e}')

        self._recompute_markers()
        self.apply_filter()
        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Префиксов: {len(self.markers)}. Кастомных строк: {n_custom}')

    def _change_data_dir(self, new_dir):
        new_dir = os.path.abspath(new_dir)
        try:
            os.makedirs(new_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось создать папку:\n{e}')
            return False

        try:
            save_markers(new_dir, self.markers)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось записать префиксы:\n{e}')
            return False

        self.settings['data_dir'] = new_dir
        try:
            save_settings(self.settings)
        except Exception as e:
            messagebox.showerror('Смена папки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return False

        self.markers = load_markers(new_dir)
        return True

    def _recompute_markers(self):
        if not self.rows:
            return
        for r in self.rows:
            r['ПризнакОбъекта'] = (
                CUSTOM_TAG
                if is_custom_name(r.get('ИмяОбъекта', ''), self.markers)
                else STD_TAG
            )

    # --- Настройки ---
    def open_settings_dialog(self):
        dlg = SettingsDialog(self, self.settings)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        old_data_dir = self.settings['data_dir']
        new = dlg.result

        new_settings_dir = new.get('settings_dir', '')
        if new_settings_dir and new_settings_dir != self.settings['settings_dir']:
            try:
                os.makedirs(new_settings_dir, exist_ok=True)
            except Exception as e:
                messagebox.showerror('Настройки',
                                     f'Не удалось создать папку настроек:\n{e}')
                return

        self.settings['settings_dir'] = new_settings_dir
        self.settings['data_dir'] = new.get('data_dir') or new_settings_dir
        self.settings['xml_dir'] = new.get('xml_dir', '')
        self.settings['export_dir'] = new.get('export_dir', '')

        if old_data_dir != self.settings['data_dir']:
            try:
                os.makedirs(self.settings['data_dir'], exist_ok=True)
                save_markers(self.settings['data_dir'], self.markers)
            except Exception as e:
                messagebox.showerror(
                    'Настройки',
                    f'Не удалось перенести префиксы в новую папку:\n{e}')

        try:
            save_settings(self.settings)
        except Exception as e:
            messagebox.showerror('Настройки',
                                 f'Не удалось сохранить settings.json:\n{e}')
            return

        self.markers = load_markers(self.settings['data_dir'])
        self._recompute_markers()
        self.apply_filter()
        self.status_var.set(
            f'Настройки сохранены. Папка данных: '
            f'{self.settings["data_dir"]}')

    # --- Объединение CSV ---
    def open_merge_dialog(self):
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
            f'Строк данных: {r["rows"]:,}\n'
            f'Колонок: {len(r["columns"])}'.replace(',', ' '),
            parent=self,
        )

        self.settings['export_dir'] = os.path.dirname(r['path'])
        try:
            save_settings(self.settings)
        except Exception:
            pass

    # --- Построение таблицы ---
    def _rebuild_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(
            self.table_frame, columns=self.columns,
            show='headings', selectmode='browse',
            style='Custom.Treeview',
        )

        for c in self.columns:
            self.tree.heading(c, text=c,
                              command=lambda col=c: self.sort_by(col))
            self.tree.column(c, width=150, anchor='w',
                             minwidth=40, stretch=False)

        for col, w in (('ТипОбъекта', 140), ('ИмяОбъекта', 200),
                       ('ВидЭлемента', 150), ('ИмяЭлемента', 220),
                       ('ВидВложенногоЭлемента', 190),
                       ('ИмяВложенногоЭлемента', 200),
                       ('ПутьЭлемента', 400),
                       ('ПризнакОбъекта', 130),
                       ('name', 400)):
            if col in self.columns:
                self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(self.table_frame, orient='vertical',
                            command=self.tree.yview,
                            style='Cyan.Vertical.TScrollbar')
        hsb = ttk.Scrollbar(self.table_frame, orient='horizontal',
                            command=self.tree.xview,
                            style='Cyan.Horizontal.TScrollbar')

        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        self.table_frame.rowconfigure(0, weight=1)
        self.table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure('odd', background=COLORS['panel'])
        self.tree.tag_configure('even', background=COLORS['panel_alt'])
        self.tree.tag_configure('match', background=COLORS['highlight'])

        self.tree.bind('<Double-Button-1>', self._on_double_click_header)

    def _on_double_click_header(self, event):
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
        new_width = max(60, min(700, max_len * 8))
        self.tree.column(col_name, width=new_width)

    # --- Загрузка файла ---
    def open_file(self):
        initial_dir = self.settings.get('xml_dir') or None
        if initial_dir and not os.path.isdir(initial_dir):
            initial_dir = None

        path = filedialog.askopenfilename(
            title='Выберите ConfigDumpInfo.xml',
            filetypes=[('XML files', '*.xml'), ('All files', '*.*')],
            initialdir=initial_dir)
        if not path:
            return

        folder = os.path.dirname(os.path.abspath(path))
        self.settings['xml_dir'] = folder
        try:
            save_settings(self.settings)
        except Exception:
            pass

        self.progress['value'] = 0
        self.progress_var.set('0%')
        self.status_var.set(f'Файл: {os.path.basename(path)}')

        def worker():
            try:
                self._set_status_safe('Подсчёт записей...')
                ns_uri = detect_namespace(path)

                def count_cb(n):
                    self._progress_safe('', f'Подсчёт: {n:,}'
                                        .replace(',', ' '))

                total = count_metadata(path, ns_uri, progress_cb=count_cb)

                self._set_status_safe(
                    f'Найдено {total:,} записей, начинаю парсинг...'
                    .replace(',', ' '))
                self._progress_safe(0, '0%')

                def parse_cb(done, tot):
                    pct = int(done * 100 / tot) if tot else 100
                    self._progress_safe(
                        pct, f'{pct}%  ({done:,} из {tot:,})'
                        .replace(',', ' '))

                rows, cols = parse_xml(path, ns_uri, total,
                                       progress_cb=parse_cb,
                                       markers=self.markers)

                self.rows, self.columns = rows, cols
                self.after(0, self._after_load)

            except Exception as e:
                self.after(0, lambda: messagebox.showerror('Ошибка', str(e)))
                self.after(0, self._reset_progress_safe)

        threading.Thread(target=worker, daemon=True).start()

    def _set_status_safe(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def _progress_safe(self, pct, label):
        def do():
            if pct != '':
                self.progress['value'] = pct
            self.progress_var.set(label)
        self.after(0, do)

    def _reset_progress_safe(self):
        self.after(0, lambda: (self.progress.configure(value=0),
                               self.progress_var.set('')))

    def _after_load(self):
        self.progress['value'] = 100
        self.progress_var.set('100%')
        self._rebuild_table()
        self._rebuild_column_checkboxes()
        self._set_data_loaded(True)

        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Загружено {len(self.rows):,} записей, '
            f'колонок: {len(self.columns)}, '
            f'кастомных: {n_custom:,}'.replace(',', ' '))
        self.apply_filter()

    # --- Фильтрация ---
    def _is_match(self, row):
        if self._regex is None:
            return False
        cols = self._active_search_columns()
        return any(match_query(self._regex, row.get(c, '')) for c in cols)

    def apply_filter(self):
        if not self._data_loaded:
            return

        pattern = self.search_var.get().strip()
        cols = self._active_search_columns()
        self._regex = compile_query(pattern)

        only = ONLY_LABELS.get(self.only_label_var.get(), 'all')

        def obj_ok(row):
            if only == 'custom':
                return row.get('ПризнакОбъекта') == CUSTOM_TAG
            if only == 'std':
                return row.get('ПризнакОбъекта') == STD_TAG
            return True

        if (pattern and self.search_mode_var.get() == 'selected'
                and not cols):
            self.filtered = []
            self.status_var.set(
                'Режим "Только по выбранным", но ни одна колонка '
                'не отмечена. Поставьте галочки в панели "Поля поиска".')
            self.render_table()
            return

        if not pattern:
            self.filtered = [r for r in self.rows if obj_ok(r)]
        else:
            self.filtered = [r for r in self.rows
                             if obj_ok(r) and self._is_match(r)]

        self.render_table()

    def render_table(self):
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
            f'Показано {len(self.filtered):,} '
            f'(всего: {len(self.rows):,})'.replace(',', ' '))

    def sort_by(self, col):
        self.filtered.sort(key=lambda r: str(r.get(col, '')).lower())
        self.render_table()

    # --- Экспорт ---
    def export_csv(self):
        if not self.rows:
            messagebox.showwarning('Экспорт', 'Сначала загрузите XML.')
            return

        pattern = self.search_var.get().strip()
        has_query = bool(pattern)

        matches = ([r for r in self.filtered if self._is_match(r)]
                   if has_query else [])

        dlg = ExportDialog(self, has_query,
                           len(self.rows), len(matches))
        self.wait_window(dlg)
        if not dlg.result:
            return

        mode = dlg.result
        if mode == 'all':
            data, name = self.rows, 'export_all.csv'
        else:
            safe_q = re.sub(r'[^\w\u0400-\u04FF\-]', '_', pattern) or 'result'
            data, name = matches, f'export_{safe_q}.csv'

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

        folder = os.path.dirname(os.path.abspath(path))
        self.settings['export_dir'] = folder
        try:
            save_settings(self.settings)
        except Exception:
            pass

        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=self.columns,
                               delimiter=';', extrasaction='ignore')
            w.writeheader()
            w.writerows(data)

        messagebox.showinfo(
            'Экспорт',
            f'Сохранено: {path}\n'
            f'Записей: {len(data):,}'.replace(',', ' '))


if __name__ == '__main__':
    App().mainloop()