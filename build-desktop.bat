@echo off
setlocal

echo ========================================
echo  Loop Calculator - Desktop Build
echo ========================================
echo.

cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Cannot enter project directory
    pause
    exit /b 1
)

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install runtime dependencies
    pause
    exit /b 1
)
pip install -r requirements-build.txt
if errorlevel 1 (
    echo ERROR: Failed to install build dependencies
    pause
    exit /b 1
)
echo      Python dependencies OK.
echo.

echo [2/4] Building local SQLite backend sidecar...
pyinstaller --clean --noconfirm loop_calculator_backend.spec
if errorlevel 1 (
    echo ERROR: Backend sidecar build failed
    pause
    exit /b 1
)
echo      Backend sidecar OK.
echo.

cd /d "%~dp0frontend"
if errorlevel 1 (
    echo ERROR: Cannot enter frontend directory
    pause
    exit /b 1
)

echo [3/4] Installing frontend dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Frontend dependency install failed
    pause
    exit /b 1
)
echo      Dependencies OK.
echo.

echo [4/4] Building Tauri desktop app...
call npm run desktop:build
if errorlevel 1 (
    echo ERROR: Tauri desktop build failed
    pause
    exit /b 1
)

cd /d "%~dp0"
if not exist "dist-desktop" mkdir "dist-desktop"
copy /Y "frontend\src-tauri\target\release\loop-calculator-desktop.exe" "dist-desktop\LoopCalculatorDesktop.exe" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy desktop executable
    pause
    exit /b 1
)
copy /Y "dist\LoopCalculatorBackend.exe" "dist-desktop\LoopCalculatorBackend.exe" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy backend sidecar
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Desktop build complete!
echo  Output: dist-desktop\LoopCalculatorDesktop.exe
echo          dist-desktop\LoopCalculatorBackend.exe
echo ========================================
echo.
pause
