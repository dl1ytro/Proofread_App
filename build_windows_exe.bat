@echo off
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-build"
set "BUILD_DIR=%ROOT%build"
set "PYINSTALLER_WORK=%BUILD_DIR%\pyinstaller-work"
set "LAUNCHER=%BUILD_DIR%\pyinstaller_launcher.py"
set "DIST_DIR=%ROOT%dist"
set "EXE_PATH=%DIST_DIR%\Proofread App.exe"

pushd "%ROOT%" >nul
if errorlevel 1 (
    echo Could not open project folder: %ROOT%
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo Python is required to build the EXE. Install Python 3.10 or newer on the build machine.
    popd >nul
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating build virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 goto build_failed
)

echo Installing PyInstaller in the build virtual environment...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto build_failed

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
(
    echo from proofread_app.ui import main
    echo.
    echo if __name__ == "__main__":
    echo     main^(^)
) > "%LAUNCHER%"

echo Building %EXE_PATH% ...
"%VENV%\Scripts\python.exe" -m PyInstaller ^
    --clean ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Proofread App" ^
    --paths "%ROOT%src" ^
    --distpath "%DIST_DIR%" ^
    --workpath "%PYINSTALLER_WORK%" ^
    --specpath "%BUILD_DIR%" ^
    "%LAUNCHER%"
if errorlevel 1 goto build_failed

if not exist "%EXE_PATH%" (
    echo Build finished, but the expected EXE was not found:
    echo %EXE_PATH%
    echo Check the PyInstaller output above for warnings or errors.
    popd >nul
    exit /b 1
)

echo.
echo Built EXE:
echo %EXE_PATH%
echo.
echo Copy that EXE to the Windows machine where you want to run the app.
echo Ollama must still be installed and running on that machine.
popd >nul
exit /b 0

:build_failed
echo.
echo EXE build failed. Read the error message above, then run this script again from the project folder.
echo You do not need to run this script as Administrator.
popd >nul
exit /b 1
