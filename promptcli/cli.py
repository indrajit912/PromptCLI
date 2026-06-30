import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from promptcli.config import VERSION
from promptcli.settings import SettingsManager, resolve_project_path

from promptcli.ui import (
    show_banner,
    print_success,
    print_warning,
    print_error,
    print_info,
    display_prompts_table,
)

console = Console()

# Create main Typer app
app = typer.Typer(
    name="promptcli",
    rich_markup_mode="rich",
)

# Create Gemini-key subcommand Typer app
gemini_key_app = typer.Typer(
    name="gemini-key",
    rich_markup_mode="rich",
    help="Manage Gemini API key stored in the .gemini-api-key file.",
)

app.add_typer(gemini_key_app, name="gemini-key")

# Create Workspace subcommand Typer app
workspace_app = typer.Typer(
    name="workspace",
    rich_markup_mode="rich",
    help="Manage PromptCLI default workspace settings.",
)

app.add_typer(workspace_app, name="workspace")

# Create Project subcommand Typer app
project_app = typer.Typer(
    name="project",
    rich_markup_mode="rich",
    help="Manage PromptCLI prompt projects.",
)

# Create Prompt subcommand Typer app
prompt_app = typer.Typer(
    name="prompt",
    rich_markup_mode="rich",
    help="Manage prompts inside projects.",
)

# Create Output subcommand Typer app
output_app = typer.Typer(
    name="output",
    rich_markup_mode="rich",
    help="Manage generated prompt outputs.",
)

app.add_typer(project_app, name="project")
app.add_typer(prompt_app, name="prompt")
app.add_typer(output_app, name="output")




@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show PromptCLI application version and exit.",
    ),
) -> None:
    """
    [bold cyan]PromptCLI[/bold cyan] - A Python CLI for Managing AI Prompts (Google GenAI).

    This toolkit helps manage prompt projects, send prompts to Gemini,
    and save outputs in a structured folder hierarchy.

    [bold underline]Usage Patterns:[/bold underline]
      [green]promptcli <project-dir> <prompt>[/green]        Generate output for a single prompt
      [green]promptcli <project-dir> --list[/green]          List all available prompts in a project directory
      [green]promptcli <project-dir> --feed-all[/green]      Generate outputs for all prompts in a project directory
      [green]promptcli create <project-dir>[/green]          Create a new project structure at the specified directory path
      [green]promptcli gemini-key status[/green]            Check Gemini API key status
      [green]promptcli gemini-key --save[/green]            Save Gemini API key securely

    [bold underline]Exit Codes:[/bold underline]
      [white]0[/white] - Success
      [white]1[/white] - Error (e.g. project/prompt not found, Gemini API failure)
      [white]2[/white] - CLI usage/parsing error
    """
    if version:
        typer.echo(f"PromptCLI version {VERSION}")
        raise typer.Exit()

    # Show banner on startup for normal commands
    show_banner()

    if ctx.invoked_subcommand is None:
        # If no subcommand was provided, display the default click help output
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("create", help="Create a new project structure at the specified directory path.")
def create_project_cmd(
    project_path: str = typer.Argument(
        ...,
        help="The directory path (relative or absolute) where the project structure should be created.",
    )
) -> None:
    """Creates prompts/ and outputs/ directories at the specified location."""
    from promptcli.core import create_project

    resolved_path = resolve_project_path(project_path)
    success = create_project(str(resolved_path))
    if success:
        try:
            display_path = resolved_path.relative_to(Path.cwd())
        except ValueError:
            display_path = resolved_path
        print_success(f"Project directory created successfully at [cyan]{display_path}[/cyan].")
    else:
        print_warning(f"Project directory '{resolved_path}' already exists.")


