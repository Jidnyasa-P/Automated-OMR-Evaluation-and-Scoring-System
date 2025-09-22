# Scanalyze - Complete Automated OMR Processing with Advanced Features

**🎯 Problem Statement**<br>
Manual OMR sheet evaluation is slow, error-prone, and difficult to scale for large exams. Educational institutions need a reliable, automated solution to quickly process answer sheets, minimize human errors, and provide instant analytics.

**🛠️ Approach**<br>
Scanalyze uses AI-powered image processing and machine learning techniques to automatically detect, evaluate, and score OMR sheets. The web-based system features:
- Frontend: Streamlit for interactive UI (upload, camera, results, dashboard)
- Backend: FastAPI for processing, scoring, exports (deployed on Hugging Face Spaces)
- Cloud deployable and accessible for all users

## ✅ Features Implemented

### Core Features
- **Bulk Upload**: Process multiple OMR sheets simultaneously
- **Auto ID Generation**: Automatic student and exam ID assignment  
- **Camera Capture**: Take photos directly through camera
- **Real-time Processing**: Instant scoring and results
- **CSV Export**: Download individual or all results as CSV/Excel
- **Subject-wise Analytics**: Detailed performance breakdown
- **Dashboard**: Comprehensive system metrics and insights
- **Secure Database**: All results stored with complete audit trail

### Technical Features
- **Bulk Summary**: Shows processing summary table after bulk upload
- **Export Endpoints**: `/export/sheet/{id}/csv` and `/export/all/csv`
- **Error Handling**: Comprehensive error handling and user feedback
- **Progress Tracking**: Real-time progress bars during processing

## 🚀 Quick Start

### 1. Setup (One-time)
```batch
setup.bat
```

### 2. Start System
```batch
# Terminal 1:
start_backend.bat

# Terminal 2:
start_frontend.bat
```

### 3. Access
- **Web Interface**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs

## 📱 Usage

### Upload & Process
1. Select multiple OMR images
2. Choose answer key set (A or B)  
3. Click "Process All Sheets"
4. View bulk processing summary
5. Download CSV exports

### Camera Capture
1. Take photo through camera
2. Select answer key set
3. Process and view results
4. Export individual results

### Dashboard & Analytics
1. View system-wide statistics
2. Monitor processing success rates
3. Download all results as CSV
4. Track recent activity

## 📊 Export Features

### Individual Sheet Export
- URL: `/export/sheet/{sheet_id}/csv`
- Contains: Sheet details, subject-wise scores, metadata

### Bulk Export  
- URL: `/export/all/csv`
- Contains: All processed sheets with complete details
- Timestamped filename for organization

## 🔧 System Requirements
- Python 3.8+
- Windows 10/11
- 4GB RAM minimum
- Internet (setup only)

## 🏆 Perfect for
- Educational institutions
- Exam processing centers
- Hackathon demonstrations
- Academic projects

## 📋 Example Usage
-Upload OMR sheet images OR capture using camera
-Select answer key set (A/B)
-Click Process
-View individual and batch results, export CSV

## Try it Online
*Frontend Demo (Hugging Face){https://huggingface.co/spaces/Jidnyasa-Patil/Scanalyze-OMR-System}*

**Status**: ✅ Production Ready
**Version**: 1.0.0 with Bulk Upload & CSV Export