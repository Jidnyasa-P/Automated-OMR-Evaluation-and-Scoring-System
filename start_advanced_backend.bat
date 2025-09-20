@echo off 
echo 🚀 Starting Advanced OMR Backend System... 
echo. 
echo 🔧 System Features: 
echo - Enhanced image preprocessing with fiducial detection 
echo - Precision bubble detection with ROI mapping 
echo - ML-assisted ambiguous bubble classification 
echo - Advanced scoring with complete audit trail 
echo - Sub 0.5% error tolerance compliance 
echo. 
echo 🌐 API will be available at: http://localhost:8000 
echo 📚 Documentation at: http://localhost:8000/docs 
echo. 
cd /d "%~dp0" 
call omr_env\Scripts\activate.bat 
python advanced_main.py 
pause 
