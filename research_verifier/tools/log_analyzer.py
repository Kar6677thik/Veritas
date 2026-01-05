"""Log and script analysis utilities for reproducibility checking."""

import os
import re
import csv
from typing import Dict, List, Optional, Any
from pathlib import Path


def analyze_training_logs(file_path: str) -> Dict:
    """
    Analyze training logs to extract metrics and identify issues.
    
    Args:
        file_path: Path to the log file (CSV, TXT, or JSON)
        
    Returns:
        Dictionary with extracted metrics and analysis
    """
    if not os.path.exists(file_path):
        return {
            "status": "error",
            "error_message": f"File not found: {file_path}"
        }
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.csv':
        return analyze_csv_log(file_path)
    elif file_ext == '.json':
        return analyze_json_log(file_path)
    else:
        return analyze_text_log(file_path)


def analyze_csv_log(file_path: str) -> Dict:
    """Analyze a CSV log file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return {"status": "success", "metrics": {}, "issues": ["Empty log file"]}
        
        # Extract numeric columns as metrics
        metrics = {}
        for key in rows[0].keys():
            values = []
            for row in rows:
                try:
                    val = float(row.get(key, ''))
                    values.append(val)
                except (ValueError, TypeError):
                    continue
            
            if values:
                metrics[key] = {
                    "min": min(values),
                    "max": max(values),
                    "final": values[-1],
                    "count": len(values),
                    "variance": calculate_variance(values) if len(values) > 1 else 0
                }
        
        # Check for issues
        issues = []
        
        for metric_name, metric_data in metrics.items():
            # Check for high variance
            if metric_data["variance"] > 0.1 and "loss" not in metric_name.lower():
                if metric_data["max"] > 0:
                    cv = (metric_data["variance"] ** 0.5) / abs(metric_data["max"])
                    if cv > 0.3:
                        issues.append(f"High variance in {metric_name} (CV={cv:.2f})")
            
            # Check for non-convergence
            if "loss" in metric_name.lower():
                if metric_data["final"] > metric_data["min"] * 1.5:
                    issues.append(f"{metric_name} may not have converged properly")
        
        return {
            "status": "success",
            "metrics": metrics,
            "num_rows": len(rows),
            "columns": list(rows[0].keys()),
            "issues": issues
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to analyze CSV log: {str(e)}"
        }


def analyze_json_log(file_path: str) -> Dict:
    """Analyze a JSON log file."""
    try:
        import json
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Try to parse as JSON lines or single JSON
        try:
            data = json.loads(content)
            if isinstance(data, list):
                rows = data
            else:
                rows = [data]
        except json.JSONDecodeError:
            # Try JSON lines format
            rows = []
            for line in content.strip().split('\n'):
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        if not rows:
            return {"status": "success", "metrics": {}, "issues": ["Empty or invalid JSON log"]}
        
        # Extract metrics similar to CSV
        metrics = {}
        for key in rows[0].keys() if isinstance(rows[0], dict) else []:
            values = []
            for row in rows:
                try:
                    val = float(row.get(key, ''))
                    values.append(val)
                except (ValueError, TypeError):
                    continue
            
            if values:
                metrics[key] = {
                    "min": min(values),
                    "max": max(values),
                    "final": values[-1],
                    "count": len(values)
                }
        
        return {
            "status": "success",
            "metrics": metrics,
            "num_entries": len(rows),
            "issues": []
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to analyze JSON log: {str(e)}"
        }


def analyze_text_log(file_path: str) -> Dict:
    """Analyze a plain text log file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract numeric values with labels
        metrics = {}
        
        # Common patterns in training logs
        patterns = [
            r'(?i)(loss|accuracy|acc|f1|precision|recall|auc|epoch|step|lr|learning.?rate)[:\s=]+([0-9]+\.?[0-9]*)',
            r'(?i)(train|val|test|eval)[_\s]*(loss|accuracy|acc|f1)[:\s=]+([0-9]+\.?[0-9]*)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if len(groups) == 2:
                    key, value = groups
                elif len(groups) == 3:
                    key = f"{groups[0]}_{groups[1]}"
                    value = groups[2]
                else:
                    continue
                
                key = key.lower().strip()
                try:
                    val = float(value)
                    if key not in metrics:
                        metrics[key] = []
                    metrics[key].append(val)
                except ValueError:
                    continue
        
        # Summarize metrics
        metric_summary = {}
        for key, values in metrics.items():
            if values:
                metric_summary[key] = {
                    "min": min(values),
                    "max": max(values),
                    "final": values[-1],
                    "count": len(values)
                }
        
        # Extract any seed information
        seed_info = extract_seeds_from_text(content)
        
        return {
            "status": "success",
            "metrics": metric_summary,
            "seed_info": seed_info,
            "issues": []
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to analyze text log: {str(e)}"
        }


def extract_metrics_from_log(file_path: str) -> Dict[str, Any]:
    """
    Extract key metrics from a log file for comparison with paper claims.
    
    Returns a simplified dictionary of metric names to their final values.
    """
    result = analyze_training_logs(file_path)
    
    if result["status"] == "error":
        return {}
    
    metrics = result.get("metrics", {})
    
    # Return final values for each metric
    return {
        key: data.get("final", data.get("max", None))
        for key, data in metrics.items()
        if isinstance(data, dict)
    }


def extract_reproducibility_info(script_path: str) -> Dict:
    """
    Extract reproducibility information from a Python script.
    
    Looks for:
    - Random seeds
    - Library imports (with potential versions)
    - Hardware specifications
    - Hyperparameters
    """
    if not os.path.exists(script_path):
        return {
            "status": "error",
            "error_message": f"File not found: {script_path}"
        }
    
    try:
        with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        result = {
            "status": "success",
            "seeds": [],
            "imports": [],
            "hardware_refs": [],
            "hyperparameters": {},
            "missing_items": []
        }
        
        # Extract seeds
        result["seeds"] = extract_seeds_from_text(content)
        
        # Extract imports
        import_pattern = r'^(?:from|import)\s+([a-zA-Z0-9_]+)'
        result["imports"] = list(set(re.findall(import_pattern, content, re.MULTILINE)))
        
        # Look for hardware specifications
        hardware_patterns = [
            r'(?i)(cuda|gpu|cpu|tpu|device)',
            r'(?i)torch\.device\(["\']([^"\']+)["\']\)',
            r'(?i)nvidia|geforce|tesla|v100|a100'
        ]
        
        for pattern in hardware_patterns:
            matches = re.findall(pattern, content)
            result["hardware_refs"].extend(matches)
        
        result["hardware_refs"] = list(set(result["hardware_refs"]))
        
        # Extract common hyperparameters
        hyperparam_patterns = [
            (r'(?i)(learning.?rate|lr)\s*=\s*([0-9\.e\-]+)', 'learning_rate'),
            (r'(?i)(batch.?size)\s*=\s*(\d+)', 'batch_size'),
            (r'(?i)(epochs?|num.?epochs?)\s*=\s*(\d+)', 'epochs'),
            (r'(?i)(hidden.?size|hidden.?dim)\s*=\s*(\d+)', 'hidden_size'),
            (r'(?i)(dropout)\s*=\s*([0-9\.]+)', 'dropout'),
        ]
        
        for pattern, key in hyperparam_patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    result["hyperparameters"][key] = float(match.group(2))
                except ValueError:
                    result["hyperparameters"][key] = match.group(2)
        
        # Identify missing reproducibility items
        if not result["seeds"]:
            result["missing_items"].append("Random seed not found")
        
        if not result["hardware_refs"]:
            result["missing_items"].append("Hardware specification not found")
        
        # Check for common ML libraries without version pinning
        ml_libs = {'torch', 'tensorflow', 'keras', 'sklearn', 'transformers', 'numpy', 'pandas'}
        used_ml_libs = ml_libs.intersection(set(result["imports"]))
        if used_ml_libs:
            result["missing_items"].append(f"Version not pinned for: {', '.join(used_ml_libs)}")
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to analyze script: {str(e)}"
        }


