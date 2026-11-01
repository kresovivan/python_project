# Все Python-файлы проекта без синтаксических ошибок.
#
# Раньше файлы компилировались во временную папку, и Windows иногда не
# успевала её удалить ("Папка не пуста"), тест падал без причины.
# Встроенная функция compile() проверяет код в памяти, файлов не создаёт.

import unittest

from tests.support import ROOT

FOLDERS = (
    "core",
    "gui",
    "gui/pages",
    "tools",
    "tests",
    "tests/unit",
    "tests/gui",
    "tests/system",
    "tests/manual",
)


class SourceTests(unittest.TestCase):
    def test_every_python_file_compiles(self):
        files = [*ROOT.glob("*.py")]
        for folder in FOLDERS:
            files.extend((ROOT / folder).glob("*.py"))

        for path in sorted(files):
            with self.subTest(file=str(path.relative_to(ROOT))):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")


if __name__ == "__main__":
    unittest.main()
