from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from promptcli.cli import app

runner = CliRunner()

def test_cli_version() -> None:
    """Tests the version option on the CLI."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "PromptCLI version" in result.stdout

def test_cli_create_new_project() -> None:
    """Tests project creation command."""
    with patch("promptcli.core.create_project", return_value=True) as mock_create:
        result = runner.invoke(app, ["create", "my-new-project"])
        assert result.exit_code == 0
        assert "created successfully" in result.stdout
        mock_create.assert_called_once_with("my-new-project")

def test_cli_create_existing_project() -> None:
    """Tests project creation command when the project already exists."""
    with patch("promptcli.core.create_project", return_value=False) as mock_create:
        result = runner.invoke(app, ["create", "existing-project"])
        assert result.exit_code == 0
        assert "already exists" in result.stdout
        mock_create.assert_called_once_with("existing-project")

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

def test_cli_list_prompts() -> None:
    """Tests listing prompts of a project."""
    mock_prompts = [
        {"name": "hello", "filename": "hello.txt", "extension": ".txt", "size_str": "12 B", "last_modified": "2026-06-30 12:00:00"}
    ]
    with patch("promptcli.core.list_prompts", return_value=mock_prompts) as mock_list:
        # Note: the cli.py pre-parser inserts "run" for project commands,
        # but in CliRunner we invoke the app directly. We should pass the exact args we want.
        # Since the pre-parser is in main(), running runner.invoke(app, ["myproj", "--list"]) won't trigger main().
        # So we invoke the "run" subcommand directly:
        result = runner.invoke(app, ["run", "myproj", "--list"])
        assert result.exit_code == 0
        assert "Available Prompts in myproj" in result.stdout
        assert "hello" in result.stdout
        mock_list.assert_called_once_with("myproj")
