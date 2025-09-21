@echo off
echo 🚀 Setting up Complete OMR System with Bulk Upload and CSV Export...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo ✅ Python found
if exist omr_env rmdir /s /q omr_env
echo 📦 Creating virtual environment...
python -m venv omr_env
call omr_env\Scripts\activate.bat
echo 🔧 Installing packages...
pip install --upgrade pip
pip install -r requirements.txt
echo 📁 Creating directories...
mkdir uploads exports processed_images overlay_images answer_keys
echo 🗄️ Initializing database...
python database_models.py
echo 📝 Creating startup scripts...
echo @echo off > start_backend.bat
echo call omr_env\Scripts\activate.bat >> start_backend.bat
echo python main.py >> start_backend.bat
echo pause >> start_backend.bat
echo @echo off > start_frontend.bat
echo call omr_env\Scripts\activate.bat >> start_frontend.bat
echo streamlit run streamlit_app.py >> start_frontend.bat
echo pause >> start_frontend.bat
echo ✅ Setup completed successfully!
echo 🎯 TO START: 1. Run start_backend.bat 2. Run start_frontend.bat
echo 📖 URLs: Frontend: http://localhost:8501 API: http://localhost:8000
echo 🎪 FEATURES: Bulk upload, Auto IDs, CSV export, Camera capture, Dashboard
pause