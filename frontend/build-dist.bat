@echo off
title EduLedger AI Frontend Compiler
echo ==================================================
echo   EduLedger AI Frontend Production Builder
echo ==================================================
echo.

:: Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating a default one.
    echo VITE_API_URL=http://localhost:5000 > .env
)

echo [1/3] Compiling React and Tailwind assets...
call npm run build

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed! Check npm compile errors above.
    pause
    exit /b %ERRORLEVEL%
)

echo [2/3] Preparing Downloads folder...
set DEST_DIR=C:\Users\Vella\Downloads\eduledger-frontend-dist
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
)

echo [3/3] Copying built assets and Netlify configs...
:: Copy dist folder content
xcopy /E /Y /I dist\* "%DEST_DIR%" > nul
:: Copy netlify.toml
copy /Y netlify.toml "%DEST_DIR%\netlify.toml" > nul

echo.
echo ==================================================
echo   SUCCESS: Build folder ready for Netlify!
echo ==================================================
echo Path: %DEST_DIR%
echo.
echo You can now drag and drop the folder 'eduledger-frontend-dist' 
echo from your Downloads folder onto the Netlify Drop dashboard.
echo.
pause
