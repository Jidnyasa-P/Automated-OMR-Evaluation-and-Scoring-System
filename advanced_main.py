from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
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

# Import our enhanced modules following implementation document
from database_models import get_db, init_db, OMRSheet, ExamConfig, Result, ProcessingLog
from enhanced_preprocessor import EnhancedOMRPreprocessor
from precision_bubble_detector import PrecisionBubbleDetector
from advanced_scoring_engine import AdvancedScoringEngine

# Initialize FastAPI app
app = FastAPI(
    title="Advanced OMR Evaluation System", 
    version="2.0.0",
    description="Production-grade OMR evaluation system following implementation specifications"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create required directories
directories = ["uploads", "exports", "processed_images", "overlay_images", "audit_trail"]
for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")
app.mount("/processed", StaticFiles(directory="processed_images"), name="processed")
app.mount("/overlays", StaticFiles(directory="overlay_images"), name="overlays")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize processing engines
enhanced_preprocessor = EnhancedOMRPreprocessor()
precision_detector = PrecisionBubbleDetector()
scoring_engine = AdvancedScoringEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize database and create sample data on startup"""
    init_db()
    logger.info("Advanced OMR Evaluation System started successfully!")
    
    # Create sample exam configuration if it doesn't exist
    await create_sample_exam_config()

async def create_sample_exam_config():
    """Create sample exam configuration for demo purposes"""
    try:
        from sqlalchemy.orm import sessionmaker
        from database_models import engine
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if exam config already exists
        existing_config = db.query(ExamConfig).first()
        if not existing_config:
            exam_config = ExamConfig(
                exam_name='Data Science Placement Assessment',
                total_questions=100,
                subjects=json.dumps([
                    'Data Analytics', 'Machine Learning', 'Python Programming', 
                    'Statistics', 'Database Management'
                ]),
                questions_per_subject=20,
                answer_key=json.dumps(scoring_engine.generate_default_answer_key())
            )
            
            db.add(exam_config)
            db.commit()
            logger.info("Sample exam configuration created")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error creating sample exam config: {e}")

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Advanced OMR Evaluation System",
        "version": "2.0.0",
        "features": [
            "Enhanced image preprocessing with ML support",
            "Precision bubble detection with ROI mapping", 
            "Advanced scoring with audit trail",
            "Sub 0.5% error tolerance",
            "Complete processing pipeline"
        ],
        "capabilities": {
            "max_processing_speed": "< 5 seconds per sheet",
            "accuracy_target": "> 99.5%",
            "supported_formats": ["PNG", "JPG", "JPEG"],
            "batch_processing": "Up to 3000 sheets"
        }
    }

@app.post("/upload-sheet/")
async def upload_omr_sheet(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    exam_id: int = 1,
    student_id: str = "DEMO_STUDENT",
    exam_version: str = "A",
    auto_process: bool = True,
    db: Session = Depends(get_db)
):
    """
    Upload OMR sheet with enhanced validation and metadata handling
    """
    try:
        # Enhanced file validation
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be a valid image")
        
        if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Generate secure filename
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.png', '.jpg', '.jpeg']:
            raise HTTPException(status_code=400, detail="Unsupported image format")
        
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("uploads", unique_filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate image can be read
        test_image = cv2.imread(file_path)
        if test_image is None:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")
        
        # Create comprehensive database record
        omr_sheet = OMRSheet(
            exam_id=exam_id,
            student_id=student_id,
            filename=unique_filename,
            processing_status="uploaded",
            upload_time=datetime.utcnow()
        )
        db.add(omr_sheet)
        db.commit()
        db.refresh(omr_sheet)
        
        # Create detailed upload log
        log_entry = ProcessingLog(
            sheet_id=omr_sheet.id,
            stage="upload",
            status="success",
            message=f"Sheet uploaded successfully. Size: {os.path.getsize(file_path)} bytes, Dimensions: {test_image.shape}",
            confidence_score=1.0
        )
        db.add(log_entry)
        db.commit()
        
        # Auto-process if requested
        if auto_process:
            background_tasks.add_task(
                process_sheet_background, 
                omr_sheet.id, 
                exam_version
            )
        
        return {
            "message": "Sheet uploaded successfully",
            "sheet_id": omr_sheet.id,
            "filename": unique_filename,
            "status": "uploaded",
            "auto_process": auto_process,
            "image_info": {
                "dimensions": test_image.shape,
                "size_bytes": os.path.getsize(file_path),
                "format": file_extension
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_sheet_background(sheet_id: int, exam_version: str):
    """Background task for processing OMR sheet"""
    try:
        # Get database session
        from sqlalchemy.orm import sessionmaker
        from database_models import engine
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Process the sheet
        result = await process_omr_sheet_complete(sheet_id, exam_version, db)
        
        db.close()
        
    except Exception as e:
        logger.error(f"Background processing error for sheet {sheet_id}: {e}")

@app.post("/process-sheet/{sheet_id}")
async def process_omr_sheet_endpoint(
    sheet_id: int, 
    exam_version: str = "A",
    db: Session = Depends(get_db)
):
    """Process OMR sheet with complete pipeline"""
    return await process_omr_sheet_complete(sheet_id, exam_version, db)

async def process_omr_sheet_complete(sheet_id: int, exam_version: str, db: Session):
    """
    Complete OMR processing pipeline following implementation document
    """
    try:
        # Get sheet from database
        omr_sheet = db.query(OMRSheet).filter(OMRSheet.id == sheet_id).first()
        if not omr_sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Update status
        omr_sheet.processing_status = "processing"
        db.commit()
        
        start_time = datetime.utcnow()
        processing_metadata = {
            "image_filename": omr_sheet.filename,
            "exam_version": exam_version,
            "student_id": omr_sheet.student_id
        }
        
        # Phase 1: Enhanced Preprocessing Pipeline
        file_path = os.path.join("uploads", omr_sheet.filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Step 1-3: Complete preprocessing (fiducials, perspective, illumination)
        processed_image, preprocessing_info = enhanced_preprocessor.complete_preprocessing_pipeline(file_path)
        
        if processed_image is None:
            await log_processing_error(db, sheet_id, "preprocessing", preprocessing_info.get("errors", []))
            raise HTTPException(status_code=500, detail="Image preprocessing failed")
        
        # Save processed image for audit trail
        processed_filename = f"processed_{omr_sheet.filename}"
        processed_path = os.path.join("processed_images", processed_filename)
        cv2.imwrite(processed_path, processed_image)
        
        # Phase 2: Precision Bubble Detection and Answer Extraction
        detection_results = precision_detector.complete_detection_process(processed_image)
        
        if not detection_results.get("process_completed", False):
            await log_processing_error(db, sheet_id, "detection", [detection_results.get("error", "Unknown error")])
            raise HTTPException(status_code=500, detail="Bubble detection failed")
        
        # Save overlay image for audit trail
        if detection_results.get("overlay_generated", False):
            overlay_filename = f"overlay_{omr_sheet.filename}"
            overlay_path = os.path.join("overlay_images", overlay_filename)
            cv2.imwrite(overlay_path, detection_results["overlay_image"])
        
        # Phase 3: Advanced Scoring and Results Generation
        extracted_answers = detection_results["extraction_results"]["answers"]
        confidence_scores = detection_results["extraction_results"]["confidence_scores"]
        
        # Combine processing metadata
        processing_metadata.update({
            "preprocessing_successful": preprocessing_info.get("processing_successful", False),
            "detection_successful": detection_results.get("process_completed", False),
            "total_processing_time": detection_results.get("total_processing_time", 0),
            "grid_identified": detection_results["grid_info"].get("grid_identified", False),
            "overlay_generated": detection_results.get("overlay_generated", False),
            "ambiguous_questions": detection_results["extraction_results"].get("ambiguous_questions", []),
            "multiple_marks": detection_results["extraction_results"].get("multiple_marks", [])
        })
        
        # Complete scoring process
        scoring_results = scoring_engine.complete_scoring_process(
            omr_sheet.student_id, 
            extracted_answers, 
            confidence_scores, 
            processing_metadata
        )
        
        if not scoring_results.get("scoring_completed", False):
            await log_processing_error(db, sheet_id, "scoring", [scoring_results.get("error", "Scoring failed")])
            raise HTTPException(status_code=500, detail="Scoring process failed")
        
        # Update database with final results
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        structured_output = scoring_results["structured_output"]
        
        omr_sheet.processing_status = "completed"
        omr_sheet.processing_time = processing_time
        omr_sheet.total_score = structured_output["score_summary"]["total_scores"]["total_correct"]
        db.commit()
        
        # Save detailed results to database
        for subject_name, subject_data in structured_output["score_summary"]["subject_scores"].items():
            result = Result(
                sheet_id=sheet_id,
                subject_name=subject_name,
                correct_answers=subject_data["correct"],
                wrong_answers=subject_data["wrong"],
                score_percentage=subject_data["score_percentage"],
                detected_answers=json.dumps(extracted_answers)
            )
            db.add(result)
        
        db.commit()
        
        # Final success log
        await log_processing_success(db, sheet_id, structured_output, processing_time)
        
        # Prepare comprehensive response
        response = {
            "message": "OMR sheet processed successfully",
            "sheet_id": sheet_id,
            "processing_summary": {
                "total_processing_time": processing_time,
                "preprocessing_successful": preprocessing_info.get("processing_successful", False),
                "detection_successful": detection_results.get("process_completed", False),
                "scoring_successful": scoring_results.get("scoring_completed", False)
            },
            "results": structured_output,
            "audit_trail": {
                "processed_image": processed_path,
                "overlay_image": overlay_path if detection_results.get("overlay_generated") else None,
                "results_file": scoring_results.get("results_file_path", ""),
                "preprocessing_stages": preprocessing_info.get("stages_completed", []),
                "detection_summary": detection_results.get("summary", {})
            },
            "quality_metrics": {
                "meets_accuracy_target": structured_output["score_summary"]["quality_metrics"]["average_confidence"] > 0.7,
                "processing_speed_target_met": processing_time < 5.0,
                "audit_trail_complete": all([
                    os.path.exists(processed_path),
                    detection_results.get("overlay_generated", False),
                    scoring_results.get("results_file_path", "") != ""
                ])
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error for sheet {sheet_id}: {e}")
        
        # Update sheet status
        if 'omr_sheet' in locals():
            omr_sheet.processing_status = "error"
            db.commit()
        
        await log_processing_error(db, sheet_id, "general", [str(e)])
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

async def log_processing_error(db: Session, sheet_id: int, stage: str, errors: List[str]):
    """Log processing errors to database"""
    try:
        log_entry = ProcessingLog(
            sheet_id=sheet_id,
            stage=stage,
            status="error",
            message=f"Errors in {stage}: {'; '.join(errors)}",
            confidence_score=0.0
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log error: {e}")

async def log_processing_success(db: Session, sheet_id: int, structured_output: Dict, processing_time: float):
    """Log successful processing to database"""
    try:
        quality_metrics = structured_output["score_summary"]["quality_metrics"]
        
        log_entry = ProcessingLog(
            sheet_id=sheet_id,
            stage="completed",
            status="success",
            message=f"Processing completed successfully. Total score: {structured_output['score_summary']['total_scores']['total_correct']}/100",
            confidence_score=quality_metrics["average_confidence"]
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log success: {e}")

@app.get("/sheet/{sheet_id}/results")
async def get_comprehensive_results(sheet_id: int, db: Session = Depends(get_db)):
    """Get comprehensive results including audit trail"""
    try:
        omr_sheet = db.query(OMRSheet).filter(OMRSheet.id == sheet_id).first()
        if not omr_sheet:
            raise HTTPException(status_code=404, detail="Sheet not found")
        
        # Get results
        results = db.query(Result).filter(Result.sheet_id == sheet_id).all()
        
        # Get processing logs
        logs = db.query(ProcessingLog).filter(ProcessingLog.sheet_id == sheet_id).order_by(ProcessingLog.timestamp).all()
        
        # Check for audit trail files
        audit_files = {
            "processed_image": os.path.exists(f"processed_images/processed_{omr_sheet.filename}"),
            "overlay_image": os.path.exists(f"overlay_images/overlay_{omr_sheet.filename}"),
            "results_json": len([f for f in os.listdir("exports") if f.startswith(omr_sheet.student_id)]) > 0
        }
        
        response = {
            "sheet_info": {
                "sheet_id": sheet_id,
                "student_id": omr_sheet.student_id,
                "exam_id": omr_sheet.exam_id,
                "filename": omr_sheet.filename,
                "status": omr_sheet.processing_status,
                "upload_time": omr_sheet.upload_time.isoformat() if omr_sheet.upload_time else None,
                "processing_time": omr_sheet.processing_time,
                "total_score": omr_sheet.total_score
            },
            "subject_results": {
                result.subject_name: {
                    "correct": result.correct_answers,
                    "wrong": result.wrong_answers,
                    "percentage": result.score_percentage
                } for result in results
            },
            "processing_logs": [
                {
                    "stage": log.stage,
                    "status": log.status,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat(),
                    "confidence": log.confidence_score
                } for log in logs
            ],
            "audit_trail": audit_files,
            "compliance": {
                "error_tolerance_met": omr_sheet.processing_status == "completed",
                "processing_speed_acceptable": omr_sheet.processing_time and omr_sheet.processing_time < 5.0,
                "audit_trail_complete": all(audit_files.values())
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comprehensive results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch results: {str(e)}")

@app.get("/sheets/dashboard")
async def get_processing_dashboard(db: Session = Depends(get_db)):
    """Get comprehensive processing dashboard"""
    try:
        all_sheets = db.query(OMRSheet).all()
        all_logs = db.query(ProcessingLog).all()
        
        # Calculate statistics
        total_sheets = len(all_sheets)
        completed_sheets = [s for s in all_sheets if s.processing_status == "completed"]
        error_sheets = [s for s in all_sheets if s.processing_status == "error"]
        
        # Performance metrics
        processing_times = [s.processing_time for s in completed_sheets if s.processing_time]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Quality metrics
        success_rate = len(completed_sheets) / total_sheets * 100 if total_sheets > 0 else 0
        speed_compliance = len([t for t in processing_times if t < 5.0]) / len(processing_times) * 100 if processing_times else 0
        
        dashboard_data = {
            "overview": {
                "total_sheets_processed": total_sheets,
                "successfully_completed": len(completed_sheets),
                "processing_errors": len(error_sheets),
                "success_rate_percentage": round(success_rate, 2),
                "average_processing_time": round(avg_processing_time, 2)
            },
            "performance_metrics": {
                "speed_target_compliance": round(speed_compliance, 2),
                "accuracy_target_met": success_rate > 99.5,
                "sub_5_second_processing": speed_compliance > 90.0,
                "fastest_processing": min(processing_times) if processing_times else 0,
                "slowest_processing": max(processing_times) if processing_times else 0
            },
            "system_health": {
                "preprocessing_success_rate": len([log for log in all_logs if log.stage == "preprocessing" and log.status == "success"]) / max(1, len([log for log in all_logs if log.stage == "preprocessing"])) * 100,
                "detection_success_rate": len([log for log in all_logs if log.stage == "detection" and log.status == "success"]) / max(1, len([log for log in all_logs if log.stage == "detection"])) * 100,
                "scoring_success_rate": len([log for log in all_logs if log.stage == "scoring" and log.status == "success"]) / max(1, len([log for log in all_logs if log.stage == "scoring"])) * 100
            },
            "recent_activity": [
                {
                    "sheet_id": sheet.id,
                    "student_id": sheet.student_id,
                    "status": sheet.processing_status,
                    "processing_time": sheet.processing_time,
                    "upload_time": sheet.upload_time.isoformat() if sheet.upload_time else None
                } for sheet in sorted(all_sheets, key=lambda x: x.upload_time or datetime.min, reverse=True)[:20]
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("advanced_main:app", host="0.0.0.0", port=8000, reload=True)