@gemini_key_app.callback(invoke_without_command=True)
def gemini_key_main(
    ctx: typer.Context,
    save: bool = typer.Option(
        False,
        "--save",
        help="Securely prompt for the Gemini API key and save it to the local .gemini-api-key file.",
    ),
) -> None:
    """
    Manage the Gemini API key.
    
    If neither --save nor status subcommand is specified, defaults to status.
    """
    from promptcli.key_manager import check_key_status, save_key

    if save:
        status = check_key_status()
        if status == "exists":
            confirm = typer.confirm(
                "An API key is already saved. Do you want to overwrite it?",
                default=True,
            )
            if not confirm:
                print_info("API key was not modified.")
                raise typer.Exit(0)

        # Securely prompt for the key (hidden input)
        api_key = typer.prompt("Enter your Gemini API key", hide_input=True)
        if not api_key.strip():
            print_error("API key cannot be empty.")
            raise typer.Exit(1)

        save_key(api_key)
        print_success("Gemini API key saved successfully to .gemini-api-key.")
        raise typer.Exit(0)

    elif ctx.invoked_subcommand is None:
        # Default behavior: run status
        show_gemini_key_status()


@gemini_key_app.command("status", help="Check the configuration status of the Gemini API key.")
def gemini_key_status_cmd() -> None:
    """Checks if the .gemini-api-key file exists and is populated."""
    show_gemini_key_status()


def show_gemini_key_status() -> None:
    """Helper to check and output the API key status."""
    from promptcli.key_manager import check_key_status

    status = check_key_status()
    if status == "exists":
        print_success("Gemini API key is configured and present in .gemini-api-key.")
    elif status == "empty":
        print_warning("The .gemini-api-key file exists but is empty.")
    else:
        print_error("Gemini API key is missing (no .gemini-api-key file found).")


@workspace_app.command("set", help="Set the default workspace root directory.")
def workspace_set(
    directory: str = typer.Argument(..., help="Path to the workspace directory.")
) -> None:
    """Verifies, optionally creates, and configures the default workspace directory."""
    resolved_path = Path(directory).resolve()
    if not resolved_path.exists():
        confirm = typer.confirm(
            f"Directory '{resolved_path}' does not exist. Do you want to create it?",
            default=True,
        )
        if confirm:
            try:
                resolved_path.mkdir(parents=True, exist_ok=True)
                print_success(f"Created directory [cyan]{resolved_path}[/cyan].")
            except Exception as e:
                print_error(f"Failed to create directory '{resolved_path}': {str(e)}")
                raise typer.Exit(1)
        else:
            print_info("Workspace path was not set.")
            raise typer.Exit(0)

    settings = SettingsManager()
    settings.workspace_dir = str(resolved_path)
    print_success(f"Default workspace successfully set to [cyan]{resolved_path}[/cyan].")


@workspace_app.command("show", help="Display the currently configured workspace directory.")
def workspace_show() -> None:
    """Prints the currently configured workspace path."""
    settings = SettingsManager()
    workspace = settings.workspace_dir
    if workspace:
        print_info(f"Current workspace directory: [cyan]{workspace}[/cyan]")
    else:
        print_warning("No default workspace is currently configured.")


@workspace_app.command("clear", help="Remove the configured default workspace.")
def workspace_clear() -> None:
    """Clears the workspace path setting after user confirmation."""
    settings = SettingsManager()
    workspace = settings.workspace_dir
    if not workspace:
        print_info("No workspace is configured to clear.")
        raise typer.Exit(0)

    confirm = typer.confirm(
        f"Are you sure you want to clear the workspace path '[cyan]{workspace}[/cyan]'?",
        default=True,
    )
    if confirm:
        settings.workspace_dir = None
        print_success("Default workspace configuration cleared successfully.")
    else:
        print_info("Clear operation cancelled.")


@workspace_app.command("status", help="Display status information about the workspace.")
def workspace_status() -> None:
    """Displays workspace path, existence, and any active projects found inside."""
    settings = SettingsManager()
    workspace = settings.workspace_dir

    if not workspace:
        print_warning("Workspace Status: [bold red]Not Configured[/bold red]")
        print_info("You can configure a default workspace using: [bold]promptcli workspace set <directory>[/bold]")
        return

    workspace_path = Path(workspace)
    exists = workspace_path.exists()

    print_info(f"Workspace Path:  [cyan]{workspace}[/cyan]")
    if exists:
        print_success("Workspace Dir:   [bold green]Exists[/bold green]")
        try:
            projects = []
            for sub in workspace_path.iterdir():
                if sub.is_dir() and (sub / "prompts").is_dir():
                    projects.append(sub.name)
            print_info(f"Active Projects: {len(projects)}")
            if projects:
                print_info(f"Projects list:   {', '.join(projects)}")
        except Exception:
            pass
    else:
        print_error("Workspace Dir:   [bold red]Does Not Exist[/bold red]")


