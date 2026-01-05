"""
ExperimentEvidenceAgent - Maps experiments to paper claims and results.

Responsibility:
- Map experiments → logs → tables → figures
- Detect missing experiment provenance
- Identify untraceable results
"""

import os
import json
from typing import Dict, List, Optional
from google.adk.agents import Agent

from ..tools.log_analyzer import (
    analyze_training_logs,
    extract_metrics_from_log,
)


def analyze_experiment_logs(log_paths_csv: str = "") -> Dict:
    """
    Analyze experiment log files.
    
    Args:
        log_paths_csv: Comma-separated list of paths to log files
        
    Returns:
        Dictionary with experiment analysis results
    """
    result = {
        "status": "success",
        "logs_analyzed": [],
        "extracted_metrics": {},
        "issues": []
    }
    
    # Parse CSV path list
    log_paths = [p.strip() for p in log_paths_csv.split(",") if p.strip()]
    
    if not log_paths:
        result["issues"].append("No log paths provided")
        return result
    
    # Analyze log files
    for log_path in log_paths:
        if os.path.exists(log_path):
            log_analysis = analyze_training_logs(log_path)
            
            if log_analysis["status"] == "success":
                result["logs_analyzed"].append({
                    "path": log_path,
                    "metrics": log_analysis.get("metrics", {}),
                    "issues": log_analysis.get("issues", [])
                })
                
                # Extract key metrics
                metrics = extract_metrics_from_log(log_path)
                for key, value in metrics.items():
                    result["extracted_metrics"][f"{os.path.basename(log_path)}:{key}"] = value
            else:
                result["issues"].append(f"Failed to analyze {log_path}: {log_analysis.get('error_message')}")
        else:
            result["issues"].append(f"Log file not found: {log_path}")
    
    return result


def analyze_experiment_scripts(script_paths_csv: str = "") -> Dict:
    """
    Analyze experiment script files.
    
    Args:
        script_paths_csv: Comma-separated list of paths to Python scripts
        
    Returns:
        Dictionary with script analysis results
    """
    result = {
        "status": "success",
        "scripts_analyzed": [],
        "issues": []
    }
    
    # Parse CSV path list
    script_paths = [p.strip() for p in script_paths_csv.split(",") if p.strip()]
    
    if not script_paths:
        result["issues"].append("No script paths provided")
        return result
    
    for script_path in script_paths:
        if os.path.exists(script_path):
            try:
                with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                result["scripts_analyzed"].append({
                    "path": script_path,
                    "has_training_loop": any(kw in content.lower() for kw in ['train', 'epoch', 'optimizer']),
                    "has_evaluation": any(kw in content.lower() for kw in ['eval', 'test', 'valid']),
                    "has_logging": any(kw in content for kw in ['print(', 'logging.', 'writer.', 'wandb.']),
                })
            except Exception as e:
                result["issues"].append(f"Failed to analyze script {script_path}: {str(e)}")
        else:
            result["issues"].append(f"Script not found: {script_path}")
    
    return result


# Define the ExperimentEvidenceAgent
experiment_evidence_agent = Agent(
    name="ExperimentEvidenceAgent",
    model="gemini-2.0-flash",
    description="Maps paper results to experimental evidence and identifies untraceable claims.",
    instruction="""You are an Experiment Evidence Agent. Your task is to verify that reported results in a research paper can be traced back to actual experimental evidence.

You will receive:
1. **Paper Analysis** (from PaperParserAgent via state key `paper_analysis`): Contains claims, reported results, datasets, and metrics
2. **Experiment Files**: Log files and scripts from the experiments

Your responsibilities:

1. **Map Results to Evidence**: For each reported result in the paper, try to find corresponding evidence in the experiment logs.
   - Match metric names (accuracy, loss, F1, etc.)
   - Compare numerical values
   - Note the source file for each match

2. **Identify Untraceable Results**: Flag results that cannot be verified from the available logs.
   - Results with no matching log entries
   - Results with significant discrepancies

3. **Check Experiment Completeness**: Verify that necessary experiments were run.
   - Are all claimed datasets represented in logs?
   - Are all reported metrics logged?

4. **Assess Evidence Strength**: Rate each mapping as:
   - **strong**: Direct match with consistent values
   - **moderate**: Partial match or minor discrepancies
   - **weak**: Possible match but cannot verify
   - **none**: No evidence found

**Input from Previous Agent**:
Look for paper analysis from PaperParserAgent in the conversation history.

**Output Format (JSON)**:
```json
{
  "experiment_map": {
    "result_1": {
      "claimed_result": "95.2% accuracy on CIFAR-10",
      "log_file": "training_log.csv",
      "script_file": "train.py",
      "evidence_strength": "strong",
      "notes": "Exact match found in log"
    }
  },
  "untraceable_results": [
    "Result X claimed in Table 2 - no corresponding log entry"
  ],
  "missing_experiments": [
    "No logs found for CIFAR-100 experiments mentioned in Section 4.3"
  ]
}
```

Use the analyze_experiment_logs tool with comma-separated file paths to analyze logs. Be thorough in checking each claimed result.""",
    tools=[analyze_experiment_logs, analyze_experiment_scripts],
    output_key="experiment_evidence"
)
