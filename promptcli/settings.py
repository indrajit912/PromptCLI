import json
import os
import sys
from pathlib import Path
from typing import Optional, Any, Dict

class SettingsManager:
    """Manages PromptCLI persistent user configurations across platforms."""
    
    def __init__(self) -> None:
        self.config_dir = self._get_config_dir()
        self.config_path = self.config_dir / "settings.json"
        self._settings = self._load()
        # Set default values if not present
        if "editor" not in self._settings:
            self.set("editor", "vim")

    def _get_config_dir(self) -> Path:
        """Resolves user's configuration directory following platform conventions."""
        if sys.platform.startswith("win"):
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / "PromptCLI"
            return Path.home() / "AppData" / "Roaming" / "PromptCLI"
        else:
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                return Path(xdg_config) / "promptcli"
            return Path.home() / ".config" / "promptcli"

    def _load(self) -> Dict[str, Any]:
        """Loads configuration from settings file."""
        if not self.config_path.is_file():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self) -> None:
        """Saves current configuration to settings file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path.write_text(json.dumps(self._settings, indent=4), encoding="utf-8")
        except Exception:
            pass

    @property
    def workspace_dir(self) -> Optional[str]:
        """Gets the configured workspace directory path."""
        return self._settings.get("workspace_dir")

    @workspace_dir.setter
    def workspace_dir(self, value: Optional[str]) -> None:
        """Sets or clears the workspace directory path."""
        if value is None:
            self._settings.pop("workspace_dir", None)
        else:
            self._settings["workspace_dir"] = str(Path(value).resolve())
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Extensible method to retrieve setting by key."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Extensible method to save setting by key."""
        self._settings[key] = value
        self._save()


def get_or_create_default_workspace() -> Optional[Path]:
    """Retrieves or configures the default workspace (~/Documents/ai-prompts).
    
    If the user has not configured a workspace yet, PromptCLI should automatically
    use ~/Documents/ai-prompts. If it doesn't exist, it asks the user to create it.
    """
    settings = SettingsManager()
    workspace_str = settings.workspace_dir
    if workspace_str:
        return Path(workspace_str)
        
    default_path = Path.home() / "Documents" / "ai-prompts"
    if not default_path.exists():
        import typer
        try:
            typer.echo("No default workspace root is currently configured.")
            confirm = typer.confirm(
                f"Would you like to configure the default workspace at '{default_path}'?",
                default=True,
            )
            if confirm:
                default_path.mkdir(parents=True, exist_ok=True)
                settings.workspace_dir = str(default_path)
                typer.echo(f"Created default workspace directory at {default_path}")
                return default_path
        except Exception:
            pass
        return None
    else:
        # If it exists, configure it automatically
        settings.workspace_dir = str(default_path)
        return default_path


def resolve_project_path(project_arg: str) -> Path:
    """Resolves a project directory argument to an absolute Path, taking workspace into account.
    
    If the argument is an absolute path, exists as a directory/file, starts with '.',
    or contains path separators, it is resolved directly.
    Otherwise, if a workspace is configured, it is resolved inside the workspace.
    """
    settings = SettingsManager()
    workspace_str = settings.workspace_dir
    
    if not workspace_str:
        workspace_path = get_or_create_default_workspace()
    else:
        workspace_path = Path(workspace_str)
        
    arg_path = Path(project_arg)
    
    if (arg_path.is_absolute() or 
        arg_path.exists() or 
        "/" in project_arg or 
        "\\" in project_arg or 
        project_arg.startswith(".")):
        return arg_path.resolve()
        
    if workspace_path:
        return (workspace_path / project_arg).resolve()
        
    return arg_path.resolve()
