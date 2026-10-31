"""GUI-парсер ConfigDumpInfo.xml (метаданные 1С).

Пакет разбит по слоям:
  constants - цвета, шрифты, колонки, переводы;
  storage   - пути, settings.json, config_markers.json;
  core      - парсер XML, поиск, слияние CSV (без Tkinter);
  ui        - стили, виджеты, главное окно;
  dialogs   - диалоговые окна.
"""

__version__ = '1.0.0'
__all__ = ['__version__']