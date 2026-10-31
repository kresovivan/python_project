"""Имена колонок, метки фильтров и общие строковые константы."""

from typing import Dict, List

# Базовые колонки, которые всегда есть в таблице.
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

# Имена файлов и программы.
APP_NAME = 'ConfigDumpParser'
SETTINGS_FILENAME = 'settings.json'
MARKERS_FILENAME = 'config_markers.json'
DEFAULT_MERGED_NAME = 'merged.csv'

# Значения по умолчанию для префиксов и признаков.
DEFAULT_MARKERS = ['ПЛ_']
CUSTOM_TAG = 'Кастомный'
STD_TAG = 'Стандартный'
NONE_TAG = '-'

# Соответствие «человеческого» текста в комбобоксе и внутреннего кода.
ONLY_LABELS: Dict[str, str] = {
    'Все': 'all',
    'Только кастомные': 'custom',
    'Только стандартные': 'std',
}