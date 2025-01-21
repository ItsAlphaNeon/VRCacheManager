@echo off

if "%1"=="" (
    echo Version number not provided.
    exit /b 1
)

set VERSION=%1

set ICON_PATH=%ICON_PATH%
if "%ICON_PATH%"=="" set ICON_PATH=%~dp0..\resources\vrcm.ico

set SCRIPT_PATH=%SCRIPT_PATH%
if "%SCRIPT_PATH%"=="" set SCRIPT_PATH=%~dp0..\main.py

set OUTPUT_DIR=%~dp0..\dist
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set EXECUTABLE_NAME=%EXECUTABLE_NAME%
if "%EXECUTABLE_NAME%"=="" set EXECUTABLE_NAME=VRCM

set ZIP_NAME=%ZIP_NAME%
if "%ZIP_NAME%"=="" set ZIP_NAME=VRCM_%VERSION%.zip

cd %OUTPUT_DIR%

pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    pip install pyinstaller
)

if not exist %SCRIPT_PATH% (
    echo Script file '%SCRIPT_PATH%' does not exist.
    pause
    exit /b 1
)

pyinstaller --onedir --icon=%ICON_PATH% --name=%EXECUTABLE_NAME% --distpath %OUTPUT_DIR% %SCRIPT_PATH% --noconsole

if not exist "%OUTPUT_DIR%\%EXECUTABLE_NAME%\%EXECUTABLE_NAME%.exe" (
    echo Executable file does not exist.
    pause
    exit /b 1
)

if not exist "..\resources" (
    echo Directory 'resources' does not exist.
    pause
    exit /b 1
)

xcopy "..\resources" "%OUTPUT_DIR%\%EXECUTABLE_NAME%\resources" /E /I /Y

cd %OUTPUT_DIR%
7z a %ZIP_NAME% "%EXECUTABLE_NAME%"

@REM Enhanced cleanup section
cd %OUTPUT_DIR%
if exist "%EXECUTABLE_NAME%" (
    attrib -r -s -h "%EXECUTABLE_NAME%\*" /S /D
    rd /s /q "%EXECUTABLE_NAME%"
)

if exist "%OUTPUT_DIR%\build" rd /s /q "%OUTPUT_DIR%\build"
if exist "%OUTPUT_DIR%\%EXECUTABLE_NAME%.spec" del /q "%OUTPUT_DIR%\%EXECUTABLE_NAME%.spec"

pause