def extract_seeds_from_text(content: str) -> List[str]:
    """Extract random seed information from text content."""
    seeds = []
    
    seed_patterns = [
        r'(?i)(?:random\.)?seed\s*[:=(\s]+(\d+)',
        r'(?i)np\.random\.seed\s*\((\d+)\)',
        r'(?i)torch\.manual_seed\s*\((\d+)\)',
        r'(?i)tf\.random\.set_seed\s*\((\d+)\)',
        r'(?i)SEED\s*=\s*(\d+)',
    ]
    
    for pattern in seed_patterns:
        matches = re.findall(pattern, content)
        seeds.extend(matches)
    
    return list(set(seeds))


def calculate_variance(values: List[float]) -> float:
    """Calculate variance of a list of values."""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance


def check_result_consistency(
    reported_results: Dict[str, float],
    log_results: Dict[str, float],
    tolerance: float = 0.01
) -> Dict:
    """
    Check if reported results are consistent with log results.
    
    Args:
        reported_results: Results claimed in the paper
        log_results: Results extracted from logs
        tolerance: Acceptable difference ratio
        
    Returns:
        Dictionary with consistency analysis
    """
    inconsistencies = []
    matched = []
    unverified = []
    
    for metric, reported_value in reported_results.items():
        # Try to find matching metric in logs (case-insensitive)
        log_value = None
        matched_key = None
        
        for log_key, log_val in log_results.items():
            if metric.lower() in log_key.lower() or log_key.lower() in metric.lower():
                log_value = log_val
                matched_key = log_key
                break
        
        if log_value is not None:
            # Check consistency
            if reported_value != 0:
                diff_ratio = abs(reported_value - log_value) / abs(reported_value)
            else:
                diff_ratio = abs(reported_value - log_value)
            
            if diff_ratio > tolerance:
                inconsistencies.append({
                    "metric": metric,
                    "reported": reported_value,
                    "logged": log_value,
                    "difference": diff_ratio
                })
            else:
                matched.append({
                    "metric": metric,
                    "reported": reported_value,
                    "logged": log_value,
                    "matched_log_key": matched_key
                })
        else:
            unverified.append(metric)
    
    return {
        "inconsistencies": inconsistencies,
        "matched": matched,
        "unverified": unverified,
        "consistency_score": len(matched) / len(reported_results) if reported_results else 1.0
    }
