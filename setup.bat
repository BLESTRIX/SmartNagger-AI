@echo off
echo ============================================
echo SmartNaggar AI - Quick Start Script (Windows)
echo ============================================
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)
echo ✓ Python found
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ! Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo [4/6] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✓ Dependencies installed
echo.

REM Create directories
echo [5/6] Creating directories...
if not exist "data\uploads" mkdir data\uploads
if not exist "data\outputs" mkdir data\outputs
if not exist "models" mkdir models
if not exist "assets" mkdir assets
echo ✓ Directories created
echo.

REM Check for secrets
echo [6/6] Checking configuration...
if not exist ".streamlit\secrets.toml" (
    echo ! No secrets file found
    echo.
    echo Creating .streamlit\secrets.toml template...
    if not exist ".streamlit" mkdir .streamlit
    (
        echo # Add your credentials here
        echo SUPABASE_URL = "your_supabase_url"
        echo SUPABASE_KEY = "your_supabase_key"
        echo.
        echo SMTP_SERVER = "smtp.gmail.com"
        echo SMTP_PORT = 587
        echo SENDER_EMAIL = "your_email@gmail.com"
        echo SENDER_PASSWORD = "your_app_password"
    ) > .streamlit\secrets.toml
    echo ✓ Secrets file created
    echo Please edit .streamlit\secrets.toml and add your credentials
) else (
    echo ✓ Secrets file found
)
echo.

echo ============================================
echo 🎉 Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Setup Supabase:
echo    - Create account at supabase.com
echo    - Run setup_supabase.sql in SQL Editor
echo    - Add credentials to .streamlit\secrets.toml
echo.
echo 2. Run the application:
echo    streamlit run app.py
echo.
echo 3. Access admin dashboard:
echo    streamlit run pages\admin.py
echo    Credentials: admin / admin123
echo.
echo For more help, see README.md and DEPLOYMENT.md
echo ============================================
echo.
pause