import os
from pathlib import Path
from typing import Optional
from promptcli.config import API_KEY_PATH

def load_key() -> Optional[str]:
    """Loads the Gemini API key from the local key file, falling back to the environment variable.
    
    Returns:
        The API key string if found, otherwise None.
    """
    if API_KEY_PATH.is_file():
        try:
            key = API_KEY_PATH.read_text(encoding="utf-8").strip()
            if key:
                return key
        except Exception:
            pass
            
    # Fallback to the environment variable
    return os.environ.get("GEMINI_API_KEY")

def save_key(key: str) -> None:
    """Saves the Gemini API key to the local key file in the project root.
    
    Args:
        key: The API key to save.
    """
    # Write key with restricted permissions if possible, though Windows handles this differently
    API_KEY_PATH.write_text(key.strip(), encoding="utf-8")

def check_key_status() -> str:
    """Checks the status of the local API key file.
    
    Returns:
        "exists" if the file exists and has a non-empty key,
        "empty" if the file exists but is empty,
        "missing" if the file does not exist.
    """
    if not API_KEY_PATH.is_file():
        return "missing"
    try:
        content = API_KEY_PATH.read_text(encoding="utf-8").strip()
        return "exists" if content else "empty"
    except Exception:
        return "missing"
