@echo off 
echo 🖥️ Starting Enhanced OMR Frontend Interface... 
echo. 
echo 🎯 Interface Features: 
echo - Professional evaluator dashboard 
echo - Real-time processing with progress tracking 
echo - Comprehensive results with audit trail 
echo - Quality metrics and compliance monitoring 
echo - Batch processing capabilities 
echo. 
echo 🌐 Web interface will open at: http://localhost:8501 
echo. 
cd /d "%~dp0" 
call omr_env\Scripts\activate.bat 
streamlit run streamlit_app.py 
pause 
