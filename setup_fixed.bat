@echo off
:: Complete OMR System Setup for Windows (Fixed Version)
echo 🚀 Setting up Complete OMR Evaluation System (FIXED)...
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
python --version

:: Clean previous installation
if exist omr_env (
    echo 🧹 Removing existing environment...
    rmdir /s /q omr_env
)

:: Create fresh virtual environment
echo 📦 Creating virtual environment...
python -m venv omr_env
call omr_env\Scripts\activate.bat

:: Upgrade pip and install build tools
echo 🔧 Upgrading pip and installing build tools...
python -m pip install --upgrade pip setuptools wheel

:: Install packages one by one for better error handling
echo 📚 Installing packages...
pip install fastapi
pip install "uvicorn[standard]"
pip install python-multipart
pip install sqlalchemy
pip install pillow
pip install opencv-python
pip install numpy
pip install pandas
pip install scikit-learn
pip install streamlit
pip install pydantic
pip install plotly
pip install requests

:: Create directories
echo 📁 Creating project directories...
if not exist uploads mkdir uploads
if not exist exports mkdir exports
if not exist processed_images mkdir processed_images
if not exist overlay_images mkdir overlay_images
if not exist answer_keys mkdir answer_keys

:: Initialize database first
echo 🗄️ Initializing database...
python database_models.py

:: Create startup scripts with proper names
echo 📝 Creating startup scripts...

echo @echo off > start_backend.bat
echo echo 🚀 Starting OMR Backend Server... >> start_backend.bat
echo echo Backend will be available at: http://localhost:8000 >> start_backend.bat
echo echo API Docs at: http://localhost:8000/docs >> start_backend.bat
echo echo. >> start_backend.bat
echo cd /d "%%~dp0" >> start_backend.bat
echo call omr_env\Scripts\activate.bat >> start_backend.bat
echo python main.py >> start_backend.bat
echo pause >> start_backend.bat

echo @echo off > start_frontend.bat
echo echo 🖥️ Starting OMR Web Interface... >> start_frontend.bat
echo echo Web interface will open at: http://localhost:8501 >> start_frontend.bat
echo echo. >> start_frontend.bat
echo cd /d "%%~dp0" >> start_frontend.bat
echo call omr_env\Scripts\activate.bat >> start_frontend.bat
echo streamlit run streamlit_app_final.py >> start_frontend.bat
echo pause >> start_frontend.bat

:: Create test script
echo @echo off > test_system.bat
echo echo 🧪 Testing OMR System... >> test_system.bat
echo cd /d "%%~dp0" >> test_system.bat
echo call omr_env\Scripts\activate.bat >> test_system.bat
echo echo Testing imports... >> test_system.bat
echo python -c "import fastapi, streamlit, requests, pandas, plotly; print('✅ All imports successful')" >> test_system.bat
echo echo Testing backend connection... >> test_system.bat
echo python -c "import requests; r=requests.get('http://localhost:8000/', timeout=2); print('✅ Backend responsive' if r.status_code==200 else '❌ Backend not running')" >> test_system.bat
echo pause >> test_system.bat

echo.
echo ✅ FIXED SETUP COMPLETED SUCCESSFULLY!
echo.
echo 🛠️ WHAT WAS FIXED:
echo ✅ Streamlit file upload attribute error
echo ✅ Camera capture functionality  
echo ✅ Proper error handling and timeouts
echo ✅ Better progress indicators
echo ✅ Backend connectivity checks
echo.
echo 🎯 TO START THE SYSTEM:
echo 1. Backend: double-click start_backend.bat
echo 2. Frontend: double-click start_frontend.bat (in new window)
echo 3. Test: double-click test_system.bat (optional)
echo.
echo 📖 ACCESS URLS:
echo - Web Interface: http://localhost:8501
echo - API Documentation: http://localhost:8000/docs
echo.
echo 🎪 FEATURES READY:
echo ✅ Fixed file upload and processing
echo ✅ Working camera capture functionality  
echo ✅ Real-time results and scoring
echo ✅ Subject-wise analytics dashboard
echo ✅ Comprehensive error handling
echo.

pause