@echo off
REM Builds a standalone JARVIS.exe (no Python needed on the target PC). Output: dist\JARVIS\JARVIS.exe
pip install pyinstaller
pyinstaller --noconfirm --windowed --name JARVIS ^
  --add-data "jarvis\assets;jarvis\assets" ^
  main.py
echo.
echo Done. Run dist\JARVIS\JARVIS.exe
pause
