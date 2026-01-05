"""Helper utilities for the research verifier system."""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv


def load_env(env_path: Optional[str] = None) -> None:
    """Load environment variables from .env file."""
    if env_path:
        load_dotenv(env_path)
    else:
        # Try common locations
        for path in ['.env', '../.env', '~/.env']:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                load_dotenv(expanded)
                break


def read_file_safe(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Safely read a file, returning None on error."""
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except Exception:
        return None


def get_file_paths(directory: str, extensions: List[str]) -> List[str]:
    """
    Get all file paths in a directory matching given extensions.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions (with dot, e.g., ['.py', '.txt'])
        
    Returns:
        List of absolute file paths
    """
    if not os.path.isdir(directory):
        return []
    
    files = []
    for ext in extensions:
        files.extend(Path(directory).rglob(f'*{ext}'))
    
    return [str(f.absolute()) for f in files]


def format_json_output(data: Any, indent: int = 2) -> str:
    """Format data as pretty JSON string."""
    return json.dumps(data, indent=indent, default=str)


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_metric_name(name: str) -> str:
    """Normalize a metric name for comparison."""
    # Remove common prefixes/suffixes and normalize
    name = name.lower().strip()
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Common aliases
    aliases = {
        'acc': 'accuracy',
        'prec': 'precision',
        'rec': 'recall',
        'lr': 'learning rate',
    }
    
    for short, full in aliases.items():
        if name == short:
            return full
    
    return name


def extract_numbers_from_text(text: str) -> List[float]:
    """Extract all numbers from a text string."""
    import re
    pattern = r'-?\d+\.?\d*(?:[eE][+-]?\d+)?'
    matches = re.findall(pattern, text)
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    
    return numbers


def create_summary_table(data: Dict[str, Any], headers: List[str] = None) -> str:
    """Create a simple text table from dictionary data."""
    if not data:
        return "No data available"
    
    if headers is None:
        headers = ["Key", "Value"]
    
    rows = []
    max_key_len = max(len(str(k)) for k in data.keys())
    max_val_len = max(len(str(v)[:50]) for v in data.values())
    
    # Header
    rows.append(f"{headers[0]:<{max_key_len}} | {headers[1]}")
    rows.append("-" * (max_key_len + max_val_len + 3))
    
    # Data rows
    for key, value in data.items():
        val_str = str(value)[:50]
        rows.append(f"{str(key):<{max_key_len}} | {val_str}")
    
    return "\n".join(rows)


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def safe_get_nested(data: Dict, *keys, default=None) -> Any:
    """Safely get a nested value from a dictionary."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current
