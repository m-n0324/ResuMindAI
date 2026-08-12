"""
Database Models and Configuration
SQLAlchemy ORM models for storing resume analysis results and history.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, String, Float, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import json
import os

# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumind.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class AnalysisRecord(Base):
    """Store resume analysis results"""
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_text = Column(Text)  # Raw extracted resume text
    ats_score = Column(Float)
    formatting_score = Column(Float)
    keyword_match_score = Column(Float)
    structure_score = Column(Float)
    readability_score = Column(Float)
    
    # Analysis results (stored as JSON)
    strengths = Column(Text)  # JSON array
    weaknesses = Column(Text)  # JSON array
    missing_skills = Column(Text)  # JSON array
    section_issues = Column(Text)  # JSON array
    improved_bullets = Column(Text)  # JSON array of {original, improved}
    summary = Column(Text)
    
    # Job description matching
    jd_text = Column(Text, nullable=True)
    jd_similarity = Column(Float, nullable=True)
    jd_missing_skills = Column(Text, nullable=True)  # JSON array
    matched_skills = Column(Text, nullable=True)  # JSON array
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(String, nullable=True, index=True)

    def to_dict(self):
        """Convert record to dictionary"""
        return {
            "id": self.id,
            "filename": self.filename,
            "ats_score": self.ats_score,
            "score_breakdown": {
                "formatting": self.formatting_score,
                "keyword_match": self.keyword_match_score,
                "structure": self.structure_score,
                "readability": self.readability_score,
            },
            "strengths": json.loads(self.strengths) if self.strengths else [],
            "weaknesses": json.loads(self.weaknesses) if self.weaknesses else [],
            "missing_skills": json.loads(self.missing_skills) if self.missing_skills else [],
            "section_issues": json.loads(self.section_issues) if self.section_issues else [],
            "improved_bullets": json.loads(self.improved_bullets) if self.improved_bullets else [],
            "summary": self.summary,
            "jd_similarity": self.jd_similarity,
            "jd_missing_skills": json.loads(self.jd_missing_skills) if self.jd_missing_skills else [],
            "matched_skills": json.loads(self.matched_skills) if self.matched_skills else [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ResumeVersion(Base):
    """Store resume version history"""
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, index=True)  # Foreign key to AnalysisRecord
    version = Column(Integer)  # Version number
    original_filename = Column(String)
    content = Column(Text)  # Original file content
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    """Store user preferences"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    preferred_job_titles = Column(Text, nullable=True)  # JSON array
    target_industries = Column(Text, nullable=True)  # JSON array
    skill_level = Column(String, nullable=True)  # junior, mid, senior
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database operations
class DatabaseOperations:
    """Helper class for common database operations"""

    @staticmethod
    def create_analysis_record(
        db: Session,
        filename: str,
        original_text: str,
        ats_score: float,
        score_breakdown: dict,
        strengths: list,
        weaknesses: list,
        missing_skills: list,
        section_issues: list,
        improved_bullets: list,
        summary: str,
        jd_text: Optional[str] = None,
        jd_similarity: Optional[float] = None,
        jd_missing_skills: Optional[list] = None,
        matched_skills: Optional[list] = None,
        user_id: Optional[str] = None,
    ) -> AnalysisRecord:
        """Create new analysis record"""
        record = AnalysisRecord(
            filename=filename,
            original_text=original_text,
            ats_score=ats_score,
            formatting_score=score_breakdown.get("formatting", 0),
            keyword_match_score=score_breakdown.get("keyword_match", 0),
            structure_score=score_breakdown.get("structure", 0),
            readability_score=score_breakdown.get("readability", 0),
            strengths=json.dumps(strengths),
            weaknesses=json.dumps(weaknesses),
            missing_skills=json.dumps(missing_skills),
            section_issues=json.dumps(section_issues),
            improved_bullets=json.dumps(improved_bullets),
            summary=summary,
            jd_text=jd_text,
            jd_similarity=jd_similarity,
            jd_missing_skills=json.dumps(jd_missing_skills) if jd_missing_skills else None,
            matched_skills=json.dumps(matched_skills) if matched_skills else None,
            user_id=user_id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_analysis_by_id(db: Session, analysis_id: int) -> Optional[AnalysisRecord]:
        """Get analysis record by ID"""
        return db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()

    @staticmethod
    def get_user_analyses(db: Session, user_id: str, limit: int = 50) -> list:
        """Get all analyses for a user"""
        return (
            db.query(AnalysisRecord)
            .filter(AnalysisRecord.user_id == user_id)
            .order_by(AnalysisRecord.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_analysis(db: Session, analysis_id: int) -> bool:
        """Delete analysis record"""
        record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False

    @staticmethod
    def save_user_settings(
        db: Session,
        user_id: str,
        preferred_job_titles: Optional[list] = None,
        target_industries: Optional[list] = None,
        skill_level: Optional[str] = None,
    ) -> UserSettings:
        """Save or update user settings"""
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
        
        if preferred_job_titles:
            settings.preferred_job_titles = json.dumps(preferred_job_titles)
        if target_industries:
            settings.target_industries = json.dumps(target_industries)
        if skill_level:
            settings.skill_level = skill_level
        
        settings.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def get_user_settings(db: Session, user_id: str) -> Optional[UserSettings]:
        """Get user settings"""
        return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
