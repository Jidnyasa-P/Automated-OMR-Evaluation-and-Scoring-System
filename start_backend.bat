@echo off 
echo 🚀 Starting OMR Backend Server... 
echo Backend will be available at: http://localhost:8000 
echo API Docs at: http://localhost:8000/docs 
echo. 
cd /d "%~dp0" 
call omr_env\Scripts\activate.bat 
python main.py 
pause 
