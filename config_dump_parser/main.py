"""Точка входа приложения."""

from .ui.main_window import MainWindow


def main() -> None:
    """Запускает главное окно и цикл обработки событий."""
    MainWindow().mainloop()


"""py -m config_dump_parser
py -X dev -m config_dump_parser 
cd C:\Python\PythonProject\python_project
Compress-Archive -Path config_dump_parser -DestinationPath config_dump_parser.zip -Forc"""