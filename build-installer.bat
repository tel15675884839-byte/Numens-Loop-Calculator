@echo off
setlocal

echo ========================================
echo  Loop Calculator - Installer Build
echo ========================================
echo.

cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Cannot enter project directory
    pause
    exit /b 1
)

echo [1/2] Building desktop application files...
cmd /c "build-desktop.bat < NUL"
if errorlevel 1 (
    echo ERROR: Desktop build failed
    pause
    exit /b 1
)
echo.

echo [2/2] Building installer with Inno Setup...
set "ISCC=C:\Users\30741\AppData\Local\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if not exist "%ISCC%" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)
if not exist "%ISCC%" (
    echo ERROR: Inno Setup 6 not found. Install it from https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

if not exist "dist-installer" mkdir "dist-installer"
"%ISCC%" /Q "installer\loop-calculator.iss"
if errorlevel 1 (
    echo ERROR: Installer build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Installer build complete!
echo  Output: dist-installer\LoopCalculatorSetup.exe
echo ========================================
echo.
pause
