@echo off
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-build"
set "LAUNCHER=%ROOT%build\pyinstaller_launcher.py"

where python >nul 2>nul
if errorlevel 1 (
    echo Python is required to build the EXE. Install Python 3.10 or newer on the build machine.
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    python -m venv "%VENV%"
    if errorlevel 1 exit /b 1
)

"%VENV%\Scripts\python.exe" -m pip install --upgrade pip pyinstaller
if errorlevel 1 exit /b 1

if not exist "%ROOT%build" mkdir "%ROOT%build"
(
    echo from proofread_app.ui import main
    echo.
    echo if __name__ == "__main__":
    echo     main^(^)
) > "%LAUNCHER%"

"%VENV%\Scripts\python.exe" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Proofread App" ^
    --paths "%ROOT%src" ^
    "%LAUNCHER%"
if errorlevel 1 exit /b 1

echo.
echo Built EXE:
echo %ROOT%dist\Proofread App.exe
echo.
echo Copy that EXE to the Windows machine where you want to run the app.
echo Ollama must still be installed and running on that machine.
