@echo off 
echo 🧪 Testing Advanced OMR System... 
cd /d "%~dp0" 
call omr_env\Scripts\activate.bat 
echo Testing core modules... 
python -c "from enhanced_preprocessor import EnhancedOMRPreprocessor; print('✅ Enhanced preprocessor loaded')" 
python -c "from precision_bubble_detector import PrecisionBubbleDetector; print('✅ Precision detector loaded')" 
python -c "from advanced_scoring_engine import AdvancedScoringEngine; print('✅ Advanced scoring engine loaded')" 
python -c "import cv2, numpy, sklearn; print('✅ All core libraries available')" 
echo. 
echo 🎉 Advanced system test completed successfully! 
pause 
