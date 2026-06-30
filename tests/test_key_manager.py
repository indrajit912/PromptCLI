import os
from unittest.mock import patch
from pathlib import Path
import pytest
from promptcli.key_manager import load_key, save_key, check_key_status

def test_key_lifecycle(tmp_path: Path) -> None:
    """Tests saving, loading, and status checking of the Gemini API key."""
    temp_key_file = tmp_path / ".gemini-api-key"
    
    with patch("promptcli.key_manager.API_KEY_PATH", temp_key_file):
        # 1. Initially it should be missing
        assert check_key_status() == "missing"
        
        # 2. Save a valid key
        save_key("my-secret-key-123")
        assert check_key_status() == "exists"
        assert load_key() == "my-secret-key-123"
        
        # 3. Save an empty key
        save_key("  ")
        assert check_key_status() == "empty"
        assert load_key() is None

def test_load_key_env_fallback(tmp_path: Path) -> None:
    """Tests that load_key falls back to the GEMINI_API_KEY environment variable when no file is present."""
    temp_key_file = tmp_path / ".gemini-api-key"
    
    with patch("promptcli.key_manager.API_KEY_PATH", temp_key_file):
        # File is missing
        assert check_key_status() == "missing"
        
        # Set environment variable
        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-secret-999"}):
            assert load_key() == "env-secret-999"
            
        # Env var missing too
        with patch.dict(os.environ, {}, clear=True):
            assert load_key() is None