def open_in_editor(file_path: Path) -> None:
    """Helper to open a file in the configured text editor or system default."""
    import shlex
    import subprocess
    import os
    settings = SettingsManager()
    editor = settings.get("editor") or os.environ.get("EDITOR", "vim")
    try:
        args = shlex.split(editor) + [str(file_path)]
        subprocess.run(args, check=True)
    except FileNotFoundError:
        print_error(f"Editor '{editor}' was not found on your system PATH.")
        print_info("You can configure your preferred editor by editing your settings at:")
        print_info(f"  [cyan]{settings.config_path}[/cyan]")
        print_info("For example, set \"editor\": \"notepad\" on Windows, or \"nano\" on Unix.")
    except Exception as e:
        print_error(f"Failed to open editor: {str(e)}")


# --- Project Management Subcommands ---

@project_app.command("create", help="Create a new project structure.")
def project_create(
    project_path: str = typer.Argument(
        ...,
        help="The directory path (relative, absolute, or workspace name) where the project should be created.",
    )
) -> None:
    """Shortcut command mapping to top-level create command."""
    create_project_cmd(project_path)


@project_app.command("delete", help="Delete a project directory and all its files recursively.")
def project_delete(
    project_path: str = typer.Argument(
        ...,
        help="The directory path or workspace name of the project to delete.",
    )
) -> None:
    """Deletes a project directory recursively after confirmation."""
    from promptcli.core import delete_project, ProjectNotFoundError
    
    resolved_path = resolve_project_path(project_path)
    if not resolved_path.exists():
        print_error(f"Project directory '{resolved_path}' does not exist.")
        raise typer.Exit(1)
        
    confirm = typer.confirm(
        f"Are you sure you want to permanently delete the project directory at '{resolved_path}' and all its files?",
        default=False,
    )
    if confirm:
        try:
            delete_project(str(resolved_path))
            print_success(f"Project directory '{resolved_path}' deleted successfully.")
        except Exception as e:
            print_error(f"Failed to delete project directory: {str(e)}")
            raise typer.Exit(1)
    else:
        print_info("Delete operation cancelled.")


@project_app.command("list", help="List all prompt projects inside your configured default workspace.")
def project_list() -> None:
    """Displays all prompt projects inside the workspace root in a table."""
    settings = SettingsManager()
    workspace = settings.workspace_dir
    if not workspace:
        print_warning("No default workspace is currently configured.")
        print_info("To list projects, configure a default workspace first using:")
        print_info("  [bold]promptcli workspace set <directory>[/bold]")
        raise typer.Exit(1)
        
    workspace_path = Path(workspace)
    if not workspace_path.exists():
        print_error(f"Configured workspace directory '{workspace}' does not exist.")
        raise typer.Exit(1)
        
    try:
        projects = []
        for sub in workspace_path.iterdir():
            if sub.is_dir() and (sub / "prompts").is_dir():
                projects.append(sub)
                
        if not projects:
            print_info(f"No prompt projects found in workspace '{workspace}'.")
            return
            
        from rich.table import Table
        table = Table(
            title=f"Available Projects in Workspace: [bold cyan]{workspace_path.name}[/bold cyan]",
            title_style="bold underline",
            border_style="blue",
            header_style="bold magenta",
            expand=True,
        )
        table.add_column("Project Name", style="bold cyan")
        table.add_column("Path", style="white")
        table.add_column("Prompts Count", style="green", justify="right")
        table.add_column("Outputs Count", style="yellow", justify="right")
        
        for p in sorted(projects, key=lambda x: x.name.lower()):
            prompts_count = sum(1 for f in (p / "prompts").iterdir() if f.is_file())
            outputs_dir = p / "outputs"
            outputs_count = sum(1 for f in outputs_dir.iterdir() if f.is_file()) if outputs_dir.is_dir() else 0
            table.add_row(p.name, str(p), str(prompts_count), str(outputs_count))
            
        console.print(table)
    except Exception as e:
        print_error(f"Failed to list projects: {str(e)}")
        raise typer.Exit(1)


# --- Prompt Management Subcommands ---

