import py_compile
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT


class SourceTests(unittest.TestCase):
    def test_all_source_files_compile(self):
        files = sorted(
            [
                *ROOT.glob("*.py"),
                *ROOT.glob("core/*.py"),
                *ROOT.glob("gui/*.py"),
                *ROOT.glob("gui/pages/*.py"),
                *ROOT.glob("tools/*.py"),
                *ROOT.glob("tests/*.py"),
            ]
        )
        self.assertGreater(len(files), 30)
        with tempfile.TemporaryDirectory(prefix="efp_compile_") as tmp:
            for index, path in enumerate(files):
                with self.subTest(path=path.relative_to(ROOT)):
                    py_compile.compile(str(path), cfile=str(Path(tmp) / f"{index}.pyc"), doraise=True)

    def test_application_imports(self):
        import gui.app

        self.assertEqual(len(gui.app.PAGE_CLASSES), 7)


if __name__ == "__main__":
    unittest.main()
