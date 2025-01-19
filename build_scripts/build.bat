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
if "%EXECUTABLE_NAME%"=="" set EXECUTABLE_NAME=VRCM.exe

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

pyinstaller -F --icon=%ICON_PATH% --noconsole --name=%EXECUTABLE_NAME:~0,-4% --distpath %OUTPUT_DIR% %SCRIPT_PATH%

if not exist "%OUTPUT_DIR%\%EXECUTABLE_NAME%" (
    echo File '%EXECUTABLE_NAME%' does not exist.
    pause
    exit /b 1
)

if not exist "..\resources" (
    echo Directory 'resources' does not exist.
    pause
    exit /b 1
)

xcopy "..\resources" "resources" /E /I /Y

7z a %ZIP_NAME% %EXECUTABLE_NAME% resources

@REM cleanup
if exist "%OUTPUT_DIR%\build" rd /s /q "%OUTPUT_DIR%\build"
if exist "%OUTPUT_DIR%\%EXECUTABLE_NAME%" del /q "%OUTPUT_DIR%\%EXECUTABLE_NAME%"
if exist "%OUTPUT_DIR%\VRCM.spec" del /q "%OUTPUT_DIR%\VRCM.spec"
if exist %OUTPUT_DIR%\resources rd /s /q %OUTPUT_DIR%\resources

pause