@prompt_app.command("create", help="Create a new prompt file inside a project.")
def prompt_create(
    project: str = typer.Argument(..., help="The project directory or workspace project name."),
    prompt_name: str = typer.Argument(..., help="The name of the prompt to create."),
    ext: str = typer.Option(".txt", "--extension", "-e", help="The file extension for the prompt file (e.g. .txt or .md)."),
) -> None:
    """Creates a new prompt file and opens it in the default text editor."""
    resolved_project_path = resolve_project_path(project)
    prompts_dir = resolved_project_path / "prompts"
    
    if not resolved_project_path.exists() or not prompts_dir.is_dir():
        print_error(f"Project directory '{resolved_project_path}' does not exist or is not initialized.")
        print_info("You can initialize it using: [bold]promptcli create <project>[/bold]")
        raise typer.Exit(1)
        
    if not ext.startswith("."):
        ext = f".{ext}"
        
    prompt_file = prompts_dir / f"{prompt_name}{ext}"
    if prompt_file.exists():
        print_warning(f"Prompt file '{prompt_file.name}' already exists.")
    else:
        try:
            prompt_file.touch()
            print_success(f"Created new prompt file: [cyan]{prompt_file.relative_to(resolved_project_path)}[/cyan]")
        except Exception as e:
            print_error(f"Failed to create prompt file: {str(e)}")
            raise typer.Exit(1)
            
    open_in_editor(prompt_file)


@prompt_app.command("edit", help="Open an existing prompt file in your configured editor.")
def prompt_edit(
    project: str = typer.Argument(..., help="The project directory or workspace project name."),
    prompt_name: str = typer.Argument(..., help="The name of the prompt file to edit (extension optional)."),
) -> None:
    """Opens a prompt file in the configured editor."""
    from promptcli.core import find_prompt_file, PromptNotFoundError, ProjectNotFoundError
    
    resolved_project_path = resolve_project_path(project)
    try:
        prompt_file = find_prompt_file(str(resolved_project_path), prompt_name)
        open_in_editor(prompt_file)
    except (ProjectNotFoundError, PromptNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)


@prompt_app.command("delete", help="Delete a prompt file from a project.")
def prompt_delete(
    project: str = typer.Argument(..., help="The project directory or workspace project name."),
    prompt_name: str = typer.Argument(..., help="The name of the prompt file to delete (extension optional)."),
) -> None:
    """Deletes a prompt file from prompts/ and offers to delete its output."""
    from promptcli.core import delete_prompt_file, delete_output_file, find_prompt_file, PromptNotFoundError, ProjectNotFoundError
    
    resolved_project_path = resolve_project_path(project)
    try:
        prompt_file = find_prompt_file(str(resolved_project_path), prompt_name)
        confirm = typer.confirm(
            f"Are you sure you want to delete prompt '{prompt_file.name}'?",
            default=False,
        )
        if confirm:
            output_file = resolved_project_path / "outputs" / f"{prompt_file.stem}.md"
            has_output = output_file.is_file()
            
            delete_prompt_file(str(resolved_project_path), prompt_name)
            print_success(f"Prompt file '{prompt_file.name}' deleted successfully.")
            
            if has_output:
                delete_out_confirm = typer.confirm(
                    f"Would you also like to delete the corresponding output file '{output_file.name}'?",
                    default=True,
                )
                if delete_out_confirm:
                    try:
                        delete_output_file(str(resolved_project_path), prompt_file.stem)
                        print_success(f"Output file '{output_file.name}' deleted successfully.")
                    except Exception as e:
                        print_error(f"Failed to delete output file: {str(e)}")
        else:
            print_info("Delete operation cancelled.")
    except (ProjectNotFoundError, PromptNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)


@prompt_app.command("list", help="List all available prompts in a project directory.")
def prompt_list(
    project: str = typer.Argument(..., help="The project directory or workspace project name.")
) -> None:
    """Lists all prompts inside the prompts/ folder."""
    from promptcli.core import list_prompts, ProjectNotFoundError
    from promptcli.ui import display_prompts_table
    
    resolved_project_path = resolve_project_path(project)
    try:
        prompts = list_prompts(str(resolved_project_path))
        if not prompts:
            print_info(f"No prompts found in project directory '{resolved_project_path}'.")
        else:
            display_prompts_table(str(resolved_project_path), prompts)
    except ProjectNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)


