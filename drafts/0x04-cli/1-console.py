from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rgbprint import Color
from rich.panel import Panel
import click
import rich
from pathlib import Path


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--file_path',
              '-f',
              type=click.Path(exists=True),
              help="Path to the audio file")
def cli(ctx, file_path):
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))

    ctx.obj = {"file_path": file_path}

    if ctx.invoked_subcommand is None:
        show_menu(ctx)


def show_menu(ctx):
    """Display a menu of available actions."""
    if ctx.obj["file_path"] is None:
        print(
            f"[{Color.red}CRITICAL{Color.reset}] File path must be provided with {Color.green}-f, --file_path{Color.reset} or use {Color.green}--help{Color.reset} to see options"
        )
        return

    action = inquirer.select(message="Select an action:",
                             choices=[
                                 "Show-Tags",
                                 "Update-Tags",
                                 "Delete-Tags",
                                 Choice(value=None, name="Exit"),
                             ],
                             default=None,
                             amark="✔️").execute()
    fp = Path(str(ctx.obj["file_path"]))

    if action == "Show-Tags":
        _show_submenu(ctx)
    elif action == "Update-Tags":
        update_tags(ctx.obj["file_path"])
    elif action == "Delete-Tags":
        delete_tags(fp)

def _show_submenu(ctx):
    """Display a submenu for 'Show-tags' options."""
    file_path = ctx.obj["file_path"]

    show_tags_choices = [
        Choice("Show all metadata", name="all"),
        Choice("Show existing metadata", name="existing"),
        Choice("Show missing metadata", name="missing"),
        Choice(value=None, name="Back"),
    ]

    show_tags_action = inquirer.select(message="Select a 'Show-tags' option:",
                                       choices=show_tags_choices,
                                       default=None,
                                       amark="✔️").execute()

    if show_tags_action == "all":
        show_tags(file_path, all_t=True, existing=False, missing=False)
    elif show_tags_action == "existing":
        show_tags(file_path, all_t=False, existing=True, missing=False)
    elif show_tags_action == "missing":
        show_tags(file_path, all_t=False, existing=False, missing=True)
    elif show_tags_action == "Back":
        show_menu(ctx)


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--all_t', '-a', is_flag=True, help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              help='Show only existing metadata.')
@click.option('--missing', '-m', is_flag=True, help='Show missing metadata.')
def show_tags(file_path, all_t, existing, missing):
    """Show metadata for a media file."""
    if all_t:
        print(f"Displaying all metadata for {file_path}")
    elif existing:
        print(f"Displaying existing metadata for {file_path}")
    elif missing:
        print(f"Displaying missing metadata for {file_path}")
    else:
        print(f"Displaying existing metadata for {file_path}")


def update_tags(file_path):
    print(f"Updating tags for {file_path}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=None))
def delete_tags(file_path):
    print(f"Deleting tags for {file_path}")


cli.add_command(show_tags)

if __name__ == "__main__":
    cli()
