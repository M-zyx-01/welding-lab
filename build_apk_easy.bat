@echo off
echo ========================================
echo 焊接分析实验室 - 一键构建工具
echo One-Click APK Builder for Welding Lab
echo ========================================
echo.

REM Try to find/install JDK
if not exist "%USERPROFILE%\.jdk\jdk-17" (
    echo [Step 1/4] Setting up JDK 17...
    
    REM Check if winget is available
    where winget >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo Installing JDK 17 via winget...
        winget install EclipseAdoptium.Temurin.17.JDK --silent --accept-source-agreements
    ) else (
        echo.
        echo Please install JDK 17 manually:
        echo https://adoptium.net/download/
        echo.
        echo After installing, set JAVA_HOME and run this script again.
        pause
        exit /b 1
    )
    
    REM Find the JDK
    for /d %%i in ("C:\Program Files\Eclipse Adoptium\jdk-17*") do set JAVA_HOME=%%i
    for /d %%i in ("C:\Program Files\Java\jdk-17*") do set JAVA_HOME=%%i
    if "%JAVA_HOME%"=="" (
        echo Could not auto-detect JDK. Please set JAVA_HOME manually.
        pause
        exit /b 1
    )
    echo JDK found at: %JAVA_HOME%
)

echo.
echo [Step 2/4] Installing npm packages...
call npm install @capacitor/core @capacitor/cli @capacitor/android

echo.
echo [Step 3/4] Syncing project...
call npx cap sync android

echo.
echo [Step 4/4] Building APK...
cd android
call gradlew.bat assembleDebug
cd ..

if exist "android\app\build\outputs\apk\debug\app-debug.apk" (
    copy "android\app\build\outputs\apk\debug\app-debug.apk" "WeldingLab.apk" >nul
    echo.
    echo ========================================
    echo SUCCESS! APK created: WeldingLab.apk
    echo ========================================
    echo Copy this file to your Android device and install it.
) else (
    echo Build failed. Check the output above for errors.
)

pause