# --- Output Management Subcommands ---

@output_app.command("open", help="Open a generated output markdown file in your configured editor.")
def output_open(
    project: str = typer.Argument(..., help="The project directory or workspace project name."),
    prompt_name: str = typer.Argument(..., help="The prompt name (matches output file stem)."),
) -> None:
    """Opens a generated output file in the configured editor."""
    resolved_project_path = resolve_project_path(project)
    output_file = resolved_project_path / "outputs" / f"{prompt_name}.md"
    
    if not output_file.is_file():
        print_error(f"Output file '{prompt_name}.md' not found in project '{resolved_project_path}'.")
        raise typer.Exit(1)
        
    open_in_editor(output_file)


@output_app.command("list", help="List all generated outputs in a project directory.")
def output_list(
    project: str = typer.Argument(..., help="The project directory or workspace project name.")
) -> None:
    """Lists all outputs inside the outputs/ folder in a styled table."""
    from promptcli.core import list_outputs, ProjectNotFoundError
    
    resolved_project_path = resolve_project_path(project)
    try:
        outputs = list_outputs(str(resolved_project_path))
        if not outputs:
            print_info(f"No outputs found in project directory '{resolved_project_path}'.")
            return
            
        from rich.table import Table
        table = Table(
            title=f"Generated Outputs in [bold cyan]{resolved_project_path.name}[/bold cyan]",
            title_style="bold underline",
            border_style="blue",
            header_style="bold magenta",
            expand=True,
        )
        table.add_column("Output Name", style="bold cyan")
        table.add_column("File Extension", style="green")
        table.add_column("File Size", style="yellow", justify="right")
        table.add_column("Last Modified", style="white")
        
        for o in outputs:
            table.add_row(
                o["name"],
                o["extension"],
                o["size_str"],
                o["last_modified"],
            )
        console.print(table)
    except ProjectNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)


@output_app.command("delete", help="Delete a generated output markdown file.")
def output_delete(
    project: str = typer.Argument(..., help="The project directory or workspace project name."),
    prompt_name: str = typer.Argument(..., help="The prompt name (matches output file stem)."),
) -> None:
    """Deletes a generated output markdown file after confirmation."""
    from promptcli.core import delete_output_file
    
    resolved_project_path = resolve_project_path(project)
    output_file = resolved_project_path / "outputs" / f"{prompt_name}.md"
    
    if not output_file.is_file():
        print_error(f"Output file '{prompt_name}.md' not found in project '{resolved_project_path}'.")
        raise typer.Exit(1)
        
    confirm = typer.confirm(
        f"Are you sure you want to permanently delete output file '{output_file.name}'?",
        default=False,
    )
    if confirm:
        try:
            delete_output_file(str(resolved_project_path), prompt_name)
            print_success(f"Output file '{output_file.name}' deleted successfully.")
        except Exception as e:
            print_error(f"Failed to delete output file: {str(e)}")
            raise typer.Exit(1)
    else:
        print_info("Delete operation cancelled.")


