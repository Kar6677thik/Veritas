"""
PaperParserAgent - Parses research papers and extracts structured information.

Responsibility:
- Parse the paper (PDF or LaTeX)
- Extract claimed contributions
- Identify datasets, metrics, baselines
- Extract reported results and their locations
"""

import os
import json
from typing import Dict, List, Optional
from google.adk.agents import Agent

from ..tools.pdf_parser import parse_pdf, extract_text_from_pdf
from ..tools.latex_parser import parse_latex


def parse_paper_file(file_path: str) -> Dict:
    """
    Parse a paper file (PDF or LaTeX) and extract text content.
    
    Args:
        file_path: Path to the paper file
        
    Returns:
        Dictionary with parsed content and status
    """
    if not file_path:
        return {
            "status": "error",
            "error_message": "No file path provided"
        }
    
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error_message": f"File not found: {file_path}"
        }
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in ['.tex', '.latex']:
        return parse_latex(file_path)
    elif ext in ['.txt', '.md']:
        # Plain text file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {
                "status": "success",
                "full_text": content,
                "title": None,
                "abstract": None
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": f"Failed to read file: {str(e)}"
            }
    else:
        return {
            "status": "error",
            "error_message": f"Unsupported file format: {ext}"
        }


def analyze_paper_content(paper_text: str) -> Dict:
    """
    Analyze paper text to extract claims, results, datasets, and metrics.
    
    This is a helper function that provides structured extraction.
    The actual deep analysis is performed by the LLM agent.
    
    Args:
        paper_text: The full text content of the paper
        
    Returns:
        Dictionary with preliminary extraction results
    """
    import re
    
    result = {
        "text_length": len(paper_text),
        "has_abstract": False,
        "has_experiments": False,
        "has_results": False,
        "table_references": [],
        "figure_references": [],
        "dataset_mentions": [],
        "metric_mentions": [],
    }
    
    text_lower = paper_text.lower()
    
    # Check for common sections
    result["has_abstract"] = "abstract" in text_lower
    result["has_experiments"] = any(kw in text_lower for kw in ["experiment", "evaluation", "results"])
    result["has_results"] = "result" in text_lower
    
    # Find table and figure references
    result["table_references"] = list(set(re.findall(r'table\s+(\d+)', text_lower)))
    result["figure_references"] = list(set(re.findall(r'figure\s+(\d+)', text_lower)))
    
    # Common dataset names
    dataset_patterns = [
        r'\b(imagenet|cifar|mnist|coco|squad|glue|wmt|penn.?treebank|imdb|yelp|amazon.?reviews)\b',
        r'\b(\w+(?:net|bench|dataset|corpus|100|1000|10k|1m))\b'
    ]
    
    for pattern in dataset_patterns:
        matches = re.findall(pattern, text_lower)
        result["dataset_mentions"].extend(matches)
    
    result["dataset_mentions"] = list(set(result["dataset_mentions"]))[:20]
    
    # Common metrics
    metric_patterns = [
        r'\b(accuracy|precision|recall|f1.?score|auc|roc|bleu|rouge|perplexity|mse|rmse|mae|loss)\b',
        r'\b(top.?\d+|map|mrr|ndcg|hit.?rate)\b'
    ]
    
    for pattern in metric_patterns:
        matches = re.findall(pattern, text_lower)
        result["metric_mentions"].extend(matches)
    
    result["metric_mentions"] = list(set(result["metric_mentions"]))[:20]
    
    return result


# Tool function for the agent
def parse_and_analyze_paper(file_path: str = None, paper_text: str = None) -> Dict:
    """
    Parse a research paper and perform preliminary analysis.
    
    Args:
        file_path: Path to the paper file (PDF, LaTeX, or text)
        paper_text: Direct paper text (if already extracted)
        
    Returns:
        Dictionary with parsed content and analysis
    """
    if paper_text:
        # Use provided text directly
        content = paper_text
        parsed = {"status": "success", "full_text": content}
    elif file_path:
        # Parse from file
        parsed = parse_paper_file(file_path)
        if parsed["status"] == "error":
            return parsed
        content = parsed.get("full_text", "")
    else:
        return {
            "status": "error",
            "error_message": "Either file_path or paper_text must be provided"
        }
    
    # Perform preliminary analysis
    analysis = analyze_paper_content(content)
    
    return {
        "status": "success",
        "title": parsed.get("title"),
        "abstract": parsed.get("abstract"),
        "full_text": content[:50000],  # Limit text length for LLM
        "analysis": analysis
    }


# Define the PaperParserAgent
paper_parser_agent = Agent(
    name="PaperParserAgent",
    model="gemini-2.0-flash",
    description="Parses research papers and extracts claims, results, datasets, and metrics.",
    instruction="""You are a Research Paper Parser Agent. Your task is to analyze research papers and extract structured information.

When given paper content (either as text or file path), you must:

1. **Extract Main Claims**: Identify the key contributions and claims made by the authors.
   - Look for phrases like "we propose", "we introduce", "our contribution", "we show that"
   - Focus on novel claims, not background information

2. **Extract Reported Results**: Find all numerical results reported in the paper.
   - Include the metric name, value, and location (e.g., "Table 1", "Section 4.2")
   - Note any comparisons to baselines

3. **Identify Datasets**: List all datasets mentioned or used.
   - Include both benchmark datasets and custom datasets
   - Note if dataset details are missing

4. **Identify Metrics**: List all evaluation metrics used.
   - Include both common metrics (accuracy, F1) and domain-specific ones
   - Note if metrics are properly defined

5. **Identify Baselines**: List methods the paper compares against.

**Output Format (JSON)**:
```json
{
  "claims": ["claim 1", "claim 2", ...],
  "reported_results": [
    {"metric_name": "accuracy", "value": "95.2%", "location": "Table 1", "context": "on CIFAR-10"}
  ],
  "datasets": ["dataset1", "dataset2"],
  "metrics": ["metric1", "metric2"],
  "baselines": ["baseline1", "baseline2"],
  "paper_title": "Title if found",
  "abstract": "Abstract if found"
}
```

Use the parse_and_analyze_paper tool to read paper files. Always provide structured JSON output.
Be thorough but focus on the most important elements. If information is missing, note it explicitly.""",
    tools=[parse_and_analyze_paper],
    output_key="paper_analysis"
)
