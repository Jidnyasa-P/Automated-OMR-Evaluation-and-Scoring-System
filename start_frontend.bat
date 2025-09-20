@echo off 
echo 🖥️ Starting OMR Web Interface... 
echo Web interface will open at: http://localhost:8501 
echo. 
cd /d "%~dp0" 
call omr_env\Scripts\activate.bat 
streamlit run streamlit_app_final.py 
pause 
