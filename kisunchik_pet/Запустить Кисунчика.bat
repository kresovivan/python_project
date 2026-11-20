@echo off
rem Запуск Кисунчика без чёрного окна консоли.
rem Путь к pythonw - это Python, встроенный в Kimi, он уже умеет PIL и numpy.
start "" "C:\Users\kresovivan\AppData\Roaming\kimi-desktop\daimon-share\daimon\runtime\python\.venv\Scripts\pythonw.exe" "%~dp0run.py"
