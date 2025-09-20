from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil
import uuid
from datetime import datetime
import json
import asyncio
from typing import Dict, List, Optional
import logging
import cv2
import numpy as np

# Import our custom modules
from database_models import get_db, init_db, OMRSheet, ExamConfig, Result, ProcessingLog

# Initialize FastAPI app
app = FastAPI(title="OMR Evaluation System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("exports", exist_ok=True)
os.makedirs("processed_images", exist_ok=True)
os.makedirs("overlay_images", exist_ok=True)
os.makedirs("answer_keys", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("OMR Evaluation System started successfully!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "OMR Evaluation System API", "version": "1.0.0"}

@app.post("/upload-sheet/")
async def upload_omr_sheet(
    file: UploadFile = File(...),
    exam_version: str = Form("A"),
    student_id: str = Form("DEMO_STUDENT"),
    exam_id: int = Form(1),
    db: Session = Depends(get_db)
):
    """Upload and process an OMR sheet"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("uploads", unique_filename)

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create database record
        omr_sheet = OMRSheet(
            exam_id=exam_id,
            student_id=student_id,
            filename=unique_filename,
            processing_status="uploaded"
        )
        db.add(omr_sheet)
        db.commit()
        db.refresh(omr_sheet)

        # Log upload
        log_entry = ProcessingLog(
            sheet_id=omr_sheet.id,
            stage="upload",
            status="success",
            message="Sheet uploaded successfully"
        )
        db.add(log_entry)
        db.commit()

        return {
            "message": "Sheet uploaded successfully",
            "sheet_id": omr_sheet.id,
            "filename": unique_filename,
            "status": "uploaded"
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/process-sheet/{sheet_id}")
async def process_omr_sheet(
    sheet_id: int, 
    exam_version: str = Query("A"),
    db: Session = Depends(get_db)
):
    """Process an uploaded OMR sheet"""
    try:
        # Get sheet from database
        omr_sheet = db.query(OMRSheet).filter(OMRSheet.id == sheet_id).first()
        if not omr_sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")

        # Update status to processing
        omr_sheet.processing_status = "processing"
        db.commit()

        # Simulate processing (replace with actual processing logic)
        import time
        time.sleep(2)  # Simulate processing time

        # Create sample results
        subjects = ["Data Analytics", "Machine Learning", "Python Programming", 
                   "Statistics", "Database Management"]

        subject_scores = {}
        total_correct = 0

        for i, subject in enumerate(subjects):
            # Generate sample scores
            correct = np.random.randint(15, 20)  # 15-19 correct out of 20
            wrong = 20 - correct
            score_percentage = (correct / 20) * 100

            subject_scores[subject] = {
                "correct": correct,
                "wrong": wrong,
                "blank": 0,
                "score_percentage": round(score_percentage, 2),
                "total_questions": 20
            }
            total_correct += correct

        total_percentage = (total_correct / 100) * 100

        # Update sheet record
        omr_sheet.processing_status = "completed"
        omr_sheet.processing_time = 2.0
        omr_sheet.total_score = total_correct
        db.commit()

        # Save results to database
        for subject_name, scores in subject_scores.items():
            result = Result(
                sheet_id=sheet_id,
                subject_name=subject_name,
                correct_answers=scores["correct"],
                wrong_answers=scores["wrong"],
                score_percentage=scores["score_percentage"],
                detected_answers=json.dumps({})
            )
            db.add(result)

        db.commit()

        # Log successful processing
        log_entry = ProcessingLog(
            sheet_id=sheet_id,
            stage="completed",
            status="success",
            message="Sheet processed successfully",
            confidence_score=0.95
        )
        db.add(log_entry)
        db.commit()

        return {
            "message": "Sheet processed successfully",
            "sheet_id": sheet_id,
            "processing_time": 2.0,
            "total_score": total_correct,
            "total_questions": 100,
            "percentage": round(total_percentage, 2),
            "subject_scores": subject_scores
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {e}")

        # Update sheet status to error
        omr_sheet = db.query(OMRSheet).filter(OMRSheet.id == sheet_id).first()
        if omr_sheet:
            omr_sheet.processing_status = "error"
            db.commit()

        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/sheet/{sheet_id}/results")
async def get_sheet_results(sheet_id: int, db: Session = Depends(get_db)):
    """Get results for a specific sheet"""
    try:
        # Get sheet
        omr_sheet = db.query(OMRSheet).filter(OMRSheet.id == sheet_id).first()
        if not omr_sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")

        # Get results
        results = db.query(Result).filter(Result.sheet_id == sheet_id).all()

        # Format response
        subject_results = {}
        for result in results:
            subject_results[result.subject_name] = {
                "correct": result.correct_answers,
                "wrong": result.wrong_answers,
                "percentage": result.score_percentage
            }

        return {
            "sheet_id": sheet_id,
            "student_id": omr_sheet.student_id,
            "status": omr_sheet.processing_status,
            "total_score": omr_sheet.total_score,
            "processing_time": omr_sheet.processing_time,
            "subject_results": subject_results,
            "upload_time": omr_sheet.upload_time.isoformat() if omr_sheet.upload_time else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch results: {str(e)}")

@app.get("/sheets/")
async def list_sheets(db: Session = Depends(get_db)):
    """Get list of all processed sheets"""
    try:
        sheets = db.query(OMRSheet).order_by(OMRSheet.upload_time.desc()).all()

        sheet_list = []
        for sheet in sheets:
            sheet_list.append({
                "id": sheet.id,
                "student_id": sheet.student_id,
                "exam_id": sheet.exam_id,
                "filename": sheet.filename,
                "status": sheet.processing_status,
                "total_score": sheet.total_score,
                "upload_time": sheet.upload_time.isoformat() if sheet.upload_time else None,
                "processing_time": sheet.processing_time
            })

        return {"sheets": sheet_list}

    except Exception as e:
        logger.error(f"Error listing sheets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sheets: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)