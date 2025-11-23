import json, pathlib
from typing import Union, Dict, Any

def load_input(path: Union[str, Dict[str, Any]]):
    """
    Load input data from file path or dict.
    
    Args:
        path: File path (str) or dict with input data
        
    Returns:
        dict: Parsed input data
    """
    # If already a dict, return it
    if isinstance(path, dict):
        return path
    
    # Otherwise, load from file path
    p = pathlib.Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    # TODO: validate against schemas/input.schema.json
    return data
