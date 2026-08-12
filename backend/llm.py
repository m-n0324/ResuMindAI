"""
LLM Analysis Module
Provides resume analysis using Google Gemini API with fallback mechanism.
Generates ATS scores, identifies strengths/weaknesses, and rewrites bullet points.
"""

import json
import os
from typing import Dict, Optional, Any
import google.generativeai as genai
from pydantic import BaseModel


class ATSScoreBreakdown(BaseModel):
    """Breakdown of ATS score components"""
    formatting: float  # 0-100
    keyword_match: float  # 0-100
    structure: float  # 0-100
    readability: float  # 0-100


class BulletPoint(BaseModel):
    """Original vs improved bullet point"""
    original: str
    improved: str


class AnalysisResult(BaseModel):
    """Complete resume analysis result"""
    ats_score: float
    score_breakdown: ATSScoreBreakdown
    strengths: list[str]
    weaknesses: list[str]
    missing_skills: list[str]
    section_issues: list[str]
    improved_bullets: list[BulletPoint]
    summary: str
    jd_similarity: Optional[float] = None
    jd_missing_skills: Optional[list[str]] = None


class LLMAnalyzer:
    """Resume analyzer using Google Gemini API"""

    ANALYSIS_PROMPT = """You are an expert ATS (Applicant Tracking System) resume analyzer and career coach.

Your task is to analyze the provided resume and generate a detailed, actionable report.

RESUME TEXT:
{resume}

JOB DESCRIPTION (if provided):
{jd}

Please analyze the resume and return ONLY a valid JSON object (no extra text, no markdown formatting) with this exact structure:
{{
  "ats_score": <number 0-100>,
  "score_breakdown": {{
    "formatting": <number 0-100 - clarity of formatting, proper sections, consistent styling>,
    "keyword_match": <number 0-100 - presence of relevant industry keywords and skills>,
    "structure": <number 0-100 - logical flow, proper section organization>,
    "readability": <number 0-100 - clarity of language, conciseness, bullet point quality>
  }},
  "strengths": [<list of 3-5 positive aspects of the resume>],
  "weaknesses": [<list of 3-5 areas for improvement>],
  "missing_skills": [<list of important skills not mentioned in resume>],
  "section_issues": [<list of missing or improperly formatted sections>],
  "improved_bullets": [
    {{"original": "<original bullet point>", "improved": "<STAR formatted improvement>"}},
    ...
  ],
  "summary": "<2-3 sentence executive summary of the analysis>"
}}

Important:
- Format improved bullets using STAR method (Situation, Task, Action, Result)
- Include quantifiable metrics where possible
- Make suggestions specific and actionable
- Consider ATS readability (no fancy formatting, clear structure)
- Return ONLY valid JSON, no markdown code blocks, no extra text
"""

    # gemini-2.5-* is no longer served to newly created API keys and returns 404.
    # Use a current model; override with the GEMINI_MODEL env var.
    DEFAULT_MODEL = "gemini-3.5-flash"

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize LLM Analyzer.

        Args:
            api_key: Google Gemini API key. If None, reads from GOOGLE_API_KEY env var.
            model_name: Gemini model to use. If None, reads GEMINI_MODEL env var,
                falling back to DEFAULT_MODEL.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not provided. Add it to the .env file in the project root "
                "(GOOGLE_API_KEY=your-key), export it as an environment variable, or pass "
                "api_key= to LLMAnalyzer. Get a key at https://aistudio.google.com/apikey"
            )

        genai.configure(api_key=self.api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL") or self.DEFAULT_MODEL

    def analyze_resume(
        self, 
        resume_text: str, 
        jd_text: Optional[str] = None
    ) -> AnalysisResult:
        """
        Analyze resume using Gemini API.
        
        Args:
            resume_text: Full resume text
            jd_text: Job description text (optional for JD matching)
            
        Returns:
            AnalysisResult with scores, feedback, and improvements
            
        Raises:
            ValueError: If API call fails or response is invalid JSON
        """
        try:
            prompt = self.ANALYSIS_PROMPT.format(
                resume=resume_text,
                jd=jd_text or "(No job description provided)"
            )
            
            # Call Gemini API
            response = genai.GenerativeModel(self.model_name).generate_content(prompt)
            
            # Extract and parse JSON
            response_text = response.text.strip()
            
            # Clean up potential markdown formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                result_dict = json.loads(response_text)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\n\nResponse: {response_text[:500]}")
            
            # Validate and construct result
            analysis = AnalysisResult(
                ats_score=float(result_dict.get("ats_score", 0)),
                score_breakdown=ATSScoreBreakdown(
                    formatting=float(result_dict.get("score_breakdown", {}).get("formatting", 0)),
                    keyword_match=float(result_dict.get("score_breakdown", {}).get("keyword_match", 0)),
                    structure=float(result_dict.get("score_breakdown", {}).get("structure", 0)),
                    readability=float(result_dict.get("score_breakdown", {}).get("readability", 0)),
                ),
                strengths=result_dict.get("strengths", []),
                weaknesses=result_dict.get("weaknesses", []),
                missing_skills=result_dict.get("missing_skills", []),
                section_issues=result_dict.get("section_issues", []),
                improved_bullets=[
                    BulletPoint(**bullet) 
                    for bullet in result_dict.get("improved_bullets", [])
                ],
                summary=result_dict.get("summary", ""),
            )
            
            return analysis
            
        except Exception as e:
            raise ValueError(f"Resume analysis failed: {str(e)}")

    def get_model_name(self) -> str:
        """Get current model name"""
        return self.model_name

    def set_model_name(self, model_name: str) -> None:
        """Change model name (e.g., to gemini-1.5-pro for advanced analysis)"""
        self.model_name = model_name


def create_analyzer(api_key: Optional[str] = None) -> LLMAnalyzer:
    """Factory function to create LLMAnalyzer"""
    return LLMAnalyzer(api_key=api_key)
