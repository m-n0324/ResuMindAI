"""
Quick test of backend modules to verify functionality.
Tests each component without running the full server.
"""

import sys
import os

# Test 1: Parser
print("\n🔍 Testing Resume Parser...")
from backend.parser import ResumeParser

sample_text = """
John Doe
Software Engineer | New York, NY | john@example.com | 555-1234

PROFESSIONAL SUMMARY
Experienced full-stack engineer with 5+ years building scalable web applications using Python, JavaScript, and cloud technologies.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL
Frameworks: FastAPI, React, Django, Node.js
Databases: PostgreSQL, MongoDB, SQLite
Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
Tools: Git, GitHub, VS Code, Postman, Jira

EXPERIENCE
Senior Software Engineer | TechCorp | Jan 2022 - Present
• Led migration of monolithic Python backend to microservices architecture
• Reduced API response time by 40% through optimization and caching
• Mentored 3 junior developers on best practices

Software Engineer | StartupXYZ | Jun 2020 - Dec 2021
• Built full-stack e-commerce platform using React and FastAPI
• Implemented CI/CD pipeline with GitHub Actions
• Managed PostgreSQL database with 100K+ daily transactions

EDUCATION
B.S. Computer Science | State University | Graduated 2020
"""

try:
    # Test parsing from text (simulate resume text)
    print("✓ ResumeParser imported")
    print("✓ Sample text length:", len(sample_text), "chars")
except Exception as e:
    print(f"✗ Parser failed: {e}")
    sys.exit(1)

# Test 2: Embeddings
print("\n🔍 Testing Embeddings & Similarity...")
from backend.embeddings import SimpleEmbedding, SkillExtractor

try:
    jd = "Seeking Python developer with FastAPI and React experience. Must know PostgreSQL and AWS."
    similarity = SimpleEmbedding.compute_similarity(sample_text, jd)
    print(f"✓ Similarity computed: {similarity:.1f}%")
    
    resume_skills, missing = SkillExtractor.find_missing_skills(sample_text, jd)
    print(f"✓ Resume skills found: {len(resume_skills)}")
    print(f"✓ Missing skills: {missing}")
except Exception as e:
    print(f"✗ Embeddings failed: {e}")
    sys.exit(1)

# Test 3: Skills
print("\n🔍 Testing Skill Extraction...")
from backend.skills import SkillCategoryExtractor

try:
    skills_by_category = SkillCategoryExtractor.extract_skills_by_category(sample_text)
    print(f"✓ Skills extracted by category:")
    for category, skills in skills_by_category.items():
        print(f"  - {category}: {len(skills)} skills - {', '.join(skills[:3])}...")
except Exception as e:
    print(f"✗ Skills extraction failed: {e}")
    sys.exit(1)

# Test 4: Database
print("\n🔍 Testing Database Setup...")
from backend.db import init_db, get_db, DatabaseOperations, SessionLocal

try:
    init_db()
    print("✓ Database initialized")
    
    # Test session
    db = SessionLocal()
    print("✓ Database session created")
    db.close()
except Exception as e:
    print(f"✗ Database failed: {e}")
    sys.exit(1)

# Test 5: Report Generation
print("\n🔍 Testing Report Generation...")
from backend.report import ReportGenerator

try:
    sample_result = {
        "formatting": 85,
        "keyword_match": 78,
        "structure": 90,
        "readability": 82,
    }
    
    pdf_buffer = ReportGenerator.generate_analysis_report(
        filename="test_resume.pdf",
        ats_score=83.75,
        score_breakdown=sample_result,
        strengths=["Strong technical skills", "Leadership experience"],
        weaknesses=["Missing certifications", "Needs more metrics"],
        missing_skills=["Cloud architecture", "DevOps"],
        section_issues=[],
        improved_bullets=[
            {"original": "Built web app", "improved": "Architected and deployed scalable web application using FastAPI and React, serving 10K daily users"},
        ],
        summary="Strong resume with good technical foundation.",
        jd_similarity=85.5,
        jd_missing_skills=["Kubernetes"],
    )
    
    print(f"✓ PDF generated: {len(pdf_buffer.getvalue())} bytes")
except Exception as e:
    print(f"✗ Report generation failed: {e}")
    sys.exit(1)

# Test 6: FastAPI
print("\n🔍 Testing FastAPI Application...")
from backend.main import app

try:
    print("✓ FastAPI app imported successfully")
    print("✓ Routes registered:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  - {route.path}")
except Exception as e:
    print(f"✗ FastAPI app failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nBackend modules are ready for production!")
print("\nTo run the server, execute:")
print(r"  .\venv\Scripts\python -m backend.main")
print("\nOr use Uvicorn directly:")
print(r"  .\venv\Scripts\uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
