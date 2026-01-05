"""BibTeX parsing utilities for citation analysis."""

import os
import re
from typing import Dict, List, Optional


def parse_bibtex(file_path: str) -> Dict:
    """
    Parse a BibTeX file and extract citation information.
    
    Args:
        file_path: Path to the .bib file
        
    Returns:
        Dictionary with parsed entries and metadata
    """
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error_message": f"File not found: {file_path}"
        }
    
    try:
        import bibtexparser
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            bib_database = bibtexparser.load(f)
        
        entries = []
        for entry in bib_database.entries:
            entries.append({
                "key": entry.get("ID", ""),
                "type": entry.get("ENTRYTYPE", ""),
                "title": entry.get("title", ""),
                "author": entry.get("author", ""),
                "year": entry.get("year", ""),
                "venue": entry.get("journal", entry.get("booktitle", "")),
                "doi": entry.get("doi", ""),
                "url": entry.get("url", ""),
            })
        
        return {
            "status": "success",
            "entries": entries,
            "count": len(entries)
        }
        
    except ImportError:
        # Fallback to manual parsing if bibtexparser not available
        return parse_bibtex_manual(file_path)
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse BibTeX: {str(e)}"
        }


def parse_bibtex_manual(file_path: str) -> Dict:
    """
    Manual BibTeX parsing fallback.
    
    Handles basic BibTeX structure without external dependencies.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        entries = []
        
        # Match BibTeX entries
        entry_pattern = r'@(\w+)\{([^,]+),([^@]*)\}'
        
        for match in re.finditer(entry_pattern, content, re.DOTALL):
            entry_type = match.group(1)
            entry_key = match.group(2).strip()
            entry_content = match.group(3)
            
            # Extract fields from entry content
            entry = {
                "key": entry_key,
                "type": entry_type,
            }
            
            # Common fields to extract
            fields = ['title', 'author', 'year', 'journal', 'booktitle', 'doi', 'url']
            
            for field in fields:
                pattern = rf'{field}\s*=\s*[\{{"](.*?)[\}}"]\s*[,\}}]'
                field_match = re.search(pattern, entry_content, re.IGNORECASE | re.DOTALL)
                if field_match:
                    value = field_match.group(1).strip()
                    # Clean up LaTeX-style braces
                    value = re.sub(r'[\{\}]', '', value)
                    entry[field] = value
            
            # Set venue from journal or booktitle
            entry["venue"] = entry.get("journal", entry.get("booktitle", ""))
            
            entries.append(entry)
        
        return {
            "status": "success",
            "entries": entries,
            "count": len(entries)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse BibTeX manually: {str(e)}"
        }


def get_citation_info(file_path: str) -> Dict:
    """
    Get comprehensive citation information from a BibTeX file.
    
    Includes analysis of citation patterns and potential issues.
    """
    result = parse_bibtex(file_path)
    
    if result["status"] == "error":
        return result
    
    entries = result["entries"]
    
    # Analyze citations
    years = []
    venues = {}
    authors = {}
    
    for entry in entries:
        # Track years
        year = entry.get("year", "")
        if year and year.isdigit():
            years.append(int(year))
        
        # Track venues
        venue = entry.get("venue", "Unknown")
        if venue:
            venues[venue] = venues.get(venue, 0) + 1
        
        # Track authors
        author_str = entry.get("author", "")
        if author_str:
            # Simple author extraction (split by 'and')
            for author in author_str.split(" and "):
                author = author.strip()
                if author:
                    authors[author] = authors.get(author, 0) + 1
    
    # Calculate statistics
    stats = {}
    if years:
        stats["year_range"] = f"{min(years)}-{max(years)}"
        stats["median_year"] = sorted(years)[len(years) // 2]
        stats["recent_citations"] = sum(1 for y in years if y >= 2020)
    
    # Identify potential issues
    issues = []
    
    if years:
        current_year = 2026  # Based on system time
        old_citations = sum(1 for y in years if y < current_year - 10)
        if old_citations > len(years) * 0.5:
            issues.append(f"Over 50% of citations are more than 10 years old ({old_citations}/{len(years)})")
    
    if len(entries) < 10:
        issues.append(f"Low citation count ({len(entries)}). Consider adding more references.")
    
    # Check for self-citation patterns (if same author appears frequently)
    max_author_count = max(authors.values()) if authors else 0
    if max_author_count > len(entries) * 0.3:
        issues.append("Potential self-citation bias detected. Verify diverse set of references.")
    
    result["statistics"] = stats
    result["top_venues"] = dict(sorted(venues.items(), key=lambda x: x[1], reverse=True)[:5])
    result["issues"] = issues
    
    return result


def find_standard_baselines(entries: List[Dict], domain: str = "ML") -> List[str]:
    """
    Identify potentially missing standard baselines based on cited work.
    
    This is a heuristic-based approach that looks for common baseline papers.
    """
    # Common baseline papers/methods in ML/DL
    common_baselines = {
        "ML": [
            "ResNet", "VGG", "BERT", "GPT", "Transformer",
            "LSTM", "GRU", "XGBoost", "Random Forest",
            "Adam", "SGD", "Dropout", "BatchNorm"
        ],
        "NLP": [
            "BERT", "GPT", "T5", "RoBERTa", "XLNet",
            "Word2Vec", "GloVe", "ELMo", "Transformer"
        ],
        "CV": [
            "ResNet", "VGG", "InceptionNet", "EfficientNet",
            "YOLO", "Faster R-CNN", "U-Net", "ViT"
        ]
    }
    
    baselines_to_check = common_baselines.get(domain, common_baselines["ML"])
    
    # Get all cited content
    cited_text = " ".join([
        str(e.get("title", "")) + " " + str(e.get("author", ""))
        for e in entries
    ]).lower()
    
    missing = []
    for baseline in baselines_to_check:
        if baseline.lower() not in cited_text:
            missing.append(baseline)
    
    return missing
