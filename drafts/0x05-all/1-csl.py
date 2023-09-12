from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from InquirerPy.base.control import Choice
from rgbprint import Color
from rich.panel import Panel
import click
import rich
import os
from dotenv import load_dotenv


def set_default_path():
    load_dotenv()
    tail = os.getenv("MUSIC_PATH")

    if tail:
        music_path = f"{os.path.join(os.path.expanduser('~'), tail)}"
    else:
        music_path = os.getcwd()
    return music_path


def interactive_selection(music_path):
    filename = inquirer.filepath(
        message="Please enter a file path:\n",
        amark="✔",
        validate=PathValidator(is_file=True, message="Invalid file path"),
        default=f"{music_path}{os.path.sep}",
        transformer=lambda x: f"Selected: {os.path.basename(x)}"
    ).execute()
    return os.path.expanduser(filename)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--path',
              '-p',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              help="Path to the audio file")
def cli(ctx, path):
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))


    if ctx.invoked_subcommand is None:
        ctx.obj = path # {"path": path}
        if ctx.obj is None:
            ctx.obj = interactive_selection(set_default_path())
        show_menu(ctx)


def show_menu(ctx):
    """Display a menu of available actions."""

    action = inquirer.select(message="Select an action:",
                             choices=[
                                 "Show-Tags",
                                 "Update-Tags",
                                 "Delete-Tags",
                                 Choice(value=None, name="Exit"),
                             ],
                             default=None,
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
                                       amark="✔️",).execute()

    if show_tags_action == "all":
        ctx.invoke(show, file_path=[fp], all_t=True)
    elif show_tags_action == "existing":
        ctx.invoke(show, file_path=[fp], existing=True)
    elif show_tags_action == "missing":
        ctx.invoke(show, file_path=[fp], missing=True)
    elif show_tags_action == "Back":
        show_menu(ctx)


def _update_submenu(ctx):
    """Display a submenu for 'Update-tags' options."""
    fp = ctx.obj
    valid_fields = {"artist": None, "album": None, "title": None, "track": None, "genre": None, "year": None, "comment": None}
    selected_fields = inquirer.fuzzy(
        message="Select fields:",
        choices=valid_fields,
        multiselect=True,
        validate=lambda result: len(result) >= 1,
        invalid_message="minimum 1 selection",
        max_height="70%",
    ).execute()
    updates = inquirer.text(message="Enter new values:", completer=selected_fields).execute()


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
    if all_t:
        print(f"Displaying all metadata for {file_path}")
    elif existing:
        print(f"Displaying existing metadata for {file_path}")
    elif missing:
        print(f"Displaying missing metadata for {file_path}")
    else:
        print(f"Displaying existing metadata for {file_path}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, resolve_path=True))
@click.argument('tags', nargs=-1)
def update(file_path):
    print(f"Updating tags for {file_path}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True, resolve_path=True))
def delete(file_path):
    print(f"Deleting tags for {file_path}")


cli.add_command(update)
cli.add_command(delete)
cli.add_command(show)

if __name__ == "__main__":
    cli()
