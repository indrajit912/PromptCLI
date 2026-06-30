import datetime
from pathlib import Path
from typing import List, Dict, Any
from google import genai

class ProjectNotFoundError(Exception):
    """Raised when a prompt project directory does not exist."""
    pass

class PromptNotFoundError(Exception):
    """Raised when a specific prompt file is not found."""
    pass

class GenerationError(Exception):
    """Raised when Gemini content generation fails."""
    pass

def create_project(project_path_str: str) -> bool:
    """Creates a new prompt project structure at the specified directory path.
    
    Args:
        project_path_str: The path to the project directory (absolute or relative).
        
    Returns:
        True if the project was created, False if it already existed.
    """
    project_dir = Path(project_path_str).resolve()
    if project_dir.exists():
        return False
        
    (project_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (project_dir / "outputs").mkdir(parents=True, exist_ok=True)
    return True

def list_prompts(project_path_str: str) -> List[Dict[str, Any]]:
    """Lists all prompts in a project directory.
    
    Args:
        project_path_str: The path to the project directory.
        
    Returns:
        A list of metadata dictionaries.
        
    Raises:
        ProjectNotFoundError: If the project or prompts directory does not exist.
    """
    project_dir = Path(project_path_str).resolve()
    prompts_dir = project_dir / "prompts"
    
    if not project_dir.exists() or not prompts_dir.exists():
        raise ProjectNotFoundError(f"Project directory '{project_path_str}' does not exist or is not a valid PromptCLI project.")
        
    results = []
    for file in prompts_dir.iterdir():
        if file.is_file():
            stat = file.stat()
            results.append({
                "name": file.stem,
                "filename": file.name,
                "extension": file.suffix,
                "size_str": format_size(stat.st_size),
                "size_bytes": stat.st_size,
                "last_modified": format_timestamp(stat.st_mtime),
            })
            
    # Sort prompts alphabetically by name
    results.sort(key=lambda x: x["name"].lower())
    return results

def find_prompt_file(project_path_str: str, prompt_name: str) -> Path:
    """Finds a prompt file by name in the project directory, checking extensions.
    
    Args:
        project_path_str: The path to the project directory.
        prompt_name: The prompt filename or stem.
        
    Returns:
        The Path to the prompt file.
        
    Raises:
        ProjectNotFoundError: If the project directory does not exist.
        PromptNotFoundError: If the prompt file is not found.
    """
    project_dir = Path(project_path_str).resolve()
    prompts_dir = project_dir / "prompts"
    
    if not project_dir.exists() or not prompts_dir.exists():
        raise ProjectNotFoundError(f"Project directory '{project_path_str}' does not exist or is not a valid PromptCLI project.")
        
    # 1. Check exact match (if extension was provided)
    exact_path = prompts_dir / prompt_name
    if exact_path.is_file():
        return exact_path
        
    # 2. Check match by stem (case-insensitive)
    for file in prompts_dir.iterdir():
        if file.is_file() and file.stem.lower() == prompt_name.lower():
            return file
            
    # 3. Check match by name including extension if omitted
    # Check if they specified without extension, look for standard extensions
    for ext in [".txt", ".md", ".json"]:
        path = prompts_dir / f"{prompt_name}{ext}"
        if path.is_file():
            return path
            
    raise PromptNotFoundError(f"Prompt '{prompt_name}' not found in project directory '{project_path_str}'.")

def generate_output(
    project_path_str: str,
    prompt_path: Path,
    api_key: str,
    model_name: str = "gemini-2.5-flash",
) -> Path:
    """Generates Gemini response for a prompt and saves it to the outputs directory in the project path.
    
    Args:
        project_path_str: The path to the project directory.
        prompt_path: The Path to the prompt file.
        api_key: The Gemini API key.
        model_name: The model to use.
        
    Returns:
        The Path to the saved output file.
        
    Raises:
        GenerationError: If the Gemini API call or file writing fails.
    """
    project_dir = Path(project_path_str).resolve()
    outputs_dir = project_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output file path (always markdown)
    output_path = outputs_dir / f"{prompt_path.stem}.md"
    
    try:
        # Load prompt text
        prompt_text = prompt_path.read_text(encoding="utf-8")
        
        # Initialize Gemini Client
        client = genai.Client(api_key=api_key)
        
        # Generate Content
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text,
        )
        
        if not response.text:
            raise GenerationError("Gemini response was empty or blocked.")
            
        # Write output file
        output_path.write_text(response.text, encoding="utf-8")
        return output_path
        
    except Exception as e:
        if isinstance(e, GenerationError):
            raise
        raise GenerationError(f"Failed to generate output for prompt '{prompt_path.name}': {str(e)}") from e

def format_size(size_in_bytes: int) -> str:
    """Formats file size into human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}" if unit != 'B' else f"{size_in_bytes} B"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"

def format_timestamp(timestamp: float) -> str:
    """Formats epoch timestamp into YYYY-MM-DD HH:MM:SS."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
