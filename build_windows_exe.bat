@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "BUILD_DIR=%ROOT%build"
set "LOG_PATH=%BUILD_DIR%\build_windows_exe.log"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"

call :main > "%LOG_PATH%" 2>&1
set "BUILD_EXIT_CODE=%ERRORLEVEL%"
type "%LOG_PATH%"
echo.
echo Build log saved to:
echo %LOG_PATH%
if not "%BUILD_EXIT_CODE%"=="0" (
    echo.
    echo Build failed. If you need help, copy the last lines from the log above.
)
echo.
pause
exit /b %BUILD_EXIT_CODE%

:main
setlocal EnableExtensions

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-build"
set "BUILD_DIR=%ROOT%build"
set "PYINSTALLER_WORK=%BUILD_DIR%\pyinstaller-work"
set "LAUNCHER=%BUILD_DIR%\pyinstaller_launcher.py"
set "DIST_DIR=%ROOT%dist"
set "EXE_PATH=%DIST_DIR%\Proofread App.exe"
set "PYTHON_CMD="

pushd "%ROOT%" >nul
if errorlevel 1 (
    echo Could not open project folder: %ROOT%
    exit /b 1
)

echo Project folder: %ROOT%
echo Expected EXE: %EXE_PATH%
echo.

call :find_python
if errorlevel 1 (
    popd >nul
    exit /b 1
)

echo Using Python command: %PYTHON_CMD%
%PYTHON_CMD% --version
if errorlevel 1 goto build_failed

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating build virtual environment...
    %PYTHON_CMD% -m venv "%VENV%"
    if errorlevel 1 goto build_failed
)

echo Installing PyInstaller in the build virtual environment...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto build_failed

echo Writing PyInstaller launcher...
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
    echo.
    echo Searching for any Proofread App.exe file under the project folder...
    dir /s /b "%ROOT%Proofread App.exe" 2>nul
    echo.
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

:find_python
python -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

py -3 -c "import sys; raise SystemExit(sys.version_info < (3, 10))" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

echo Python 3.10 or newer is required on the build machine.
echo Install Python from https://www.python.org/downloads/windows/ and enable "Add python.exe to PATH".
echo The generated EXE will not require Python on the machine that runs it.
exit /b 1

:build_failed
echo.
echo EXE build failed. Read the error message above, then run this script again from the project folder.
echo You do not need to run this script as Administrator.
popd >nul
exit /b 1
