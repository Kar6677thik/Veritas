"""PDF parsing utilities for research papers."""

import os
from typing import Dict, List, Optional
import re


def extract_text_from_pdf(file_path: str) -> Dict:
    """
    Extract text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary with status and extracted text or error message
    """
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error_message": f"File not found: {file_path}"
        }
    
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(file_path)
        text_content = []
        
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
        
        full_text = "\n\n".join(text_content)
        
        return {
            "status": "success",
            "text": full_text,
            "num_pages": len(reader.pages)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse PDF: {str(e)}"
        }


def parse_pdf(file_path: str) -> Dict:
    """
    Parse a PDF research paper and extract structured information.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted paper components
    """
    result = extract_text_from_pdf(file_path)
    
    if result["status"] == "error":
        return result
    
    text = result["text"]
    
    # Extract common paper sections
    sections = extract_sections_from_text(text)
    
    # Try to extract title (usually first significant line)
    title = extract_title(text)
    
    # Try to extract abstract
    abstract = extract_abstract(text)
    
    return {
        "status": "success",
        "title": title,
        "abstract": abstract,
        "sections": sections,
        "full_text": text,
        "num_pages": result.get("num_pages", 0)
    }


def extract_sections_from_text(text: str) -> Dict[str, str]:
    """Extract common paper sections from text."""
    sections = {}
    
    # Common section patterns
    section_patterns = [
        (r'(?i)\b(abstract)\b[:\s]*\n?(.*?)(?=\n\s*\d*\.?\s*(?:introduction|keywords|1\s)|\Z)', 'abstract'),
        (r'(?i)\b(\d*\.?\s*introduction)\b[:\s]*\n?(.*?)(?=\n\s*\d*\.?\s*(?:related|background|method|2\s)|\Z)', 'introduction'),
        (r'(?i)\b(\d*\.?\s*related\s*work)\b[:\s]*\n?(.*?)(?=\n\s*\d*\.?\s*(?:method|approach|model|3\s)|\Z)', 'related_work'),
        (r'(?i)\b(\d*\.?\s*(?:method|methodology|approach))\b[:\s]*\n?(.*?)(?=\n\s*\d*\.?\s*(?:experiment|result|evaluation|4\s)|\Z)', 'methodology'),
        (r'(?i)\b(\d*\.?\s*(?:experiment|evaluation|result)s?)\b[:\s]*\n?(.*?)(?=\n\s*\d*\.?\s*(?:discussion|conclusion|analysis|5\s|6\s)|\Z)', 'experiments'),
        (r'(?i)\b(\d*\.?\s*(?:conclusion|summary)s?)\b[:\s]*\n?(.*?)(?=\n\s*(?:reference|acknowledgment|appendix)|\Z)', 'conclusion'),
    ]
    
    for pattern, section_name in section_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(2) if len(match.groups()) > 1 else match.group(1)
            sections[section_name] = content.strip()[:2000]  # Limit content length
    
    return sections


def extract_title(text: str) -> Optional[str]:
    """Try to extract paper title from text."""
    lines = text.strip().split('\n')
    
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        # Title is usually a longer line without common section markers
        if len(line) > 20 and len(line) < 200:
            if not re.match(r'^(?:abstract|introduction|\d+\.)', line, re.IGNORECASE):
                return line
    
    return None


def extract_abstract(text: str) -> Optional[str]:
    """Extract abstract from paper text."""
    # Try to find abstract section
    abstract_match = re.search(
        r'(?i)\babstract\b[:\s]*\n?(.*?)(?=\n\s*(?:\d*\.?\s*introduction|keywords|1\s|\n\n))',
        text,
        re.DOTALL
    )
    
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        # Clean up and limit length
        abstract = ' '.join(abstract.split())
        return abstract[:1500] if len(abstract) > 1500 else abstract
    
    return None


def extract_tables_from_text(text: str) -> List[Dict]:
    """
    Attempt to identify table references and captions in text.
    
    Note: Full table extraction from PDFs is complex and may require
    specialized libraries like tabula-py or camelot.
    """
    tables = []
    
    # Find table references
    table_pattern = r'(?i)table\s+(\d+)[:\.]?\s*([^\n]+)?'
    matches = re.findall(table_pattern, text)
    
    for match in matches:
        table_num, caption = match
        tables.append({
            "table_number": table_num,
            "caption": caption.strip() if caption else None
        })
    
    # Deduplicate
    seen = set()
    unique_tables = []
    for table in tables:
        key = table["table_number"]
        if key not in seen:
            seen.add(key)
            unique_tables.append(table)
    
    return unique_tables
