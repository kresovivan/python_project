"""
GUI-парсер ConfigDumpInfo.xml (метаданные 1С).

Возможности:
- открытие XML через диалог;
- потоковый парсинг больших файлов с прогрессом;
- динамические колонки: 8 базовых (русских) + все атрибуты XML;
- русские значения ТипОбъекта, ВидЭлемента, ВидВложенногоЭлемента;
- колонка ПутьЭлемента в терминах 1С;
- колонка ПризнакОбъекта: Кастомный / Стандартный по списку префиксов;
- список префиксов хранится в config_markers.json рядом со скриптом
  и редактируется через кнопку "Префиксы";
- фильтр по признаку объекта выпадающим списком;
- поиск по всем полям или только по выбранным чекбоксами;
- шаблоны поиска: ^ (начало), $ (конец), ? (один символ), * (любое число);
- подсветка найденного жёлтым, зебра строк;
- колонки растягиваются мышью, не сжимая соседей;
- двойной клик по границе заголовка - автоподгон ширины;
- экспорт в CSV: всё / только подсвеченные;
- короткая инструкция пользователя;
- вставка из буфера по Ctrl+V, правым кликом по полю поиска,
  а также прямо из окна инструкции;
- кнопка "Очистить поиск" рядом с полем поиска;
- статусная строка вынесена вниз окна отдельной полосой;
- зависимые от данных элементы выключены до загрузки XML.

Только стандартная библиотека Python 3.8+.
"""
import os
import re
import csv
import json
import threading
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
    'h2':      ('Segoe UI Semibold', 10),
    'body':    ('Segoe UI', 9),
    'body_sm': ('Segoe UI', 8),
    'button':  ('Segoe UI', 9),
    'mono':    ('Consolas', 11, 'bold'),
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


# --- Префиксы кастомных объектов ---
MARKERS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'config_markers.json',
)

DEFAULT_MARKERS = ['ПЛ_']

CUSTOM_TAG = 'Кастомный'
STD_TAG = 'Стандартный'
NONE_TAG = '-'

ONLY_LABELS = {
    'Все': 'all',
    'Только кастомные': 'custom',
    'Только стандартные': 'std',
}


def load_markers():
    """Читает список префиксов из JSON. При ошибке возвращает DEFAULT_MARKERS."""
    try:
        with open(MARKERS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get('markers'), list):
            return [str(x) for x in data['markers'] if str(x).strip()]
        if isinstance(data, list):
            return [str(x) for x in data if str(x).strip()]
    except Exception:
        pass
    return list(DEFAULT_MARKERS)


def save_markers(markers):
    """Сохраняет список префиксов в JSON."""
    with open(MARKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'markers': list(markers)}, f,
                  ensure_ascii=False, indent=2)


def is_custom_name(name, markers):
    """Объект считается кастомным, если его имя начинается с префикса."""
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
    """URI namespace из корневого тега XML."""
    for _, elem in ET.iterparse(path, events=('start',)):
        t = elem.tag
        return t[1:t.index('}')] if t.startswith('{') else ''
    return ''


def count_metadata(path, ns_uri, progress_cb=None):
    """Быстрый проход по файлу: количество тегов Metadata."""
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
    """Разбор атрибута name на русские колонки."""
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
    """Потоковый парсинг. Возвращает (rows, columns)."""
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


# --- Поиск по шаблону ---
def compile_query(pattern):
    """Превращает шаблон (^, $, ?, *) в скомпилированное регулярное выражение."""
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
    """Проверяет значение на соответствие шаблону."""
    if regex is None:
        return False
    return regex.search(str(value)) is not None


