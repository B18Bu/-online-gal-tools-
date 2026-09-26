@echo off
setlocal
set "PYTHON_EXE=D:\Python311\python.exe"
set "OUTPUT_DIR=%~dp0outputs"

if not exist "%PYTHON_EXE%" (
    echo Python was not found at %PYTHON_EXE%.
    exit /b 1
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name EarthOnlineGalToolkit --icon "%~dp0earth_online_icon.ico" --add-data "%~dp0earth_online_icon.png;." --distpath "%OUTPUT_DIR%" --workpath "%~dp0build" --specpath "%~dp0build" --hidden-import keyboard --hidden-import pyperclip --hidden-import pyautogui --hidden-import numpy --collect-all rapidocr_onnxruntime "%~dp0earth_online_gal_gui.py"
endlocal