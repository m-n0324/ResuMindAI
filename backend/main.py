"""
FastAPI Backend Application
Main entry point for ResuMind AI resume analysis API.
Endpoints for resume upload, analysis, and results retrieval.
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.parser import ResumeParser
from backend.llm import LLMAnalyzer
from backend.embeddings import SimpleEmbedding, SkillExtractor
from backend.skills import SkillCategoryExtractor, SkillCategory
from backend.report import ReportGenerator
from backend.db import init_db, get_db, DatabaseOperations, AnalysisRecord

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="ResuMind AI API",
    description="Advanced Resume Intelligence & ATS Optimizer",
    version="1.0.0"
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")


# ============ Request/Response Models ============

class AnalysisResponse(BaseModel):
    """Analysis result response"""
    id: int
    ats_score: float
    score_breakdown: dict
    strengths: list
    weaknesses: list
    missing_skills: list
    section_issues: list
    improved_bullets: list
    summary: str
    jd_similarity: Optional[float]
    jd_missing_skills: Optional[list]
    matched_skills: Optional[list]
    created_at: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    database: str


# ============ API Endpoints ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="SQLite"
    )


@app.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Analyze resume and generate ATS score, feedback, and improvements.
    
    Args:
        file: Resume file (PDF, DOCX, or TXT)
        job_description: Optional job description for JD matching
        user_id: Optional user identifier for history tracking
        
    Returns:
        Analysis results with scores and recommendations
    """
    try:
        # Validate file type
        allowed_types = [".pdf", ".docx", ".txt"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_types):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")
        
        logger.info(f"📄 Processing resume: {file.filename}")
        
        # Parse resume
        try:
            resume_text = ResumeParser.parse_from_bytes(file_content, file.filename)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse resume: {str(e)}")
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="No text extracted from resume")
        
        logger.info(f"✅ Resume parsed successfully ({len(resume_text)} chars)")
        
        # Analyze using LLM
        try:
            llm_analyzer = LLMAnalyzer()
            analysis = llm_analyzer.analyze_resume(resume_text, job_description)
            logger.info(f"✅ LLM analysis complete - ATS Score: {analysis.ats_score}")
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
        
        # Calculate JD similarity if provided
        jd_similarity = None
        jd_missing_skills = None
        matched_skills = None
        
        if job_description:
            try:
                jd_similarity = SimpleEmbedding.compute_similarity(resume_text, job_description)
                gap_analysis = SkillExtractor.find_missing_skills(resume_text, job_description)
                matched_skills = gap_analysis[0]
                jd_missing_skills = gap_analysis[1]
                logger.info(f"✅ JD matching complete - Similarity: {jd_similarity:.1f}%")
            except Exception as e:
                logger.warning(f"⚠️ JD matching failed: {str(e)}")
        
        # Shape the response payload before touching the database, so a DB
        # failure can never cost the user an analysis that already succeeded.
        score_breakdown = {
            "formatting": analysis.score_breakdown.formatting,
            "keyword_match": analysis.score_breakdown.keyword_match,
            "structure": analysis.score_breakdown.structure,
            "readability": analysis.score_breakdown.readability,
        }

        improved_bullets_data = [
            {"original": b.original, "improved": b.improved}
            for b in analysis.improved_bullets
        ]

        # Save to database
        db_record = None
        try:
            db_record = DatabaseOperations.create_analysis_record(
                db=db,
                filename=file.filename,
                original_text=resume_text,
                ats_score=analysis.ats_score,
                score_breakdown=score_breakdown,
                strengths=analysis.strengths,
                weaknesses=analysis.weaknesses,
                missing_skills=analysis.missing_skills,
                section_issues=analysis.section_issues,
                improved_bullets=improved_bullets_data,
                summary=analysis.summary,
                jd_text=job_description,
                jd_similarity=jd_similarity,
                jd_missing_skills=jd_missing_skills,
                matched_skills=matched_skills,
                user_id=user_id,
            )
            logger.info(f"✅ Analysis saved to database (ID: {db_record.id})")
        except Exception as e:
            logger.error(f"❌ Database save failed: {str(e)}")
            # Return analysis even if DB save fails
        
        # Return response
        return {
            "id": db_record.id if db_record else None,
            "ats_score": analysis.ats_score,
            "score_breakdown": score_breakdown,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "missing_skills": analysis.missing_skills,
            "section_issues": analysis.section_issues,
            "improved_bullets": improved_bullets_data,
            "summary": analysis.summary,
            "jd_similarity": jd_similarity,
            "jd_missing_skills": jd_missing_skills,
            "matched_skills": matched_skills,
            "created_at": db_record.created_at.isoformat() if db_record else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/history/{user_id}")
async def get_user_history(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get analysis history for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of records to return
        
    Returns:
        List of past analyses
    """
    try:
        records = DatabaseOperations.get_user_analyses(db, user_id, limit)
        return [record.to_dict() for record in records]
    except Exception as e:
        logger.error(f"❌ History fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@app.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get specific analysis result.
    
    Args:
        analysis_id: Analysis record ID
        
    Returns:
        Analysis details
    """
    try:
        record = DatabaseOperations.get_analysis_by_id(db, analysis_id)
        if not record:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return record.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analysis: {str(e)}")


@app.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete analysis record"""
    try:
        if DatabaseOperations.delete_analysis(db, analysis_id):
            return {"status": "deleted", "id": analysis_id}
        else:
            raise HTTPException(status_code=404, detail="Analysis not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@app.get("/skills/{analysis_id}")
async def get_skills_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """
    Get detailed skills analysis for a specific resume.
    
    Args:
        analysis_id: Analysis record ID
        
    Returns:
        Skills breakdown by category
    """
    try:
        record = DatabaseOperations.get_analysis_by_id(db, analysis_id)
        if not record:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        skills = SkillCategoryExtractor.extract_skills_by_category(record.original_text)
        
        return {
            "analysis_id": analysis_id,
            "skills_by_category": skills,
            "total_skills": sum(len(v) for v in skills.values()),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Skills analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze skills: {str(e)}")


@app.get("/report/{analysis_id}")
async def download_report(analysis_id: int, db: Session = Depends(get_db)):
    """
    Generate and download a PDF report for a stored analysis.

    Args:
        analysis_id: Analysis record ID

    Returns:
        PDF file stream
    """
    try:
        record = DatabaseOperations.get_analysis_by_id(db, analysis_id)
        if not record:
            raise HTTPException(status_code=404, detail="Analysis not found")

        data = record.to_dict()
        pdf_buffer = ReportGenerator.generate_analysis_report(
            filename=data["filename"] or "resume",
            ats_score=data["ats_score"] or 0.0,
            score_breakdown=data["score_breakdown"],
            strengths=data["strengths"],
            weaknesses=data["weaknesses"],
            missing_skills=data["missing_skills"],
            section_issues=data["section_issues"],
            improved_bullets=data["improved_bullets"],
            summary=data["summary"] or "",
            jd_similarity=data["jd_similarity"],
            jd_missing_skills=data["jd_missing_skills"],
        )

        safe_name = os.path.splitext(data["filename"] or "resume")[0]
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="ResuMind_Report_{safe_name}.pdf"'
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
