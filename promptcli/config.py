from pathlib import Path

# Resolve the root directory of the PromptCLI project
BASE_DIR = Path(__file__).resolve().parent.parent

# Path to the API key file
API_KEY_PATH = BASE_DIR / ".gemini-api-key"

# Version of PromptCLI
VERSION = "1.0.0"
