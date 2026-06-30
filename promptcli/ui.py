from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()

def show_banner() -> None:
    """Displays the professional PromptCLI startup banner."""
    # Custom text styling to match and elevate the requested box representation
    banner_text = Text()
    banner_text.append("           PromptCLI\n", style="bold cyan")
    banner_text.append("  AI Prompt Management Toolkit\n", style="italic white")
    banner_text.append("─" * 38 + "\n", style="dim blue")
    banner_text.append("Author   : ", style="bold green")
    banner_text.append("Indrajit Ghosh\n", style="white")
    banner_text.append("Position : ", style="bold green")
    banner_text.append("Postdoctoral Fellow\n", style="white")
    banner_text.append("Institute: ", style="bold green")
    banner_text.append("IIT Kanpur\n", style="white")
    banner_text.append("Version  : ", style="bold green")
    banner_text.append("1.0.0", style="white")
    
    panel = Panel(
        banner_text,
        border_style="bold blue",
        expand=False,
        padding=(1, 3),
    )
    console.print(panel)

def print_success(message: str) -> None:
    """Prints a styled success message with a checkmark icon."""
    console.print(f"[bold green]✔[/bold green] {message}")

def print_warning(message: str) -> None:
    """Prints a styled warning message with an alert icon."""
    console.print(f"[bold yellow]⚠[/bold yellow] [yellow]{message}[/yellow]")

def print_error(message: str) -> None:
    """Prints a styled error message with a cross icon."""
    console.print(f"[bold red]✘[/bold red] [red]{message}[/red]")

def print_info(message: str) -> None:
    """Prints a styled info message with an information icon."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")

def display_prompts_table(project_name: str, prompts: list[dict]) -> None:
    """Displays a list of prompts in a colorful table.
    
    Args:
        project_name: The name of the project.
        prompts: A list of prompt file metadata dictionaries.
    """
    table = Table(
        title=f"Available Prompts in [bold cyan]{project_name}[/bold cyan]",
        title_style="bold underline",
        border_style="blue",
        header_style="bold magenta",
        expand=True,
    )
    
    table.add_column("Prompt Name", style="bold cyan")
    table.add_column("File Extension", style="green")
    table.add_column("File Size", style="yellow", justify="right")
    table.add_column("Last Modified", style="white")
    
    for prompt in prompts:
        table.add_row(
            prompt["name"],
            prompt["extension"],
            prompt["size_str"],
            prompt["last_modified"],
        )
        
    console.print(table)
