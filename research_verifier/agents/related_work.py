"""
RelatedWorkBaselineAgent - Analyzes citations and baseline comparisons.

Responsibility:
- Analyze citations from BibTeX
- Detect missing standard baselines
- Identify weak or incomplete comparisons
"""

import os
import json
from typing import Dict, List, Optional
from google.adk.agents import Agent

from ..tools.bib_parser import parse_bibtex, get_citation_info, find_standard_baselines


def analyze_citations(bibtex_path: str = None) -> Dict:
    """
    Analyze citations from a BibTeX file.
    
    Args:
        bibtex_path: Path to the .bib file
        
    Returns:
        Dictionary with citation analysis
    """
    if not bibtex_path:
        return {
            "status": "error",
            "error_message": "No BibTeX file path provided"
        }
    
    if not os.path.exists(bibtex_path):
        return {
            "status": "error",
            "error_message": f"BibTeX file not found: {bibtex_path}"
        }
    
    return get_citation_info(bibtex_path)


def check_baseline_coverage(
    paper_analysis: str,
    bibtex_path: str = None,
    domain: str = "ML"
) -> Dict:
    """
    Check if standard baselines are covered in the paper.
    
    Args:
        paper_analysis: JSON string of paper analysis
        bibtex_path: Path to BibTeX file
        domain: Research domain (ML, NLP, CV)
        
    Returns:
        Dictionary with baseline coverage analysis
    """
    result = {
        "status": "success",
        "covered_baselines": [],
        "missing_baselines": [],
        "recommendations": []
    }
    
    # Parse paper analysis
    try:
        if isinstance(paper_analysis, str):
            paper_data = json.loads(paper_analysis)
        else:
            paper_data = paper_analysis
    except json.JSONDecodeError:
        paper_data = {}
    
    # Get baselines mentioned in paper
    paper_baselines = paper_data.get("baselines", [])
    result["covered_baselines"] = paper_baselines
    
    # If we have a BibTeX file, check for standard baselines
    if bibtex_path and os.path.exists(bibtex_path):
        citation_result = parse_bibtex(bibtex_path)
        
        if citation_result["status"] == "success":
            entries = citation_result.get("entries", [])
            missing = find_standard_baselines(entries, domain)
            
            # Filter out baselines that are mentioned in the paper
            paper_text_lower = str(paper_data).lower()
            for baseline in missing:
                if baseline.lower() not in paper_text_lower:
                    result["missing_baselines"].append(baseline)
    
    # Generate recommendations
    if result["missing_baselines"]:
        result["recommendations"].append(
            f"Consider comparing against: {', '.join(result['missing_baselines'][:5])}"
        )
    
    if len(result["covered_baselines"]) < 3:
        result["recommendations"].append(
            "Paper compares against fewer than 3 baselines. Consider adding more comparisons."
        )
    
    return result


def analyze_related_work_coverage(paper_text: str) -> Dict:
    """
    Analyze the related work section for completeness.
    
    Args:
        paper_text: Full text of the paper
        
    Returns:
        Dictionary with related work analysis
    """
    import re
    
    result = {
        "status": "success",
        "has_related_work_section": False,
        "related_work_length": 0,
        "citation_density": 0,
        "gaps": [],
        "recommendations": []
    }
    
    text_lower = paper_text.lower()
    
    # Check for related work section
    rw_patterns = [
        r'related\s+work',
        r'background',
        r'prior\s+work',
        r'literature\s+review'
    ]
    
    for pattern in rw_patterns:
        if re.search(pattern, text_lower):
            result["has_related_work_section"] = True
            break
    
    # Estimate related work section length
    rw_match = re.search(
        r'(?:related\s+work|background)(.*?)(?:method|approach|model|experiment|\d+\.)',
        text_lower,
        re.DOTALL
    )
    
    if rw_match:
        result["related_work_length"] = len(rw_match.group(1).split())
    
    # Count citation references
    citations = re.findall(r'\[(?:\d+(?:,\s*\d+)*|\w+\s+et\s+al\.)\]', paper_text)
    result["citation_density"] = len(citations)
    
    # Check for gaps
    if not result["has_related_work_section"]:
        result["gaps"].append("No dedicated related work section found")
    
    if result["related_work_length"] < 200:
        result["gaps"].append("Related work section appears brief")
    
    if result["citation_density"] < 15:
        result["gaps"].append(f"Low citation count ({result['citation_density']})")
    
    return result


# Define the RelatedWorkBaselineAgent
related_work_agent = Agent(
    name="RelatedWorkBaselineAgent",
    model="gemini-2.0-flash",
    description="Analyzes citations and baseline comparisons for completeness.",
    instruction="""You are a Related Work & Baseline Analysis Agent. Your task is to evaluate the paper's related work coverage and baseline comparisons.

You will receive:
1. **Paper Analysis** (via state key `paper_analysis`): Contains claims, baselines, and paper content
2. **BibTeX File**: If provided, you can analyze the citation list

Your responsibilities:

1. **Analyze Baseline Comparisons**:
   - Are standard baselines included?
   - Are comparisons fair (same settings, datasets)?
   - Are recent state-of-the-art methods compared?
   - Are baseline implementations appropriate (official vs. re-implementation)?

2. **Evaluate Related Work Coverage**:
   - Is the related work section comprehensive?
   - Are key foundational papers cited?
   - Are recent papers in the field covered?
   - Is the positioning against prior work clear?

3. **Identify Missing Standard Baselines**: Based on the research area:
   - For NLP: BERT, GPT, RoBERTa, T5, etc.
   - For CV: ResNet, VGG, EfficientNet, ViT, etc.
   - For ML: XGBoost, Random Forest, MLP, etc.

4. **Check Citation Quality**:
   - Are citations recent enough?
   - Is there potential self-citation bias?
   - Are seminal papers cited?

**Input from Previous Agents**:
Look for analysis from PaperParserAgent in the conversation history.

**Output Format (JSON)**:
```json
{
  "missing_baselines": [
    "ResNet (standard CV baseline not compared)",
    "BERT-base (common NLP baseline missing)"
  ],
  "related_work_gaps": [
    "No coverage of recent work on X from 2024",
    "Missing citation to foundational paper Y"
  ],
  "weak_comparisons": [
    "Baseline A uses different hyperparameters than reported in original paper",
    "Comparison on subset of test set only"
  ],
  "citation_issues": [
    "Over 60% of citations are self-citations",
    "Most citations are from before 2020"
  ]
}
```

Use the analyze_citations and check_baseline_coverage tools. Focus on issues that reviewers would likely catch.""",
    tools=[analyze_citations, check_baseline_coverage, analyze_related_work_coverage],
    output_key="related_work_analysis"
)
