@echo off
REM Запускать НА WINDOWS. Соберёт Hush.exe в папке dist.
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller tkinterdnd2
python -m PyInstaller --noconfirm --clean hush.spec
echo.
echo Gotovo: dist\Hush\Hush.exe
pause
