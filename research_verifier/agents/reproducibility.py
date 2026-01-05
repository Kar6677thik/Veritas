"""
ReproducibilityAgent - Checks reproducibility information in experiments.

Responsibility:
- Extract/infer seeds, hardware, library versions
- Flag missing reproducibility information
"""

import os
import json
from typing import Dict, List, Optional
from google.adk.agents import Agent

from ..tools.log_analyzer import extract_reproducibility_info, extract_seeds_from_text


def analyze_reproducibility(script_paths_csv: str = "", log_paths_csv: str = "") -> Dict:
    """
    Analyze experiment files for reproducibility information.
    
    Args:
        script_paths_csv: Comma-separated paths to experiment scripts
        log_paths_csv: Comma-separated paths to log files
        
    Returns:
        Dictionary with reproducibility analysis
    """
    result = {
        "status": "success",
        "seeds_found": [],
        "hardware_info": [],
        "library_versions": {},
        "hyperparameters": {},
        "missing_items": [],
        "reproducibility_score": 0
    }
    
    # Parse CSV path lists
    script_paths = [p.strip() for p in script_paths_csv.split(",") if p.strip()]
    log_paths = [p.strip() for p in log_paths_csv.split(",") if p.strip()]
    
    score = 0
    
    # Analyze scripts
    if script_paths:
        for script_path in script_paths:
            if os.path.exists(script_path):
                script_analysis = extract_reproducibility_info(script_path)
                
                if script_analysis["status"] == "success":
                    result["seeds_found"].extend(script_analysis.get("seeds", []))
                    result["hardware_info"].extend(script_analysis.get("hardware_refs", []))
                    # Handle imports - it's a list of library names, not a dict
                    imports = script_analysis.get("imports", [])
                    if isinstance(imports, list):
                        for lib in imports:
                            result["library_versions"][lib] = "found in imports"
                    elif isinstance(imports, dict):
                        result["library_versions"].update(imports)
                    result["hyperparameters"].update(script_analysis.get("hyperparameters", {}))
    
    # Analyze logs for seeds
    if log_paths:
        for log_path in log_paths:
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    seeds = extract_seeds_from_text(content)
                    result["seeds_found"].extend(seeds)
                except Exception:
                    pass
    
    # Deduplicate
    result["seeds_found"] = list(set(result["seeds_found"]))
    result["hardware_info"] = list(set(result["hardware_info"]))
    
    # Calculate reproducibility score and identify missing items
    checklist = [
        ("Random seed set", bool(result["seeds_found"]), 20),
        ("Hardware specified", bool(result["hardware_info"]), 15),
        ("Library imports found", bool(result["library_versions"]), 10),
        ("Hyperparameters documented", bool(result["hyperparameters"]), 20),
        ("Multiple seeds used", len(result["seeds_found"]) > 1, 15),
        ("GPU/Device specified", any("cuda" in str(h).lower() or "gpu" in str(h).lower() for h in result["hardware_info"]), 10),
        ("Learning rate specified", "learning_rate" in result["hyperparameters"], 5),
        ("Batch size specified", "batch_size" in result["hyperparameters"], 5),
    ]
    
    for item_name, is_present, points in checklist:
        if is_present:
            score += points
        else:
            result["missing_items"].append(item_name)
    
    result["reproducibility_score"] = score
    
    return result


def check_reproducibility_statement(paper_text: str = "") -> Dict:
    """
    Check if paper includes reproducibility statement or appendix.
    
    Args:
        paper_text: Full text of the paper
        
    Returns:
        Dictionary with reproducibility statement analysis
    """
    import re
    
    result = {
        "status": "success",
        "has_reproducibility_section": False,
        "has_code_availability": False,
        "has_data_availability": False,
        "mentions_found": []
    }
    
    if not paper_text:
        return result
    
    text_lower = paper_text.lower()
    
    # Check for reproducibility section
    repro_patterns = [
        r'reproducib',
        r'implementation\s+details',
        r'experimental\s+setup',
        r'training\s+details',
    ]
    
    for pattern in repro_patterns:
        if re.search(pattern, text_lower):
            result["has_reproducibility_section"] = True
            result["mentions_found"].append(pattern)
    
    # Check for code availability
    code_patterns = [
        r'code\s+(?:is\s+)?available',
        r'github\.com',
        r'open.?source',
        r'released\s+(?:the\s+)?code',
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, text_lower):
            result["has_code_availability"] = True
            break
    
    # Check for data availability
    data_patterns = [
        r'data\s+(?:is\s+)?available',
        r'publicly\s+available\s+dataset',
        r'dataset\s+(?:is\s+)?released',
    ]
    
    for pattern in data_patterns:
        if re.search(pattern, text_lower):
            result["has_data_availability"] = True
            break
    
    return result


# Define the ReproducibilityAgent
reproducibility_agent = Agent(
    name="ReproducibilityAgent",
    model="gemini-2.0-flash",
    description="Checks for reproducibility information and flags missing details.",
    instruction="""You are a Reproducibility Agent. Your task is to evaluate whether the research can be reproduced and identify missing reproducibility information.

You will analyze:
1. **Experiment Scripts**: Python files for training/evaluation
2. **Log Files**: Training logs that may contain configuration

Your responsibilities:

1. **Check for Random Seeds**:
   - Are random seeds set for numpy, torch, tensorflow?
   - Is the same seed used across components?
   - Are multiple seeds run for variance estimation?

2. **Verify Hardware Specifications**:
   - GPU type and count specified?
   - Memory requirements mentioned?
   - Training time reported?

3. **Check Library Versions**:
   - Are key library versions pinned?
   - Is a requirements.txt or environment file provided?
   - Are version-sensitive libraries identified?

4. **Verify Hyperparameters**:
   - Learning rate, batch size, optimizer?
   - Model architecture details?
   - Training epochs/steps?

5. **Check Code/Data Availability**:
   - Is code released?
   - Is data publicly available?
   - Are preprocessing steps described?

**Reproducibility Checklist**:
- [ ] Random seeds for all sources of randomness
- [ ] GPU/hardware specifications
- [ ] Library versions (especially PyTorch, TensorFlow, transformers)
- [ ] Complete hyperparameters
- [ ] Data preprocessing steps
- [ ] Training time and resources needed
- [ ] Code availability statement

**Output Format (JSON)**:
```json
{
  "missing_reproducibility_items": [
    "Random seed not found in training script",
    "GPU specifications not mentioned",
    "Library versions not pinned",
    "Data preprocessing steps unclear"
  ],
  "found_seeds": ["42", "123"],
  "found_hardware": ["NVIDIA V100", "cuda"],
  "found_library_versions": {"torch": "seen in imports", "transformers": "seen in imports"},
  "reproducibility_score": 65,
  "recommendations": [
    "Add explicit random seed setting",
    "Create requirements.txt with pinned versions"
  ]
}
```

Use the analyze_reproducibility tool with comma-separated file paths. Score 0-100 where 100 is fully reproducible.""",
    tools=[analyze_reproducibility, check_reproducibility_statement],
    output_key="reproducibility_analysis"
)
