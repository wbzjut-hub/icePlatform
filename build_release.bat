@echo off
setlocal

echo ==========================================
echo       IcePlatform Windows Builder
echo ==========================================

echo [1/3] Cleaning up previous builds...
cd backend
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
cd ..

echo [2/3] Building Backend (PyInstaller)...
cd backend
pyinstaller icePlatform.spec
if %ERRORLEVEL% NEQ 0 (
    echo Backend build failed!
    pause
    exit /b %ERRORLEVEL%
)
cd ..

echo [3/3] Building Frontend & Electron...
cd my-vue-app
call npm run electron:build
if %ERRORLEVEL% NEQ 0 (
    echo Frontend/Electron build failed!
    pause
    exit /b %ERRORLEVEL%
)
cd ..

echo ==========================================
echo        Build Success! 
echo ==========================================
echo Installer should be in my-vue-app/dist_electron/
pause
