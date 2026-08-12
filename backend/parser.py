"""
Resume Parser Module
Extracts text from PDF, DOCX, and plain text resume files.
Supports PyMuPDF (fitz) for PDF parsing and python-docx for DOCX files.
"""

import fitz  # PyMuPDF
from docx import Document
from pathlib import Path
from typing import Optional


class ResumeParser:
    """Parse resume files in various formats (PDF, DOCX, TXT)"""

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """
        Extract text from PDF file using PyMuPDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        try:
            text = ""
            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc, 1):
                    page_text = page.get_text()
                    if page_text.strip():
                        text += f"\n--- Page {page_num} ---\n"
                        text += page_text
            
            if not text.strip():
                raise ValueError("No text extracted from PDF")
                
            return text.strip()
        except fitz.FileError as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
        except Exception as e:
            raise ValueError(f"Unexpected error parsing PDF: {str(e)}")

    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        Extract text from DOCX file using python-docx.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text from all paragraphs
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        try:
            doc = Document(file_path)
            
            # Extract text from paragraphs
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
            
            # Extract text from tables if they exist
            if doc.tables:
                text += "\n\n--- Tables ---\n"
                for table_idx, table in enumerate(doc.tables, 1):
                    text += f"\nTable {table_idx}:\n"
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells)
                        if row_text.strip():
                            text += row_text + "\n"
            
            if not text.strip():
                raise ValueError("No text extracted from DOCX")
                
            return text.strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"DOCX file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")

    @staticmethod
    def parse_txt(file_path: str) -> str:
        """
        Extract text from plain text file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            File contents
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be parsed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                raise ValueError("Text file is empty")
                
            return text
        except FileNotFoundError:
            raise FileNotFoundError(f"Text file not found: {file_path}")
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file (not UTF-8)")
        except Exception as e:
            raise ValueError(f"Failed to parse text file: {str(e)}")

    @staticmethod
    def parse_resume(file_path: str) -> str:
        """
        Parse resume file from path, detecting format by extension.
        
        Args:
            file_path: Path to resume file (PDF, DOCX, or TXT)
            
        Returns:
            Extracted resume text
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or cannot be parsed
        """
        file_path = str(file_path).lower()
        
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        if file_path.endswith('.pdf'):
            return ResumeParser.parse_pdf(file_path)
        elif file_path.endswith('.docx'):
            return ResumeParser.parse_docx(file_path)
        elif file_path.endswith('.txt'):
            return ResumeParser.parse_txt(file_path)
        else:
            raise ValueError(
                f"Unsupported file format. Supported formats: PDF, DOCX, TXT. "
                f"Got: {Path(file_path).suffix}"
            )

    @staticmethod
    def parse_from_bytes(file_bytes: bytes, file_name: str) -> str:
        """
        Parse resume from bytes (useful for uploaded files).
        Saves temporarily to disk and parses.
        
        Args:
            file_bytes: File content as bytes
            file_name: Original file name (used to determine format)
            
        Returns:
            Extracted resume text
            
        Raises:
            ValueError: If format is unsupported or parsing fails
        """
        from tempfile import NamedTemporaryFile
        import os
        
        file_name_lower = file_name.lower()
        
        # Determine extension
        if file_name_lower.endswith('.pdf'):
            suffix = '.pdf'
        elif file_name_lower.endswith('.docx'):
            suffix = '.docx'
        elif file_name_lower.endswith('.txt'):
            suffix = '.txt'
        else:
            raise ValueError(f"Unsupported file format: {file_name}")
        
        # Write bytes to temp file and parse
        temp_path = None
        try:
            with NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name

            # Parse the temp file
            return ResumeParser.parse_resume(temp_path)
        except Exception as e:
            raise ValueError(f"Failed to parse uploaded file: {str(e)}")
        finally:
            # Always clean up, otherwise failed uploads leak temp files forever
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
