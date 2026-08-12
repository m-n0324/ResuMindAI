"""
PDF Report Generation Module
Creates downloadable PDF reports of resume analysis results.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


class ReportGenerator:
    """Generate PDF reports from analysis results"""

    PAGE_WIDTH, PAGE_HEIGHT = letter
    MARGIN = 0.5 * inch

    @staticmethod
    def generate_analysis_report(
        filename: str,
        ats_score: float,
        score_breakdown: dict,
        strengths: list,
        weaknesses: list,
        missing_skills: list,
        section_issues: list,
        improved_bullets: list,
        summary: str,
        jd_similarity: float = None,
        jd_missing_skills: list = None,
    ) -> BytesIO:
        """
        Generate PDF report from analysis results.
        
        Args:
            filename: Original resume filename
            ats_score: Overall ATS score (0-100)
            score_breakdown: Dict with formatting, keyword_match, structure, readability scores
            strengths: List of resume strengths
            weaknesses: List of weaknesses
            missing_skills: Skills missing from resume
            section_issues: Section formatting issues
            improved_bullets: List of {original, improved} bullet points
            summary: Executive summary
            jd_similarity: JD match percentage (0-100)
            jd_missing_skills: Skills missing from resume per JD
            
        Returns:
            BytesIO object containing PDF data
        """
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=ReportGenerator.MARGIN,
            leftMargin=ReportGenerator.MARGIN,
            topMargin=ReportGenerator.MARGIN,
            bottomMargin=ReportGenerator.MARGIN,
        )
        
        # Setup styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=10,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
        
        # Build document content
        elements = []
        
        # Title
        elements.append(Paragraph("RESUME ANALYSIS REPORT", title_style))
        elements.append(Paragraph(f"ResuMind AI - ATS Optimizer", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # File info
        info_data = [
            ["Resume File:", filename],
            ["Analysis Date:", datetime.now().strftime("%B %d, %Y")],
            ["Overall ATS Score:", f"{ats_score:.1f} / 100"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f0ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))
        
        # Score breakdown
        elements.append(Paragraph("ATS Score Breakdown", heading_style))
        score_data = [
            ["Component", "Score"],
            ["Formatting", f"{score_breakdown.get('formatting', 0):.0f}%"],
            ["Keyword Match", f"{score_breakdown.get('keyword_match', 0):.0f}%"],
            ["Structure", f"{score_breakdown.get('structure', 0):.0f}%"],
            ["Readability", f"{score_breakdown.get('readability', 0):.0f}%"],
        ]
        
        score_table = Table(score_data, colWidths=[3*inch, 2.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 12))
        
        # Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(summary, normal_style))
        elements.append(Spacer(1, 12))
        
        # Strengths
        elements.append(Paragraph("Strengths", heading_style))
        for i, strength in enumerate(strengths, 1):
            elements.append(Paragraph(f"• {strength}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Weaknesses
        elements.append(Paragraph("Areas for Improvement", heading_style))
        for i, weakness in enumerate(weaknesses, 1):
            elements.append(Paragraph(f"• {weakness}", normal_style))
        elements.append(Spacer(1, 12))
        
        # Section Issues
        if section_issues:
            elements.append(Paragraph("Section Formatting Issues", heading_style))
            for issue in section_issues:
                elements.append(Paragraph(f"• {issue}", normal_style))
            elements.append(Spacer(1, 12))
        
        # Missing Skills
        elements.append(Paragraph("Skills to Highlight", heading_style))
        elements.append(Paragraph(
            "These professional skills are commonly sought but may be missing or understated in your resume:",
            normal_style
        ))
        skills_text = ", ".join(missing_skills[:10])
        if len(missing_skills) > 10:
            skills_text += f", and {len(missing_skills) - 10} more..."
        elements.append(Paragraph(f"<b>{skills_text}</b>", normal_style))
        elements.append(Spacer(1, 12))
        
        # JD Matching
        if jd_similarity is not None:
            elements.append(Paragraph("Job Description Match", heading_style))
            elements.append(Paragraph(
                f"Resume-JD Similarity Score: <b>{jd_similarity:.1f}%</b><br/>"
                "This indicates how well your resume aligns with the job requirements.",
                normal_style
            ))
            if jd_missing_skills:
                elements.append(Paragraph(
                    f"<b>Critical Missing Skills:</b> {', '.join(jd_missing_skills[:5])}",
                    normal_style
                ))
            elements.append(Spacer(1, 12))
        
        # Page break before improved bullets
        elements.append(PageBreak())
        
        # Improved Bullet Points
        elements.append(Paragraph("Optimized Bullet Points (STAR Format)", heading_style))
        elements.append(Paragraph(
            "Below are improved versions of your bullet points using the STAR method "
            "(Situation, Task, Action, Result) for better ATS compatibility and impact:",
            normal_style
        ))
        elements.append(Spacer(1, 6))
        
        for i, bullet in enumerate(improved_bullets[:5], 1):  # Show top 5
            elements.append(Paragraph(f"<b>Original:</b>", normal_style))
            elements.append(Paragraph(f"{bullet['original']}", ParagraphStyle(
                'Italic',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.grey,
                leftIndent=0.2*inch
            )))
            elements.append(Spacer(1, 6))
            
            elements.append(Paragraph(f"<b>Improved:</b>", normal_style))
            elements.append(Paragraph(f"{bullet['improved']}", ParagraphStyle(
                'Improved',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=0.2*inch,
                textColor=colors.HexColor('#1f4788'),
                fontName='Helvetica-Bold'
            )))
            elements.append(Spacer(1, 12))
        
        # Footer
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(
            "<i>This report was generated by ResuMind AI, an advanced ATS optimization tool. "
            "For more information, visit: https://resumind.ai</i>",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer

    @staticmethod
    def save_to_file(pdf_buffer: BytesIO, output_path: str):
        """Save PDF buffer to file"""
        with open(output_path, 'wb') as f:
            f.write(pdf_buffer.getvalue())
