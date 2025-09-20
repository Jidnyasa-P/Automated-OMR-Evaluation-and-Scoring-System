from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sqlite3
import json

Base = declarative_base()

class OMRSheet(Base):
    __tablename__ = "omr_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, nullable=False, index=True)
    student_id = Column(String(50), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, error
    processing_time = Column(Float, nullable=True)
    total_score = Column(Integer, nullable=True)
    
class ExamConfig(Base):
    __tablename__ = "exam_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(255), nullable=False)
    total_questions = Column(Integer, default=100)
    subjects = Column(Text, nullable=False)  # JSON string with subject names
    questions_per_subject = Column(Integer, default=20)
    answer_key = Column(Text, nullable=False)  # JSON string with correct answers
    created_date = Column(DateTime, default=datetime.utcnow)
    
class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, nullable=False, index=True)
    subject_name = Column(String(100), nullable=False)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    detected_answers = Column(Text, nullable=True)  # JSON string with detected answers
    
class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, nullable=False, index=True)
    stage = Column(String(50), nullable=False)  # upload, preprocessing, detection, scoring
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), nullable=False)  # success, error, warning
    message = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)

# Database connection
DATABASE_URL = "sqlite:///./omr_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()