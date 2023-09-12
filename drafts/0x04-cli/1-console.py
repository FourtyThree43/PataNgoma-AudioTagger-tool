from os.path import isdir
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from InquirerPy.base.control import Choice
# from rgbprint import Color
from rich.panel import Panel
import click
import rich
import os
from dotenv import load_dotenv


def set_default_path():
    load_dotenv()
    tail = os.getenv("MUSIC_PATH")

    if tail:
        music_path = f"{os.path.expanduser('~')}{os.path.sep}{tail}"
    else:
        click.secho("Path to music directory not set, defaulting to current directory", fg="yellow")
        music_path = os.getcwd()
    return music_path


def interactive_selection(music_path):
    filename = inquirer.filepath(
        message="Please enter a path or select file from list:\n",
        amark="✔️",
        qmark=">",
        validate=PathValidator(is_file=True, message="Invalid file path"),
        default=f"{music_path}{os.path.sep}",
        transformer=lambda x: f"File: {os.path.basename(x)}",
        instruction="Press <tab> to list directory contents",
        long_instruction="Use <up> and <down> arrow keys to navigate list, then <enter> to select"
    ).execute()
    return os.path.expanduser(filename)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--path',
              '-p',
              type=click.Path(exists=True, dir_okay=True, resolve_path=True),
              help="Path to the audio file or its parent directory")
def cli(ctx, path):
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))

    if path and os.path.isdir(path):
        click.echo("Path provided is a directory, please select a file")
        path = interactive_selection(path)
    if ctx.invoked_subcommand is None:
        ctx.obj = path # {"path": path}
        if ctx.obj is None:
            ctx.obj = interactive_selection(set_default_path())
        menu(ctx)


def menu(ctx):
    """Display a menu of available actions."""

    action = inquirer.select(message="Select an action:",
                             choices=[
                                 "Show-Tags",
                                 "Update-Tags",
                                 "Delete-Tags",
                                 Choice(value=None, name="Exit"),
                             ],
                             default=None,
                             qmark=">",
                             amark="✔️").execute()
    fp = ctx.obj

    if action == "Show-Tags":
        _show_submenu(ctx)
    elif action == "Update-Tags":
        _update_submenu(ctx)
        # update([fp])
    elif action == "Delete-Tags":
        delete([fp])


def _show_submenu(ctx):
    """Display a submenu for 'Show-tags' options."""
    fp = ctx.obj

    show_tags_choices = [
        Choice(name="Show all metadata", value="all"),
        Choice(name="Show existing metadata", value="existing"),
        Choice(name="Show missing metadata", value="missing"),
        Choice(name="Go back", value="Back"),
    ]

    show_tags_action = inquirer.select(message="Select a 'Show-tags' option:",
                                       choices=show_tags_choices,
                                       default="Back",
                                       amark="✔️", qmark=">").execute()

    if show_tags_action == "all":
        ctx.invoke(show, file_path=[fp], all_t=True)
    elif show_tags_action == "existing":
        ctx.invoke(show, file_path=[fp], existing=True)
    elif show_tags_action == "missing":
        ctx.invoke(show, file_path=[fp], missing=True)
    elif show_tags_action == "Back":
        menu(ctx)


def _update_submenu(ctx):
    """Display a submenu for 'Update-tags' options."""
    fp = ctx.obj
    valid_fields = {"artist": None, "album": None, "title": None, "track": None, "genre": None, "year": None, "comment": None}
    selected_fields = inquirer.fuzzy(
        message="Select fields:",
        choices=list(valid_fields.keys()),
        multiselect=True,
        validate=lambda result: len(result) >= 1,
        invalid_message="minimum 1 selection",
        max_height="70%",
        qmark=">",
        amark="✔️",
    ).execute()
    updates = []
    click.echo("Enter new values as prompted:")
    for key in selected_fields:
        updates.append(inquirer.text(message=f"{key}:", qmark= ">", amark="✔️").execute())
    click.echo("Your updates:")
    for key, value in zip(selected_fields, updates):
        click.echo(f"{key}: {value}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, resolve_path=True))
@click.option('--all_t', '-a', is_flag=True, help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              help='Show only existing metadata.')
@click.option('--missing', '-m', is_flag=True, help='Show missing metadata.')
def show(file_path, all_t, existing, missing):
    """Show metadata for a media file."""
    if os.path.isdir(file_path[0]):
        click.echo("Path provided is a directory, please select a file")
        file_path = interactive_selection(file_path[0])
    if all_t:
        print(f"Displaying all metadata for {file_path[0]}")
    elif existing:
        print(f"Displaying existing metadata for {file_path[0]}")
    elif missing:
        print(f"Displaying missing metadata for {file_path[0]}")
    else:
        print(f"Displaying existing metadata for {file_path[0]}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, resolve_path=True))
@click.argument('tags', nargs=-1)
def update(file_path, tags):
    if os.path.isdir(file_path[0]):
        click.echo("Path provided is a directory, please select a file")
        file_path = interactive_selection(file_path[0])
    print(f"Updating tags for {file_path[0]}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, resolve_path=True))
def delete(file_path):
    if os.path.isdir(file_path[0]):
        click.echo("Path provided is a directory, please select a file")
        file_path = interactive_selection(file_path[0])
    print(f"Deleting tags for {file_path[0]}")


cli.add_command(update)
cli.add_command(delete)
cli.add_command(show)

if __name__ == "__main__":
    cli()
