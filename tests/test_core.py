from unittest.mock import MagicMock, patch
from pathlib import Path
import pytest
from promptcli.core import (
    create_project,
    list_prompts,
    find_prompt_file,
    generate_output,
    ProjectNotFoundError,
    PromptNotFoundError,
)

def test_project_creation_and_listing(tmp_path: Path) -> None:
    """Tests creating projects and listing prompt files inside them."""
    proj_path = str(tmp_path / "testproj")
    
    # Create a new project
    assert create_project(proj_path) is True
    assert (tmp_path / "testproj" / "prompts").is_dir()
    assert (tmp_path / "testproj" / "outputs").is_dir()
    
    # Creating a duplicate should return False (already exists)
    assert create_project(proj_path) is False
    
    # Listing prompts of a newly created project should be empty
    prompts = list_prompts(proj_path)
    assert len(prompts) == 0
    
    # Add a prompt file manually
    prompt_file = tmp_path / "testproj" / "prompts" / "hello.txt"
    prompt_file.write_text("Hello Gemini", encoding="utf-8")
    
    # List prompts again
    prompts = list_prompts(proj_path)
    assert len(prompts) == 1
    assert prompts[0]["name"] == "hello"
    assert prompts[0]["filename"] == "hello.txt"
    assert prompts[0]["extension"] == ".txt"
    assert prompts[0]["size_bytes"] == 12

def test_find_prompt_file(tmp_path: Path) -> None:
    """Tests finding prompt files by exact name, case-insensitive stem, and default extensions."""
    proj_path = str(tmp_path / "myproj")
    
    create_project(proj_path)
    prompts_dir = tmp_path / "myproj" / "prompts"
    
    file_md = prompts_dir / "summary.md"
    file_md.write_text("summary markdown", encoding="utf-8")
    
    file_txt = prompts_dir / "notes.txt"
    file_txt.write_text("notes txt", encoding="utf-8")
    
    # 1. Exact match
    assert find_prompt_file(proj_path, "summary.md") == file_md
    
    # 2. Case-insensitive stem match
    assert find_prompt_file(proj_path, "notes") == file_txt
    assert find_prompt_file(proj_path, "NOTES") == file_txt
    
    # 3. Match without extension (defaults to .md or .txt lookup)
    assert find_prompt_file(proj_path, "summary") == file_md
    
    # 4. Error if missing prompt
    with pytest.raises(PromptNotFoundError):
        find_prompt_file(proj_path, "nonexistent")
        
    # 5. Error if missing project
    with pytest.raises(ProjectNotFoundError):
        find_prompt_file(str(tmp_path / "missing_project"), "notes")

def test_generate_output(tmp_path: Path) -> None:
    """Tests invoking generate_output with a mocked Gemini client and content generation."""
    proj_path = str(tmp_path / "myproj")
    
    create_project(proj_path)
    prompt_path = tmp_path / "myproj" / "prompts" / "joke.txt"
    prompt_path.write_text("Tell a joke", encoding="utf-8")
    
    # Mock the Google GenAI SDK Client
    mock_client_class = MagicMock()
    mock_client_instance = MagicMock()
    mock_client_class.return_value = mock_client_instance
    
    mock_response = MagicMock()
    mock_response.text = "This is a joke response."
    mock_client_instance.models.generate_content.return_value = mock_response
    
    with patch("promptcli.core.genai.Client", mock_client_class):
        output_file = generate_output(proj_path, prompt_path, api_key="mock-key-456")
        
        # Check response saved to markdown output file
        expected_output_file = tmp_path / "myproj" / "outputs" / "joke.md"
        assert output_file == expected_output_file
        assert expected_output_file.is_file()
        assert expected_output_file.read_text(encoding="utf-8") == "This is a joke response."
        
        # Assert client was initialized and generated content with correct params
        mock_client_class.assert_called_once_with(api_key="mock-key-456")
        mock_client_instance.models.generate_content.assert_called_once_with(
            model="gemini-2.5-flash",
            contents="Tell a joke",
        )
