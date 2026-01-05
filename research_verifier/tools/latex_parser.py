"""LaTeX parsing utilities for research papers."""

import os
import re
from typing import Dict, List, Optional


def parse_latex(file_path: str) -> Dict:
    """
    Parse a LaTeX file and extract structured information.
    
    Args:
        file_path: Path to the .tex file
        
    Returns:
        Dictionary with parsed content and structure
    """
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error_message": f"File not found: {file_path}"
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract document content (between \begin{document} and \end{document})
        doc_match = re.search(
            r'\\begin\{document\}(.*?)\\end\{document\}',
            content,
            re.DOTALL
        )
        
        document_content = doc_match.group(1) if doc_match else content
        
        # Clean LaTeX and convert to plain text
        plain_text = latex_to_text(document_content)
        
        # Extract metadata
        title = extract_latex_command(content, 'title')
        abstract = extract_latex_environment(content, 'abstract')
        
        # Extract sections
        sections = extract_sections(content)
        
        return {
            "status": "success",
            "title": title,
            "abstract": abstract,
            "sections": sections,
            "full_text": plain_text,
            "raw_latex": content
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to parse LaTeX: {str(e)}"
        }


def latex_to_text(latex_content: str) -> str:
    """
    Convert LaTeX content to plain text.
    
    This is a simplified conversion that handles common cases.
    For full conversion, consider using pylatexenc.
    """
    text = latex_content
    
    # Remove comments
    text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)
    
    # Remove common LaTeX commands but keep their content
    text = re.sub(r'\\(?:textbf|textit|emph|underline)\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\(?:section|subsection|subsubsection)\*?\{([^}]*)\}', r'\n\n\1\n', text)
    
    # Remove citations (keep the marker)
    text = re.sub(r'\\cite\{([^}]*)\}', r'[CITE: \1]', text)
    
    # Remove references
    text = re.sub(r'\\ref\{([^}]*)\}', r'[REF: \1]', text)
    
    # Remove figure/table environments but note them
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '[FIGURE]', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '[TABLE]', text, flags=re.DOTALL)
    
    # Remove math environments but keep inline math
    text = re.sub(r'\$\$.*?\$\$', '[EQUATION]', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '[EQUATION]', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{align\*?\}.*?\\end\{align\*?\}', '[EQUATION]', text, flags=re.DOTALL)
    
    # Remove remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{[^}]*\}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
    
    # Clean up braces
    text = re.sub(r'[{}]', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def extract_latex_command(content: str, command: str) -> Optional[str]:
    """Extract content of a LaTeX command like \\title{...}."""
    pattern = rf'\\{command}\{{([^}}]*)\}}'
    match = re.search(pattern, content)
    return match.group(1).strip() if match else None


def extract_latex_environment(content: str, environment: str) -> Optional[str]:
    """Extract content of a LaTeX environment like \\begin{abstract}...\\end{abstract}."""
    pattern = rf'\\begin\{{{environment}\}}(.*?)\\end\{{{environment}\}}'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return latex_to_text(match.group(1).strip())
    return None


def extract_sections(content: str) -> Dict[str, str]:
    """Extract all sections from a LaTeX document."""
    sections = {}
    
    # Find all section commands
    section_pattern = r'\\(section|subsection|subsubsection)\*?\{([^}]*)\}'
    
    # Split content by sections
    parts = re.split(section_pattern, content)
    
    current_section = None
    for i, part in enumerate(parts):
        if part in ['section', 'subsection', 'subsubsection']:
            # Next part is the section title
            if i + 1 < len(parts):
                current_section = parts[i + 1].strip()
        elif current_section and part.strip():
            # This is section content
            if current_section not in sections:
                sections[current_section] = latex_to_text(part)[:2000]
    
    return sections


def extract_citations(content: str) -> List[str]:
    """Extract all citation keys from LaTeX content."""
    citations = []
    
    # Match \cite{key1, key2, ...} patterns
    cite_pattern = r'\\cite[pt]?\{([^}]+)\}'
    matches = re.findall(cite_pattern, content)
    
    for match in matches:
        # Split by comma for multiple citations
        keys = [k.strip() for k in match.split(',')]
        citations.extend(keys)
    
    return list(set(citations))


def extract_figures_and_tables(content: str) -> Dict[str, List[Dict]]:
    """Extract figure and table information from LaTeX."""
    result = {"figures": [], "tables": []}
    
    # Extract figures
    figure_pattern = r'\\begin\{figure\}.*?\\caption\{([^}]*)\}.*?\\label\{([^}]*)\}.*?\\end\{figure\}'
    for match in re.finditer(figure_pattern, content, re.DOTALL):
        result["figures"].append({
            "caption": match.group(1).strip(),
            "label": match.group(2).strip()
        })
    
    # Extract tables
    table_pattern = r'\\begin\{table\}.*?\\caption\{([^}]*)\}.*?\\label\{([^}]*)\}.*?\\end\{table\}'
    for match in re.finditer(table_pattern, content, re.DOTALL):
        result["tables"].append({
            "caption": match.group(1).strip(),
            "label": match.group(2).strip()
        })
    
    return result