# --- Копируемая метка ---
class CopyableLabel(tk.Label):
    """tk.Label с копированием по правому или двойному клику.

    Параметры:
      text       - что видно в метке;
      copy_value - что копировать в буфер. Если None - копируется text.
                   Если задан - в буфер попадёт именно это значение,
                   а в контекстное меню добавится пункт
                   "Копировать строку целиком", который положит весь text.
      app        - ссылка на главное окно (App). Если задана, в меню
                   появится пункт "Копировать и вставить в поиск".
    """

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
    """Короткая инструкция: что делать и в каком порядке."""

    SECTIONS = [
        ('С чего начать', [
            {'type': 'text',
             'text': 'Открываем XML, ждём окончания разбора, ищем нужное, '
                     'выгружаем в CSV. Всё.'},
            {'type': 'steps', 'items': [
                'Жмём "Открыть XML" и выбираем файл ConfigDumpInfo.xml.',
                'Ждём: прогресс покажет проценты, а строки появятся '
                'в таблице.',
                'Если нужно отделить свои объекты от типовых - жмём '
                '"Префиксы" и задаём префиксы (по умолчанию ПЛ_).',
                'Пишем запрос в поле "Поиск" и при желании выбираем '
                'поля и признак объекта.',
                'Жмём "Экспорт в CSV" - сохраняем всё или только то, '
                'что подсветилось.',
            ]},
        ]),

        ('Открытие файла', [
            {'type': 'text',
             'text': 'Файл ConfigDumpInfo.xml выгружается из Конфигуратора: '
                     '"Конфигурация" -> "Выгрузить конфигурацию в файл". '
                     'Размер роли не играет - разбор идёт потоково, '
                     'память не забивается.'},
            {'type': 'text',
             'text': 'Пока файл не открыт, кнопки поиска и экспорта '
                     'неактивны. Это нормально - сначала данные.'},
        ]),

        ('Что в таблице', [
            {'type': 'text',
             'text': 'Каждая строка - один элемент конфигурации. '
                     'Основные колонки:'},
            {'type': 'kv', 'items': [
                ('ТипОбъекта', 'Справочник, Документ, РегистрСведений и т. д.'),
                ('ИмяОбъекта', 'Имя самого объекта, например ФизическиеЛица.'),
                ('ВидЭлемента', 'Реквизит, ТабличнаяЧасть, Форма, Команда...'),
                ('ИмяЭлемента', 'Имя этого элемента.'),
                ('ПутьЭлемента', 'Полный путь по-русски: '
                                 'Справочник.ФизическиеЛица.Реквизит.ФИО'),
                ('ПризнакОбъекта', 'Кастомный или Стандартный - по префиксам.'),
            ]},
            {'type': 'text',
             'text': 'Остальные колонки (id, configVersion и подобные) - '
                     'это атрибуты XML, они появляются сами.'},
        ]),

        ('Свои объекты: префиксы', [
            {'type': 'text',
             'text': 'Объект считается кастомным, если его имя начинается '
                     'с одного из ваших префиксов. По умолчанию ПЛ_. '
                     'Список хранится в config_markers.json рядом '
                     'со скриптом.'},
            {'type': 'steps', 'items': [
                'Кнопка "Префиксы" - открыть список.',
                'Вводим префикс, Enter - он в списке.',
                'Выделяем лишнее, "Удалить выделенное" - убрать.',
                '"Сохранить" - записать файл и пересчитать признак '
                'у всех строк сразу.',
            ]},
            {'type': 'text',
             'text': 'Пример. С префиксами ПЛ_ и АБ_: ПЛ_Заявка и '
                     'АБ_Договор - кастомные, ФизическиеЛица - '
                     'стандартный.'},
        ]),

        ('Поиск', [
            {'type': 'text',
             'text': 'Ищем по подстроке, регистр не важен. Плюс есть '
                     'четыре знака-шаблона:'},
            {'type': 'kv', 'items': [
                ('^', 'начало поля'),
                ('$', 'конец поля'),
                ('?', 'ровно один любой символ'),
                ('*', 'любое количество символов'),
            ]},
            {'type': 'text', 'text': 'Примеры:'},
            {'type': 'samples', 'items': [
                ('ФИО', 'где угодно'),
                ('^ФИО', 'начинается с ФИО'),
                ('ФИО$', 'заканчивается на ФИО'),
                ('^ФИО$', 'ровно ФИО'),
                ('Ф?О', 'одна любая буква между Ф и О'),
                ('Ф*О', 'любое число букв между Ф и О'),
                ('Д?та*ждения', 'ДатаРождения, ДитаРождения'),
            ]},
            {'type': 'text',
             'text': 'Правый клик по шаблону копирует только сам шаблон. '
                     'Двойной клик - то же. Если нужна фраза целиком, '
                     'в меню есть "Копировать строку целиком".'},
            {'type': 'text',
             'text': 'Вставить текст можно без кнопок: Ctrl+V прямо '
                     'в поле поиска, либо правый клик по полю -> '
                     '"Вставить". Сбросить поле - кнопка "Очистить поиск".'},
        ]),

        ('Где искать', [
            {'type': 'text',
             'text': 'По умолчанию поиск идёт по всем колонкам. Если '
                     'это слишком широко - включаем "Только по выбранным" '
                     'и отмечаем галочками нужные колонки.'},
            {'type': 'text',
             'text': 'Типичный случай: ищем конкретный GUID. Включаем '
                     '"Только по выбранным", оставляем галочку на id, '
                     'вставляем GUID через Ctrl+V.'},
        ]),

        ('Признак объекта', [
            {'type': 'text',
             'text': 'Выпадающий список справа от "Только по выбранным". '
                     'Быстрый способ отсеять лишнее.'},
            {'type': 'kv', 'items': [
                ('Все', 'показывать всё'),
                ('Только кастомные', 'только строки с вашими префиксами'),
                ('Только стандартные', 'только типовые объекты'),
            ]},
            {'type': 'text',
             'text': 'Фильтр работает вместе с поиском: сначала '
                     'отсекаем по признаку, потом ищем по шаблону.'},
        ]),

        ('Колонки', [
            {'type': 'text',
             'text': 'Тянем границу заголовка - колонка расширяется, '
                     'соседние уезжают вправо, снизу включается '
                     'горизонтальная прокрутка. Двойной клик по границе - '
                     'подгон под самые длинные данные.'},
            {'type': 'text',
             'text': 'Клик по заголовку - сортировка по колонке.'},
        ]),

        ('Экспорт в CSV', [
            {'type': 'text',
             'text': 'Файл сохраняется в UTF-8 с BOM и разделителем ";". '
                     'Excel и LibreOffice открывают его нормально.'},
            {'type': 'steps', 'items': [
                'Жмём "Экспорт в CSV".',
                'Выбираем: все строки или только подсвеченные '
                '(второе - если есть непустой поиск).',
                'Указываем файл.',
                'Готово - программа скажет, сколько записей сохранила.',
            ]},
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
                 font=('Segoe UI Semibold', 16),
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
                 font=('Segoe UI Semibold', 13),
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
                             font=('Segoe UI Semibold', 10),
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
                        font=('Segoe UI Semibold', 9),
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
    """Окно выбора режима экспорта: всё или только подсвеченные."""

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
                 font=('Segoe UI Semibold', 12),
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w', pady=(0, 12))

        def radio(text, value, enabled=True):
            rb = tk.Radiobutton(
                inner, text=text, variable=self.mode, value=value,
                font=FONTS['body'], fg=COLORS['text'],
                bg=COLORS['panel'], activebackground=COLORS['panel'],
                selectcolor=COLORS['panel'],
                anchor='w', padx=4,
            )
            rb.pack(anchor='w', pady=3, fill=tk.X)
            if not enabled:
                rb.configure(state='disabled',
                              fg=COLORS['text_muted'])

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


# --- Диалог управления префиксами ---
class MarkersDialog(tk.Toplevel):
    """Редактор списка префиксов кастомных объектов."""

    def __init__(self, parent, markers):
        super().__init__(parent)
        self.title('Префиксы кастомных объектов')
        self.geometry('520x560')
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS['bg'])

        self.result = None
        self._markers = list(markers)

        card = tk.Frame(self, bg=COLORS['panel'],
                        highlightthickness=1,
                        highlightbackground=COLORS['border'])
        card.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        inner = tk.Frame(card, bg=COLORS['panel'])
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)

        tk.Label(inner, text='Префиксы имён кастомных объектов',
                 font=('Segoe UI Semibold', 12),
                 fg=COLORS['text'], bg=COLORS['panel']
                 ).pack(anchor='w')

        tk.Label(inner,
                 text='Объект считается кастомным, если "ИмяОбъекта" '
                      'начинается с одного из префиксов.\n'
                      'Пример: ПЛ_, АБ_, Моё_. Список сохраняется в файл '
                      f'{os.path.basename(MARKERS_FILE)} рядом со скриптом.',
                 font=FONTS['body_sm'], fg=COLORS['text_muted'],
                 bg=COLORS['panel'], justify=tk.LEFT
                 ).pack(anchor='w', pady=(4, 10))

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
        x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_rooty() + 100
        self.geometry(f'520x560+{max(0, x)}+{max(0, y)}')

        self.entry.focus_set()
        self.bind('<Escape>', lambda *_: self._cancel())

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
        self.result = list(self._markers)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


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

        self.markers = load_markers()

        self.search_mode_var = tk.StringVar(value='all')
        self.only_label_var = tk.StringVar(value='Все')
        self.search_columns = {}
        self.column_checkboxes = []
        self._regex = None
        self.search_entry = None

        self._loading_controls = []
        self._data_loaded = False

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
            borderwidth=0,
            focusthickness=0,
            padding=(14, 7),
            relief='flat',
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
            borderwidth=0,
            focusthickness=0,
            padding=(14, 7),
            relief='flat',
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
            font=FONTS['body'],
            foreground=COLORS['text'],
            background='#e8eaee',
            borderwidth=0,
            focusthickness=0,
            padding=(10, 4),
            relief='flat',
        )
        style.map(
            'Small.TButton',
            background=[('active', '#d5d8dd'),
                        ('disabled', '#f1f3f5')],
            foreground=[('disabled', '#a6adb8')],
        )

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

        style.configure(
            'Card.TCheckbutton',
            font=FONTS['body'],
            background=COLORS['panel'],
            foreground=COLORS['text'],
            padding=2,
        )
        style.map(
            'Card.TCheckbutton',
            background=[('active', COLORS['panel'])],
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
            relief='flat',
            padding=(8, 6),
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

    # --- Верхняя панель ---
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

        # Левая группа.
        self.btn_open = ttk.Button(inner, text='Открыть XML',
                                   style='Accent.TButton',
                                   command=self.open_file)
        self.btn_open.pack(side=tk.LEFT)

        self.btn_export = ttk.Button(inner, text='Экспорт в CSV',
                                     style='Secondary.TButton',
                                     command=self.export_csv)
        self.btn_export.pack(side=tk.LEFT, padx=(8, 0))

        self.btn_markers = ttk.Button(inner, text='Префиксы',
                                      style='Secondary.TButton',
                                      command=self.open_markers_dialog)
        self.btn_markers.pack(side=tk.LEFT, padx=(8, 0))

        # Правая группа.
        self.btn_help = ttk.Button(
            inner,
            text='Инструкция',
            style='Secondary.TButton',
            command=lambda: self.open_user_help(anchor='start'),
        )
        self.btn_help.pack(side=tk.RIGHT)

        # Центральный блок - поиск.
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
            lambda *_: (
                self.apply_filter(),
                self._update_search_hint(),
            ),
        )

        entry_wrap = tk.Frame(search_block, bg=COLORS['border'])
        entry_wrap.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry = tk.Entry(
            entry_wrap, textvariable=self.search_var,
            font=FONTS['body'], bd=0, relief='flat',
            bg=COLORS['panel'], fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            width=30,
            disabledbackground=COLORS['panel_alt'],
            disabledforeground=COLORS['text_muted'],
        )
        self.search_entry.pack(padx=1, pady=1, ipady=5, fill=tk.X,
                               expand=True)

        # Контекстное меню правого клика по полю поиска.
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

        # Горячие клавиши внутри поля поиска.
        self.search_entry.bind('<Control-v>',
                               lambda e: self._paste_to_search())
        self.search_entry.bind('<Control-V>',
                               lambda e: self._paste_to_search())
        self.search_entry.bind('<Control-c>',
                               lambda e: self._copy_from_search())
        self.search_entry.bind('<Control-C>',
                               lambda e: self._copy_from_search())
        self.search_entry.bind('<Control-x>',
                               lambda e: self._cut_from_search())
        self.search_entry.bind('<Control-X>',
                               lambda e: self._cut_from_search())
        self.search_entry.bind('<Control-a>',
                               lambda e: self._select_all_search())
        self.search_entry.bind('<Control-A>',
                               lambda e: self._select_all_search())

        self.btn_clear_search = ttk.Button(search_block,
                                           text='Очистить поиск',
                                           style='Secondary.TButton',
                                           command=self._clear_search)
        self.btn_clear_search.pack(side=tk.LEFT, padx=(8, 0))

        # Прогресс-бар под панелью.
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

    # --- Панель полей поиска ---
    def _build_search_settings_panel(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.X, padx=12, pady=(0, 6))

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.X)

        inner = tk.Frame(panel, bg=COLORS['panel'])
        inner.pack(fill=tk.X, padx=16, pady=10)

        # Заголовок раздела.
        tk.Label(inner, text='Поля поиска',
                 font=FONTS['h2'], fg=COLORS['text'],
                 bg=COLORS['panel']
                 ).pack(anchor='w')

        # --- Ряд 1: режим поиска и массовые кнопки ---
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
            mode_row, text='Снять все',
            style='Small.TButton',
            command=lambda: self._set_all_columns(False),
        )
        self.btn_uncheck_all.pack(side=tk.RIGHT, padx=(4, 0))

        self.btn_check_all = ttk.Button(
            mode_row, text='Отметить все',
            style='Small.TButton',
            command=lambda: self._set_all_columns(True),
        )
        self.btn_check_all.pack(side=tk.RIGHT)

        # --- Ряд 2: чекбоксы колонок - часть "Полей поиска" ---
        self.columns_frame = tk.Frame(inner, bg=COLORS['panel'])
        self.columns_frame.pack(fill=tk.X, pady=(8, 0))

        # --- Разделитель перед "Признаком объекта" ---
        tk.Frame(inner, height=1, bg=COLORS['border']
                 ).pack(fill=tk.X, pady=(12, 0))

        # --- Ряд 3: фильтр по признаку объекта ---
        obj_row = tk.Frame(inner, bg=COLORS['panel'])
        obj_row.pack(fill=tk.X, pady=(10, 0))

        self.lbl_obj = tk.Label(
            obj_row,
            text='Признак объекта:',
            font=FONTS['h2'],
            fg=COLORS['text'],
            bg=COLORS['panel'],
        )
        self.lbl_obj.pack(side=tk.LEFT, padx=(0, 10))

        self.only_combo = ttk.Combobox(
            obj_row,
            textvariable=self.only_label_var,
            values=list(ONLY_LABELS.keys()),
            state='readonly',
            width=24,
            font=FONTS['body'],
            style='Card.TCombobox',
        )
        self.only_combo.pack(side=tk.LEFT)
        self.only_combo.bind(
            '<<ComboboxSelected>>',
            lambda *_: self.apply_filter(),
        )

        self._loading_controls.extend([
            self.rb_all_fields,
            self.rb_selected_fields,
            self.btn_check_all,
            self.btn_uncheck_all,
            self.only_combo,
        ])

    # --- Подсказка рядом с поиском ---
    def _build_search_hint(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(
            fill=tk.X,
            padx=12,
            pady=(0, 6),
            after=self._top_panel_outer,
        )
        self._search_hint_outer = outer
        outer.pack_forget()

        bar = tk.Frame(outer, bg=COLORS['warn_bg'],
                       highlightthickness=1,
                       highlightbackground='#f0d998')
        bar.pack(fill=tk.X)

        inner = tk.Frame(bar, bg=COLORS['warn_bg'])
        inner.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(inner,
                 text='Подсказка:',
                 font=('Segoe UI Semibold', 9), fg='#b8860b',
                 bg=COLORS['warn_bg']).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            inner,
            text='^ФИО - начинается с ФИО   |   '
                 'ФИО$ - заканчивается   |   '
                 '^ФИО$ - точно ФИО   |   '
                 'Ф?О - одна любая буква   |   '
                 'Ф*О - любое число букв',
            font=FONTS['body'], fg=COLORS['warn_fg'],
            bg=COLORS['warn_bg'],
        ).pack(side=tk.LEFT)

    def _update_search_hint(self):
        """Показывает подсказку только во время ввода текста в поиск."""
        if not hasattr(self, '_search_hint_outer'):
            return

        if self.search_var.get().strip():
            self._search_hint_outer.pack(
                fill=tk.X,
                padx=12,
                pady=(0, 6),
                after=self._top_panel_outer,
            )
        else:
            self._search_hint_outer.pack_forget()

    # --- Каркас таблицы ---
    def _build_table_frame(self):
        outer = tk.Frame(self, bg=COLORS['bg'])
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))

        panel = tk.Frame(outer, bg=COLORS['panel'],
                         highlightthickness=1,
                         highlightbackground=COLORS['border'])
        panel.pack(fill=tk.BOTH, expand=True)

        self.table_frame = tk.Frame(panel, bg=COLORS['panel'])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    # --- Статусная строка внизу окна ---
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
            inner,
            textvariable=self.status_var,
            font=FONTS['body'],
            fg=COLORS['text_muted'],
            bg=COLORS['panel'],
            anchor='w',
            justify=tk.LEFT,
        )
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # --- Блокировка элементов до загрузки ---
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

        if loaded:
            self._update_checkboxes_state()
        else:
            for cb in self.column_checkboxes:
                cb.state(['disabled'])
            for btn in (getattr(self, 'btn_check_all', None),
                        getattr(self, 'btn_uncheck_all', None)):
                if btn is not None:
                    btn.state(['disabled'])

    # --- Чекбоксы колонок ---
    def _rebuild_column_checkboxes(self):
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
            cb.pack(side=tk.LEFT, padx=(0, 12))
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
        state = ['!disabled'] if enabled else ['disabled']

        for cb in self.column_checkboxes:
            cb.state(state)

        for btn in (getattr(self, 'btn_check_all', None),
                    getattr(self, 'btn_uncheck_all', None)):
            if btn is not None:
                btn.state(state)

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

    # --- Инструкция, работа с поиском, префиксы ---
    def open_user_help(self, anchor='start'):
        """Открывает инструкцию как неблокирующее окно.

        Повторное нажатие не создаёт новое окно, а активирует уже открытое.
        Основное окно приложения продолжает работать независимо от инструкции.
        """
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
            self._help_window.protocol(
                'WM_DELETE_WINDOW',
                self._close_help_window,
            )
        except tk.TclError:
            pass

    def _close_help_window(self):
        """Закрывает окно инструкции без блокировки основного окна."""
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

    def _paste_to_search(self):
        """Вставляет текст из буфера обмена в поле поиска."""
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
        """Копирует выделенный фрагмент из поля поиска."""
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
        """Вырезает выделенный фрагмент из поля поиска."""
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
        """Ctrl+A - выделяет всё содержимое поля поиска."""
        if not self.search_entry:
            return
        self.search_entry.select_range(0, tk.END)
        self.search_entry.icursor(tk.END)
        return 'break'

    def _clear_search(self):
        self.search_var.set('')
        if self.search_entry and self._data_loaded:
            self.search_entry.focus_set()

    def open_markers_dialog(self):
        dlg = MarkersDialog(self, self.markers)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        self.markers = dlg.result
        try:
            save_markers(self.markers)
        except Exception as e:
            messagebox.showerror('Сохранение',
                                 f'Не удалось сохранить список:\n{e}')
        self._recompute_markers()
        self.apply_filter()
        n_custom = sum(1 for r in self.rows
                       if r.get('ПризнакОбъекта') == CUSTOM_TAG)
        self.status_var.set(
            f'Префиксов: {len(self.markers)}. Кастомных строк: {n_custom}'
        )

    def _recompute_markers(self):
        if not self.rows:
            return
        for r in self.rows:
            r['ПризнакОбъекта'] = (
                CUSTOM_TAG
                if is_custom_name(r.get('ИмяОбъекта', ''), self.markers)
                else STD_TAG
            )

    # --- Построение таблицы ---
    def _rebuild_table(self):
        for w in self.table_frame.winfo_children():
            w.destroy()

        self.tree = ttk.Treeview(
            self.table_frame,
            columns=self.columns,
            show='headings',
            selectmode='browse',
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
        path = filedialog.askopenfilename(
            title='Выберите ConfigDumpInfo.xml',
            filetypes=[('XML files', '*.xml'), ('All files', '*.*')])
        if not path:
            return

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
                    self._progress_safe(pct, f'{pct}%  ({done:,} из {tot:,})'
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

        path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[('CSV', '*.csv')],
            initialfile=name)
        if not path:
            return

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