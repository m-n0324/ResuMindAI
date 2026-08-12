"""
ResuMind AI - Streamlit Frontend
Advanced Resume Intelligence & ATS Optimizer Web Interface
"""

import os
import streamlit as st
import requests
import json
from io import BytesIO
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="ResuMind AI - Resume Optimizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        color: #1f4788;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .sub-header {
        color: #2c5aa0;
        font-size: 1.5em;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2em;
        font-weight: bold;
    }
    .success-card {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .warning-card {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .metric-box {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Constants
API_URL = os.getenv("RESUMIND_API_URL", "http://localhost:8000")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
# Gemini analysis of a long resume + JD can run well past a minute; the old
# 60s limit cut off valid analyses and surfaced only a raw ReadTimeout string.
ANALYZE_TIMEOUT_SECONDS = 300

# Session state initialization
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "history" not in st.session_state:
    st.session_state.history = []


# ============ Helper Functions ============

def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_and_analyze(file_upload, job_description: Optional[str] = None):
    """Upload resume and get analysis"""
    if not file_upload:
        # Previously returned silently, so clicking Analyze with no file
        # attached looked exactly like a broken app.
        st.warning("📎 Please choose a resume file first, then click Analyze.")
        return None

    # Validate file type
    if not any(file_upload.name.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        st.error(f"❌ Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
        return None

    try:
        with st.spinner("📊 Analyzing resume... this usually takes 10-40 seconds."):
            files = {"file": (file_upload.name, file_upload.getvalue())}
            data = {}
            if st.session_state.user_id:
                data["user_id"] = st.session_state.user_id
            if job_description:
                data["job_description"] = job_description

            response = requests.post(
                f"{API_URL}/analyze",
                files=files,
                data=data,
                timeout=ANALYZE_TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                return response.json()

            try:
                detail = response.json().get("detail", response.text[:300])
            except ValueError:
                detail = response.text[:300] or "Unknown error"
            st.error(f"❌ Analysis failed (HTTP {response.status_code}): {detail}")
            return None
    except requests.ConnectionError:
        st.error(
            "❌ Cannot connect to the backend API. Start it with: "
            "`uvicorn backend.main:app --port 8000`"
        )
        return None
    except requests.Timeout:
        st.error(
            f"⏱️ The analysis took longer than {ANALYZE_TIMEOUT_SECONDS}s and timed out. "
            "Try a shorter resume or a shorter job description."
        )
        return None
    except Exception as e:
        st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
        return None


def fetch_report_pdf(analysis_id: int):
    """Fetch the generated PDF report for an analysis"""
    try:
        response = requests.get(f"{API_URL}/report/{analysis_id}", timeout=60)
        if response.status_code == 200:
            return response.content
        st.error(f"❌ Could not generate report (HTTP {response.status_code}).")
    except Exception as e:
        st.error(f"❌ Could not generate report: {str(e)}")
    return None


def get_user_history(user_id: str):
    """Fetch user analysis history"""
    try:
        response = requests.get(f"{API_URL}/history/{user_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []


def create_score_gauge(score: float, title: str):
    """Create gauge chart for score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": title},
        delta={"reference": 75},
        gauge={
            "axis": {"range": [None, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 25], "color": "#ff6b6b"},
                {"range": [25, 50], "color": "#ffd93d"},
                {"range": [50, 75], "color": "#a8e6cf"},
                {"range": [75, 100], "color": "#56ab2f"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=50, r=50, t=50, b=50))
    return fig


# ============ Main UI ============

def main():
    # Header
    st.markdown('<p class="main-header">📄 ResuMind AI</p>', unsafe_allow_html=True)
    st.markdown("**Advanced Resume Intelligence & ATS Optimizer**")
    
    # Check API status
    if not check_api_health():
        st.error("🔴 **Backend API is not running.** Please start the server with: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`")
        return
    
    st.success("✅ **Backend API is running!**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        
        st.subheader("User Profile")
        user_id = st.text_input(
            "User ID (optional)",
            value=st.session_state.user_id or "",
            help="Enter a user ID to track your analysis history"
        )
        if user_id:
            st.session_state.user_id = user_id
        
        st.divider()
        
        st.subheader("Navigation")
        page = st.radio(
            "Select Page:",
            options=["Upload & Analyze", "History", "About"],
            label_visibility="collapsed"
        )
    
    # ============ Page: Upload & Analyze ============
    if page == "Upload & Analyze":
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<p class="sub-header">📤 Upload Resume</p>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Choose a resume file",
                type=["pdf", "docx", "txt"],
                help="PDF, DOCX, or TXT format",
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown('<p class="sub-header">🎯 Job Description (Optional)</p>', unsafe_allow_html=True)
            jd_input = st.text_area(
                "Paste job description for JD matching",
                height=150,
                placeholder="Paste the job description here for better matching and recommendations...",
                label_visibility="collapsed"
            )
        
        # Analyze button
        if st.button("🔍 Analyze Resume", type="primary", use_container_width=True):
            result = upload_and_analyze(uploaded_file, jd_input if jd_input.strip() else None)
            if result:
                st.session_state.analysis_result = result
                st.success("✅ Analysis complete!")
        
        # Display results if available
        if st.session_state.analysis_result:
            result = st.session_state.analysis_result
            
            st.markdown("---")
            st.markdown('<p class="sub-header">📊 Analysis Results</p>', unsafe_allow_html=True)
            
            # ATS Score - Main Display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="score-card">ATS Score<br/>' + 
                          f'{result["ats_score"]:.1f} / 100</div>',
                          unsafe_allow_html=True)
            
            with col2:
                st.metric(
                    "Formatting",
                    f'{result["score_breakdown"]["formatting"]:.0f}%',
                    delta=-5 if result["score_breakdown"]["formatting"] < 85 else "Good"
                )
            
            with col3:
                st.metric(
                    "Keywords",
                    f'{result["score_breakdown"]["keyword_match"]:.0f}%',
                    delta=-5 if result["score_breakdown"]["keyword_match"] < 80 else "Good"
                )
            
            with col4:
                st.metric(
                    "Structure",
                    f'{result["score_breakdown"]["structure"]:.0f}%',
                    delta=-5 if result["score_breakdown"]["structure"] < 85 else "Good"
                )
            
            st.divider()
            
            # Score Breakdown Visualization
            st.markdown("**Score Breakdown Details**")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                fig = create_score_gauge(result["ats_score"], "Overall ATS Score")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Breakdown as bar chart
                scores_df = pd.DataFrame({
                    "Component": ["Formatting", "Keywords", "Structure", "Readability"],
                    "Score": [
                        result["score_breakdown"]["formatting"],
                        result["score_breakdown"]["keyword_match"],
                        result["score_breakdown"]["structure"],
                        result["score_breakdown"]["readability"],
                    ]
                })
                
                fig = go.Figure(data=[
                    go.Bar(x=scores_df["Component"], y=scores_df["Score"],
                           marker_color=['#56ab2f' if x >= 80 else '#ffd93d' for x in scores_df["Score"]],
                           text=scores_df["Score"].round(0),
                           textposition='auto')
                ])
                fig.update_layout(
                    title="Score Component Breakdown",
                    xaxis_title="Component",
                    yaxis_title="Score (%)",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            # Executive Summary
            st.markdown("**Executive Summary**")
            st.info(result["summary"])
            
            st.divider()
            
            # Strengths & Weaknesses
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**✅ Strengths**")
                for strength in result["strengths"]:
                    st.markdown(f"• {strength}")
            
            with col2:
                st.markdown("**⚠️ Areas for Improvement**")
                for weakness in result["weaknesses"]:
                    st.markdown(f"• {weakness}")
            
            st.divider()
            
            # Missing Skills
            st.markdown("**📚 Skills to Highlight**")
            if result["missing_skills"]:
                skills_str = ", ".join(result["missing_skills"][:15])
                if len(result["missing_skills"]) > 15:
                    skills_str += f", and {len(result['missing_skills']) - 15} more"
                st.warning(f"Consider adding: **{skills_str}**")
            
            # Section Issues
            if result["section_issues"]:
                st.markdown("**🔧 Section Formatting Issues**")
                for issue in result["section_issues"]:
                    st.markdown(f"• {issue}")
            
            st.divider()
            
            # JD Matching
            if result.get("jd_similarity") is not None:
                st.markdown("**🎯 Job Description Matching**")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.metric(
                        "Resume-JD Match",
                        f'{result["jd_similarity"]:.1f}%',
                        help="How well your resume aligns with the job requirements"
                    )
                
                with col2:
                    if result.get("jd_missing_skills"):
                        missing = ", ".join(result["jd_missing_skills"][:5])
                        st.warning(f"**Missing Skills for JD:** {missing}")
            
            st.divider()
            
            # Improved Bullet Points
            st.markdown("**✨ Optimized Bullet Points (STAR Format)**")
            for i, bullet in enumerate(result["improved_bullets"][:5], 1):
                with st.expander(f"Bullet {i}", expanded=i==1):
                    st.markdown("**Original:**")
                    st.caption(bullet["original"])
                    st.markdown("**Improved:**")
                    st.success(bullet["improved"])
            
            st.divider()
            
            # Download Report
            analysis_id = result.get("id")
            if analysis_id:
                pdf_bytes = fetch_report_pdf(analysis_id)
                if pdf_bytes:
                    st.download_button(
                        "📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"ResuMind_Report_{analysis_id}.pdf",
                        mime="application/pdf",
                        type="secondary",
                        use_container_width=True,
                    )
            else:
                st.info(
                    "📝 This analysis was not saved to the database, so a PDF report "
                    "cannot be generated for it."
                )

            # Save Analysis
            if st.session_state.user_id and analysis_id:
                st.success(f"✅ Analysis saved (ID: {analysis_id})")
    
    # ============ Page: History ============
    elif page == "History":
        st.markdown('<p class="sub-header">📋 Analysis History</p>', unsafe_allow_html=True)
        
        if not st.session_state.user_id:
            st.warning("👤 Please set a User ID in Settings to view your history.")
        else:
            with st.spinner("📚 Loading history..."):
                history = get_user_history(st.session_state.user_id)
            
            if history:
                st.success(f"Found {len(history)} analyses")
                
                # Display as table
                df_data = []
                for analysis in history:
                    df_data.append({
                        "Date": analysis["created_at"][:10],
                        "Filename": analysis.get("filename", "Unknown"),
                        "ATS Score": f"{analysis['ats_score']:.1f}",
                        "JD Match": f"{analysis.get('jd_similarity', 0):.1f}%" if analysis.get("jd_similarity") else "N/A",
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No analysis history found. Upload a resume to get started!")
    
    # ============ Page: About ============
    elif page == "About":
        st.markdown('<p class="sub-header">ℹ️ About ResuMind AI</p>', unsafe_allow_html=True)
        
        st.markdown("""
        ## Welcome to ResuMind AI
        
        **Advanced Resume Intelligence & ATS Optimizer**
        
        ### What We Do
        ResuMind AI uses cutting-edge AI and natural language processing to:
        
        - 🎯 **Calculate ATS Score** - Analyze your resume against applicant tracking systems
        - 📊 **Score Breakdown** - Understand formatting, keywords, structure, and readability
        - 🔍 **Job Matching** - Compare your resume against job descriptions
        - 💡 **Smart Recommendations** - Get actionable improvements to boost your chances
        - ⭐ **Bullet Point Optimization** - Rewrite achievements in STAR format
        - 📈 **Skill Analysis** - Identify missing skills and gaps
        
        ### Key Features
        
        1. **Multi-Format Support** - PDF, DOCX, TXT files
        2. **Semantic Matching** - AI-powered job description comparison
        3. **Detailed Analytics** - Comprehensive scoring and breakdowns
        4. **Version History** - Track improvements over time
        5. **PDF Reports** - Download professional analysis reports
        
        ### Technology Stack
        
        - **Backend**: FastAPI, Python
        - **LLM**: Google Gemini API
        - **Database**: SQLAlchemy + SQLite
        - **Frontend**: Streamlit
        - **PDF Processing**: PyMuPDF, ReportLab
        
        ### Getting Started
        
        1. Upload your resume (PDF, DOCX, or TXT)
        2. Optionally paste a job description for matching
        3. Click "Analyze" and get instant feedback
        4. Review the results and implement improvements
        5. Re-upload to track your progress
        
        ---
        
        **Made with ❤️ using AI and Python**
        """)
        
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "✅ Live")
        with col2:
            st.metric("API", "FastAPI")
        with col3:
            st.metric("Version", "1.0.0")


if __name__ == "__main__":
    main()
