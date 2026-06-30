from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
import json
import pytest
from typer.testing import CliRunner
from promptcli.cli import app
from promptcli.settings import SettingsManager

runner = CliRunner()

@pytest.fixture(autouse=True)
def isolate_settings(tmp_path: Path):
    """Autouse fixture to isolate settings for every test to a temporary config folder."""
    temp_config_dir = tmp_path / "config"
    with patch("promptcli.settings.SettingsManager._get_config_dir", return_value=temp_config_dir):
        yield

def test_cli_version() -> None:
    """Tests the version option on the CLI."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "PromptCLI version" in result.stdout

@patch("promptcli.settings.get_or_create_default_workspace", return_value=None)
def test_cli_create_new_project(mock_workspace: MagicMock) -> None:
    """Tests project creation command."""
    with patch("promptcli.core.create_project", return_value=True) as mock_create:
        result = runner.invoke(app, ["create", "my-new-project"])
        assert result.exit_code == 0
        assert "created successfully" in result.stdout
        expected_path = str(Path("my-new-project").resolve())
        mock_create.assert_called_once_with(expected_path)

@patch("promptcli.settings.get_or_create_default_workspace", return_value=None)
def test_cli_create_existing_project(mock_workspace: MagicMock) -> None:
    """Tests project creation command when the project already exists."""
    with patch("promptcli.core.create_project", return_value=False) as mock_create:
        result = runner.invoke(app, ["create", "existing-project"])
        assert result.exit_code == 0
        assert "already" in result.stdout
        assert "exists" in result.stdout
        expected_path = str(Path("existing-project").resolve())
        mock_create.assert_called_once_with(expected_path)

def test_cli_gemini_key_status_missing() -> None:
    """Tests gemini-key status when missing."""
    with patch("promptcli.key_manager.check_key_status", return_value="missing"):
        result = runner.invoke(app, ["gemini-key", "status"])
        assert result.exit_code == 0
        assert "Gemini API key is missing" in result.stdout

def test_cli_gemini_key_status_exists() -> None:
    """Tests gemini-key status when it exists."""
    with patch("promptcli.key_manager.check_key_status", return_value="exists"):
        result = runner.invoke(app, ["gemini-key", "status"])
        assert result.exit_code == 0
        assert "Gemini API key is configured" in result.stdout

def test_cli_gemini_key_save() -> None:
    """Tests saving the API key via CLI."""
    with patch("promptcli.key_manager.check_key_status", return_value="missing"), \
         patch("promptcli.key_manager.save_key") as mock_save:
        result = runner.invoke(app, ["gemini-key", "--save"], input="my-super-secret-key-999\n")
        assert result.exit_code == 0
        assert "saved successfully" in result.stdout
        mock_save.assert_called_once_with("my-super-secret-key-999")

@patch("promptcli.settings.get_or_create_default_workspace", return_value=None)
def test_cli_list_prompts(mock_workspace: MagicMock) -> None:
    """Tests listing prompts of a project."""
    mock_prompts = [
        {"name": "hello", "filename": "hello.txt", "extension": ".txt", "size_str": "12 B", "last_modified": "2026-06-30 12:00:00"}
    ]
    with patch("promptcli.core.list_prompts", return_value=mock_prompts) as mock_list:
        result = runner.invoke(app, ["run", "myproj", "--list"])
        assert result.exit_code == 0
        assert "Available Prompts in" in result.stdout
        assert "myproj" in result.stdout
        expected_path = str(Path("myproj").resolve())
        mock_list.assert_called_once_with(expected_path)


# --- Workspace Subcommands Tests ---

def test_workspace_commands_lifecycle(tmp_path: Path) -> None:
    """Tests the workspace subcommands (status, set, show, clear) in a temporary config file context."""
    # 1. Initially it should not be configured
    result = runner.invoke(app, ["workspace", "status"])
    assert result.exit_code == 0
    assert "Not Configured" in result.stdout
    
    # 2. Show should say no workspace configured
    result = runner.invoke(app, ["workspace", "show"])
    assert result.exit_code == 0
    assert "No default workspace is currently configured" in result.stdout
    
    # 3. Set the workspace to a temporary path
    test_workspace_dir = tmp_path / "my-workspace"
    # Since it doesn't exist, we confirm creation
    result = runner.invoke(app, ["workspace", "set", str(test_workspace_dir)], input="y\n")
    assert result.exit_code == 0
    assert "Created directory" in result.stdout
    assert "Default workspace successfully set" in result.stdout
    assert test_workspace_dir.is_dir()
    
    # 4. Show should now print the path
    result = runner.invoke(app, ["workspace", "show"])
    assert result.exit_code == 0
    assert "my-workspace" in result.stdout
    
    # 5. Status should say Exists and count active projects
    # Let's create a mock project inside it
    project_dir = test_workspace_dir / "blog"
    (project_dir / "prompts").mkdir(parents=True)
    (project_dir / "outputs").mkdir(parents=True)
    
    result = runner.invoke(app, ["workspace", "status"])
    assert result.exit_code == 0
    assert "Exists" in result.stdout
    assert "Active Projects: 1" in result.stdout
    assert "blog" in result.stdout
    
    # 6. Clear workspace with confirmation
    result = runner.invoke(app, ["workspace", "clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared successfully" in result.stdout
    
    # Ensure status is now unconfigured
    result = runner.invoke(app, ["workspace", "status"])
    assert "Not Configured" in result.stdout


# --- Prompt and Output Subcommand Tests ---

def test_prompt_create(tmp_path: Path) -> None:
    """Tests the prompt create subcommand."""
    proj_path = tmp_path / "proj"
    (proj_path / "prompts").mkdir(parents=True)
    (proj_path / "outputs").mkdir(parents=True)
    
    with patch("promptcli.cli.resolve_project_path", return_value=proj_path), \
         patch("promptcli.cli.open_in_editor") as mock_editor:
         
        result = runner.invoke(app, ["prompt", "create", "proj", "my-prompt"])
        assert result.exit_code == 0
        assert "Created new prompt file" in result.stdout
        assert (proj_path / "prompts" / "my-prompt.txt").is_file()
        mock_editor.assert_called_once_with(proj_path / "prompts" / "my-prompt.txt")

def test_prompt_edit(tmp_path: Path) -> None:
    """Tests the prompt edit subcommand."""
    proj_path = tmp_path / "proj"
    (proj_path / "prompts").mkdir(parents=True)
    prompt_file = proj_path / "prompts" / "notes.txt"
    prompt_file.touch()
    
    with patch("promptcli.cli.resolve_project_path", return_value=proj_path), \
         patch("promptcli.cli.open_in_editor") as mock_editor:
         
        result = runner.invoke(app, ["prompt", "edit", "proj", "notes"])
        assert result.exit_code == 0
        mock_editor.assert_called_once_with(prompt_file)

def test_prompt_delete(tmp_path: Path) -> None:
    """Tests the prompt delete subcommand and output cleanup."""
    proj_path = tmp_path / "proj"
    (proj_path / "prompts").mkdir(parents=True)
    (proj_path / "outputs").mkdir(parents=True)
    
    prompt_file = proj_path / "prompts" / "notes.txt"
    prompt_file.touch()
    output_file = proj_path / "outputs" / "notes.md"
    output_file.touch()
    
    with patch("promptcli.cli.resolve_project_path", return_value=proj_path):
        # Confirm prompt delete, but decline output delete
        result = runner.invoke(app, ["prompt", "delete", "proj", "notes"], input="y\nn\n")
        assert result.exit_code == 0
        assert not prompt_file.exists()
        assert output_file.exists()

def test_output_commands(tmp_path: Path) -> None:
    """Tests opening, listing, and deleting outputs."""
    proj_path = tmp_path / "proj"
    (proj_path / "outputs").mkdir(parents=True)
    output_file = proj_path / "outputs" / "joke.md"
    output_file.touch()
    
    with patch("promptcli.cli.resolve_project_path", return_value=proj_path), \
         patch("promptcli.cli.open_in_editor") as mock_editor:
         
        # Test Open Output
        result = runner.invoke(app, ["output", "open", "proj", "joke"])
        assert result.exit_code == 0
        mock_editor.assert_called_once_with(output_file)
        
        # Test List Outputs
        result = runner.invoke(app, ["output", "list", "proj"])
        assert result.exit_code == 0
        assert "joke" in result.stdout
        
        # Test Delete Output
        result = runner.invoke(app, ["output", "delete", "proj", "joke"], input="y\n")
        assert result.exit_code == 0
        assert not output_file.exists()

def test_project_list_and_delete(tmp_path: Path) -> None:
    """Tests listing projects in workspace and project deletion."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    proj_dir = workspace_dir / "my-project"
    (proj_dir / "prompts").mkdir(parents=True)
    (proj_dir / "outputs").mkdir(parents=True)
    
    with patch("promptcli.settings.SettingsManager.workspace_dir", new_callable=PropertyMock) as mock_workspace:
        mock_workspace.return_value = str(workspace_dir)
        
        # List projects in workspace
        result = runner.invoke(app, ["project", "list"])
        assert result.exit_code == 0
        assert "my-project" in result.stdout
        
        # Delete project with confirmation
        with patch("promptcli.cli.resolve_project_path", return_value=proj_dir):
            result = runner.invoke(app, ["project", "delete", "my-project"], input="y\n")
            assert result.exit_code == 0
            assert not proj_dir.exists()
