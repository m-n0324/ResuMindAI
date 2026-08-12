# ResuMind AI - Advanced Resume Intelligence & ATS Optimizer

**Transform your resume with AI-powered analysis and ATS optimization**

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen) ![Python](https://img.shields.io/badge/Python-3.12.10-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-green) ![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)

---

## 🎯 Project Overview

ResuMind AI is a comprehensive resume analysis platform that uses cutting-edge AI and natural language processing to help job seekers optimize their resumes for Applicant Tracking Systems (ATS).

### Key Features
✅ **ATS Score Analysis** - Detailed scoring on formatting, keywords, structure, readability
✅ **Job Description Matching** - Compare resume against job postings using AI
✅ **Skill Gap Analysis** - Identify missing and important skills
✅ **Bullet Point Optimization** - Rewrite achievements in STAR format
✅ **PDF Report Generation** - Download professional analysis reports
✅ **Analysis History** - Track improvements over time
✅ **Multi-Format Support** - PDF, DOCX, and TXT uploads

---

## 🚀 Quick Start

### 1. Setup
```bash
cd "ResuMind AI"
.\venv\Scripts\activate
pip install -r requirements.txt
```
Then copy `.env.example` to `.env` and set `GOOGLE_API_KEY`
(get one at https://aistudio.google.com/apikey).

### 2. Run it (single command)
```bash
python run.py
```
This starts the backend, waits until it is healthy, then starts the UI.

**UI:** http://localhost:8501 · **API docs:** http://localhost:8000/docs

> ⚠️ **The app needs BOTH processes.** The Streamlit UI hides the upload form
> unless it can reach the backend's `/health` endpoint. Running only
> `streamlit run app.py` is the most common reason uploads appear to do nothing.

### Running the two processes manually
```bash
# Terminal 1
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# Terminal 2
streamlit run app.py --server.port 8501
```

---

## 📊 Backend Modules

| Module | Purpose |
|--------|---------|
| `parser.py` | PDF/DOCX/TXT extraction |
| `llm.py` | Google Gemini AI integration |
| `embeddings.py` | TF-IDF semantic matching |
| `skills.py` | Skill extraction (200+ skills) |
| `db.py` | SQLAlchemy ORM models |
| `main.py` | FastAPI application |
| `report.py` | PDF report generation |

---

## 🔌 API Endpoints

```
POST   /analyze              - Upload resume and analyze
GET    /health               - Health check
GET    /history/{user_id}    - Get analysis history
GET    /analysis/{id}        - Get specific analysis
GET    /skills/{id}          - Get skills breakdown
GET    /report/{id}          - Download PDF analysis report
DELETE /analysis/{id}        - Delete analysis
```

---

## 📦 Tech Stack

**Backend:**
- FastAPI 0.141.1, SQLAlchemy 2.0.52, SQLite
- PyMuPDF, python-docx, ReportLab
- Google Gemini API

**Frontend:**
- Streamlit, Plotly, Pandas

---

## 📝 Database Schema

### AnalysisRecord
- ATS scores and components
- Resume text and parsed content
- JD matching results
- Skills analysis
- Recommendations and improvements

### UserSettings
- User preferences
- Target job titles and industries
- Skill levels

---

## 🧪 Testing

Run comprehensive backend tests:
```bash
python test_backend.py
```

Test health endpoint:
```bash
curl http://localhost:8000/health
```

---

## 🔐 Security

- Store API keys in `.env` (never commit to git)
- File upload validation (PDF, DOCX, TXT only)
- Proper error handling without info leakage
- CORS configured for production

---

## 🚀 Deployment

Deploy to Render, Railway, or Heroku using the provided configuration.

---

## 📞 Support

**Issues?**
1. Check backend health: `curl http://localhost:8000/health`
2. Verify .env configuration
3. Check terminal logs for errors
4. Review API docs at `http://localhost:8000/docs`

---

**Version:** 1.0.0 | **Status:** Production Ready ✅
*Made with ❤️ using Python, FastAPI, Streamlit, and AI*
