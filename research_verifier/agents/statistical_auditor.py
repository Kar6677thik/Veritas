"""
StatisticalAuditorAgent - Evaluates statistical validity of claims.

Responsibility:
- Evaluate variance and significance
- Detect statistical issues
- Identify metric misuse
"""

import os
import json
import re
from typing import Dict, List, Optional
from google.adk.agents import Agent

from ..tools.log_analyzer import analyze_training_logs


def analyze_statistical_validity(log_paths_csv: str = "") -> Dict:
    """
    Analyze statistical validity of experimental results.
    
    Args:
        log_paths_csv: Comma-separated paths to experiment log files
        
    Returns:
        Dictionary with statistical analysis
    """
    result = {
        "status": "success",
        "variance_analysis": [],
        "significance_issues": [],
        "metric_issues": [],
        "recommendations": []
    }
    
    # Parse CSV path list
    log_paths = [p.strip() for p in log_paths_csv.split(",") if p.strip()]
    
    if log_paths:
        for log_path in log_paths:
            if os.path.exists(log_path):
                log_analysis = analyze_training_logs(log_path)
                
                if log_analysis["status"] == "success":
                    metrics = log_analysis.get("metrics", {})
                    
                    for metric_name, metric_data in metrics.items():
                        if isinstance(metric_data, dict) and "variance" in metric_data:
                            variance = metric_data["variance"]
                            count = metric_data.get("count", 0)
                            
                            # Check for high variance
                            if variance > 0.01 and count > 1:
                                cv = (variance ** 0.5) / abs(metric_data.get("max", 1)) if metric_data.get("max", 0) != 0 else 0
                                
                                result["variance_analysis"].append({
                                    "metric": metric_name,
                                    "variance": variance,
                                    "coefficient_of_variation": cv,
                                    "sample_count": count,
                                    "concern_level": "high" if cv > 0.3 else "medium" if cv > 0.1 else "low"
                                })
                                
                                if cv > 0.3:
                                    result["recommendations"].append(
                                        f"High variance in {metric_name} (CV={cv:.2f}). Consider running multiple seeds."
                                    )
    
    return result


def check_multiple_run_evidence(log_directory: str = "") -> Dict:
    """
    Check if experiments were run multiple times with different seeds.
    
    Args:
        log_directory: Directory containing experiment logs
        
    Returns:
        Dictionary with multi-run analysis
    """
    result = {
        "status": "success",
        "runs_detected": 0,
        "seeds_found": [],
        "issues": []
    }
    
    if not log_directory or not os.path.isdir(log_directory):
        result["issues"].append("No log directory provided or directory not found")
        return result
    
    # Look for multiple run files
    import glob
    
    log_files = glob.glob(os.path.join(log_directory, "**/*.*"), recursive=True)
    
    # Simple heuristic: count files that look like run logs
    run_patterns = [
        r'run[_\-]?\d+',
        r'seed[_\-]?\d+',
        r'exp[_\-]?\d+',
    ]
    
    for log_file in log_files:
        filename = os.path.basename(log_file)
        for pattern in run_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                result["runs_detected"] += 1
                break
    
    if result["runs_detected"] < 3:
        result["issues"].append(
            f"Only {result['runs_detected']} runs detected. Statistical significance typically requires 3+ runs."
        )
    
    return result


# Define the StatisticalAuditorAgent  
statistical_auditor_agent = Agent(
    name="StatisticalAuditorAgent",
    model="gemini-2.0-flash",
    description="Evaluates statistical validity of claims and identifies weak statistical practices.",
    instruction="""You are a Statistical Auditor Agent. Your task is to evaluate the statistical validity of experimental results and identify potential issues.

You will receive:
1. **Experiment Evidence** (from ExperimentEvidenceAgent via state key `experiment_evidence`): Contains mappings of results to experimental evidence
2. **Paper Analysis** (via state key `paper_analysis`): Contains the reported results

Your responsibilities:

1. **Evaluate Variance Reporting**: Check if results include proper uncertainty measures.
   - Are standard deviations or confidence intervals reported?
   - Is variance consistent across metrics?

2. **Check Statistical Significance**: Look for:
   - Multiple experimental runs
   - Proper baseline comparisons
   - Significance tests (t-test, paired tests, etc.)

3. **Identify Metric Misuse**: Flag potential issues like:
   - Using metrics inappropriate for the task
   - Cherry-picking best results
   - Reporting test accuracy without validation
   - Overfitting indicators

4. **Assess Claim Strength**: Rate claims as:
   - **strong**: Well-supported with proper statistics
   - **moderate**: Reasonable but missing some rigor
   - **weak**: Insufficient statistical evidence

**Input from Previous Agents**:
Look for analysis from PaperParserAgent and ExperimentEvidenceAgent in the conversation history.

**Output Format (JSON)**:
```json
{
  "weak_claims": [
    {
      "claim": "Our method achieves 95.2% accuracy",
      "reason": "No standard deviation reported, unclear if statistically significant",
      "severity": "medium",
      "recommendation": "Run with 5 seeds and report mean ± std"
    }
  ],
  "variance_issues": [
    "Accuracy reported without confidence intervals",
    "Only single seed used for experiments"
  ],
  "significance_issues": [
    "No significance test comparing to baseline"
  ],
  "metric_misuse": [
    "Using accuracy for imbalanced dataset - should prefer F1 or AUC"
  ]
}
```

Use the analyze_statistical_validity tool with comma-separated log paths. Be rigorous but fair.""",
    tools=[analyze_statistical_validity, check_multiple_run_evidence],
    output_key="statistical_audit"
)
