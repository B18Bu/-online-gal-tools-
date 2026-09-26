@echo off
setlocal
chcp 65001 >nul
set "PYTHON_EXE=D:\Python311\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python was not found at %PYTHON_EXE%.
    echo Update PYTHON_EXE in this file, then run it again.
    exit /b 1
)

"%PYTHON_EXE%" "%~dp0deepseek_wechat_fallback.py" %*
endlocal