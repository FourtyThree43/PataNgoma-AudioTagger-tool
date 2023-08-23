# Import necessary modules
import click
from tinytag import TinyTag
from mutagen import File
from rich.console import Console
from rich.table import Table
import sqlite3

# Create a Rich Console instance for styling output
console = Console()

# Define a dictionary of available commands
commands = {
    "tinytag": "info with TinyTag",
    "mutagen": "info with Mutagen",
}

@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--file_path', type=click.Path(exists=True), help="Path to the audio file")
def cli(ctx, file_path):
    """A simple CLI for managing your music library."""
    # Print a styled welcome message and app title
    console.print("[bold cyan]Welcome to My Music Library CLI![/bold cyan]")
    console.print("[bold cyan]====================================[/bold cyan]\n")
    
    # Store the provided file_path in the context
    ctx.obj = {"file_path": file_path}

    # Check if the CLI was invoked without a subcommand, and if so, run select_command
    if ctx.invoked_subcommand is None:
        select_command()

@cli.command()
def T_info():
    """Display metadata for an audio file using TinyTag."""
    # Retrieve the file_path from the context
    file_path = click.get_current_context().obj.get("file_path")

    if file_path:
        tag = TinyTag.get(file_path)
    
        # Create a table to display the metadata
        table = Table(title="File Information", show_header=True, header_style="bold magenta")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        # Add rows for each metadata field
        table.add_row("Title", tag.title)
        table.add_row("Artist", tag.artist)
        table.add_row("Album", tag.album)
        table.add_row("Duration", f"{tag.duration} seconds")

        # Print the table
        console.print(table)
    else:
        console.print("[bold red]Error:[/bold red] No file path provided.")

@cli.command()
def M_info():
    """Display metadata for an audio file using Mutagen."""
    # Retrieve the file_path from the context
    file_path = click.get_current_context().obj.get("file_path")

    if file_path:
        audio = File(file_path)

        if audio is None:
            console.print(f"[bold red]Error:[/bold red] Unable to read metadata for {file_path}")
            return

        # Create a table to display the metadata
        table = Table(title="File Information", show_header=True, header_style="bold magenta")
        table.add_column("Field", style="bold")
        table.add_column("Value")

        # Add rows for each metadata field
        table.add_row("Title", audio.get("title", "N/A"))
        table.add_row("Artist", audio.get("artist", "N/A"))
        table.add_row("Album", audio.get("album", "N/A"))
        table.add_row("Duration", f"{audio.info.length} seconds")

        # Print the table
        console.print(table)
    else:
        console.print("[bold red]Error:[/bold red] No file path provided.")

@cli.command()
@click.option('--command', type=click.Choice(commands.keys()), prompt=True)
def select_command(command):
    """Select the version of 'info' command to run."""
    if command == "tinytag":
        T_info()
    elif command == "mutagen":
        M_info()
    else:
        console.print("[bold red]Error:[/bold red] Invalid command selected.")

if __name__ == '__main__':
    cli()
