@echo off
echo ========================================
echo 焊接分析实验室 - Android APK Builder
echo Welding Intelligence Lab
echo ========================================
echo.

REM Check Java
java -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Java JDK 17+ not found!
    echo Please install JDK from: https://adoptium.net/download/
    echo Or run: winget install EclipseAdoptium.Temurin.17.JDK
    pause
    exit /b 1
)

REM Set JAVA_HOME if needed
if "%JAVA_HOME%"=="" (
    for /f "tokens=*" %%i in ('where java') do set JAVA_PATH=%%i
    echo JAVA_HOME not set, using system Java at %JAVA_PATH%
)

REM Check Android SDK
if "%ANDROID_HOME%"=="" if "%ANDROID_SDK_ROOT%"=="" (
    echo [INFO] ANDROID_HOME not set.
    echo Capacitor will try to find Android SDK automatically.
    echo If build fails, set ANDROID_HOME to your Android SDK location.
)

echo.
echo [1/3] Installing npm dependencies...
call npm install @capacitor/core @capacitor/cli @capacitor/android
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm install failed
    pause
    exit /b 1
)

echo.
echo [2/3] Syncing web assets to Android project...
call npx cap sync android
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] cap sync failed
    pause
    exit /b 1
)

echo.
echo [3/3] Building APK...
cd android
call gradlew.bat assembleDebug
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed. Common fixes:
    echo   1. Install Android SDK Command-line Tools from: https://developer.android.com/studio
    echo   2. Set ANDROID_HOME environment variable
    echo   3. Run: sdkmanager "platforms;android-34" "build-tools;34.0.0"
    cd ..
    pause
    exit /b 1
)
cd ..

set APK_PATH=android\app\build\outputs\apk\debug\app-debug.apk
if exist "%APK_PATH%" (
    copy "%APK_PATH%" "WeldingLab-app-debug.apk" >nul
    echo.
    echo ========================================
    echo BUILD SUCCESS!
    echo APK: WeldingLab-app-debug.apk
    echo Size: 
    for %%A in ("WeldingLab-app-debug.apk") do echo %%~zA bytes
    echo ========================================
    echo.
    echo Transfer this APK to your Android phone and install it.
    echo Note: This is a debug build. For release, use gradlew.bat assembleRelease
) else (
    echo [ERROR] APK not found at %APK_PATH%
)

pause