@app.command("run", hidden=True)
def run_project(
    project: str = typer.Argument(..., help="The path to the project directory"),
    prompt: Optional[str] = typer.Argument(
        None,
        help="The prompt file name (extension optional)",
    ),
    list_prompts_flag: bool = typer.Option(
        False,
        "--list",
        help="List all available prompts in the project directory",
    ),
    feed_all: bool = typer.Option(
        False,
        "--feed-all",
        help="Generate outputs for all prompts in the project directory",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output files without confirmation",
    ),
) -> None:
    """Internal command to handle project-specific prompts and feeds."""
    from promptcli.core import (
        ProjectNotFoundError,
        PromptNotFoundError,
        GenerationError,
        list_prompts,
        find_prompt_file,
        generate_output,
    )
    from promptcli.key_manager import load_key

    resolved_project_path = resolve_project_path(project)
    project_path_str = str(resolved_project_path)

    # 1. Check if listing prompts
    if list_prompts_flag:
        try:
            prompts = list_prompts(project_path_str)
            if not prompts:
                print_info(f"No prompts found in project directory '{project_path_str}'.")
            else:
                display_prompts_table(project_path_str, prompts)
        except ProjectNotFoundError as e:
            settings = SettingsManager()
            if not settings.workspace_dir:
                print_error(f"Project directory '{project}' does not exist.")
                print_info("Tip: You can configure a default workspace using: [bold]promptcli workspace set <directory>[/bold]")
                print_info("Or provide a valid relative/absolute path to your project directory.")
            else:
                print_error(str(e))
            raise typer.Exit(1)
        return

    # 2. Check if feeding all prompts
    if feed_all:
        api_key = load_key()
        if not api_key:
            print_error("Gemini API key is missing. Please save it first using: promptcli gemini-key --save")
            raise typer.Exit(1)

        try:
            prompts = list_prompts(project_path_str)
            if not prompts:
                print_warning(f"No prompts found in project directory '{project_path_str}' to feed.")
                return

            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
            )

            print_info(f"Feeding all {len(prompts)} prompts in project directory '{project_path_str}'...")

            success_count = 0
            failed_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Generating responses...", total=len(prompts))

                for p in prompts:
                    prompt_file = resolved_project_path / "prompts" / p["filename"]
                    progress.update(task, description=f"Processing {p['filename']}...")

                    try:
                        out_path = resolved_project_path / "outputs" / f"{prompt_file.stem}.md"
                        if out_path.exists() and not force:
                            # Suspend progress bar for interactive overwrite confirmation
                            progress.stop()
                            confirm = typer.confirm(
                                f"Output file '{out_path.name}' already exists. Overwrite?",
                                default=True,
                            )
                            progress.start()
                            if not confirm:
                                print_info(f"Skipped '{p['filename']}'.")
                                failed_count += 1
                                progress.advance(task)
                                continue

                        generate_output(project_path_str, prompt_file, api_key)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        print_error(f"Failed '{p['filename']}': {str(e)}")
                    progress.advance(task)

            # Summarize the run
            if success_count > 0:
                print_success(f"Successfully generated {success_count} prompt response(s).")
            if failed_count > 0:
                print_warning(f"Failed or skipped {failed_count} prompt response(s).")

        except ProjectNotFoundError as e:
            settings = SettingsManager()
            if not settings.workspace_dir:
                print_error(f"Project directory '{project}' does not exist.")
                print_info("Tip: You can configure a default workspace using: [bold]promptcli workspace set <directory>[/bold]")
                print_info("Or provide a valid relative/absolute path to your project directory.")
            else:
                print_error(str(e))
            raise typer.Exit(1)
        return

    # 3. Handle single prompt generation
    if not prompt:
        print_error("Missing argument 'PROMPT'. Please specify a prompt file name or use --list / --feed-all.")
        raise typer.Exit(1)

    api_key = load_key()
    if not api_key:
        print_error("Gemini API key is missing. Please save it first using: promptcli gemini-key --save")
        raise typer.Exit(1)

    try:
        prompt_file = find_prompt_file(project_path_str, prompt)

        out_path = resolved_project_path / "outputs" / f"{prompt_file.stem}.md"
        if out_path.exists() and not force:
            confirm = typer.confirm(
                f"Output file '{out_path.name}' already exists. Overwrite?",
                default=True,
            )
            if not confirm:
                print_info("Cancelled response generation.")
                return

        with console.status(
            f"[bold green]Contacting Gemini API for '{prompt_file.name}'...",
            spinner="dots",
        ):
            out_file = generate_output(project_path_str, prompt_file, api_key)

        try:
            display_out = out_file.relative_to(Path.cwd())
        except ValueError:
            display_out = out_file

        print_success(f"Generated response saved to [cyan]{display_out}[/cyan].")

    except (ProjectNotFoundError, PromptNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)
    except GenerationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(1)


def main() -> None:
    """CLI entry point which transforms positional arguments to subcommand if needed."""
    # Reconfigure stdout/stderr to UTF-8 to prevent encoding errors on Windows console
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    # Pre-parse arguments: if first argument is not a known subcommand/option,

    # route it dynamically to the hidden "run" subcommand.
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        known_commands = {
            "create",
            "gemini-key",
            "workspace",
            "project",
            "prompt",
            "output",
            "run",
            "--help",
            "-h",
            "--version",
            "-v",
        }
        if first_arg not in known_commands and not first_arg.startswith("-"):
            sys.argv.insert(1, "run")

    app()

