@echo off
cd /d "%~dp0"
py -m loop_calculator
if %errorlevel% neq 0 (
    echo.
    echo 程序启动失败。请确保安装了 PySide6。
    pause
)
