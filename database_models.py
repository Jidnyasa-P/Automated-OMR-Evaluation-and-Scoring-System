from sqlalchemy import Column, Integer, String, Text, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./omr_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class OMRSheet(Base):
    __tablename__ = "omr_sheets"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, default=1)
    student_id = Column(String, default="DEMO_STUDENT")
    filename = Column(String, unique=True, index=True)
    processing_status = Column(String, default="uploaded")
    upload_time = Column(DateTime, default=datetime.utcnow)
    processing_time = Column(Float, nullable=True)
    total_score = Column(Integer, nullable=True)

class ExamConfig(Base):
    __tablename__ = "exam_configs"
    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String)
    total_questions = Column(Integer, default=100)
    subjects = Column(Text)
    questions_per_subject = Column(Integer, default=20)
    answer_key = Column(Text)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer)
    subject_name = Column(String)
    correct_answers = Column(Integer, default=0)
    wrong_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    detected_answers = Column(Text)

class ProcessingLog(Base):
    __tablename__ = "processing_logs"
    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer)
    stage = Column(String)
    status = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    confidence_score = Column(Float, default=0.0)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()