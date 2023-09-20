# Purpose: Command line interface for PataNgoma AutoTagger

from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from InquirerPy.base.control import Choice
from rgbprint import gradient_print, gradient_scroll, Color
from rich.panel import Panel
import click
import rich
import os
from dotenv import load_dotenv


def hello():
    """Print a welcome message."""
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))


def set_default_path():
    """Set default path to music directory."""
    load_dotenv()
    tail = os.getenv("MUSIC_PATH")

    if tail:
        music_path = f"{os.path.expanduser('~')}{os.path.sep}{tail}"
    else:
        click.secho(
            "Path to music directory not set, defaulting to current directory",
            fg="yellow")
        music_path = os.getcwd()
    return music_path


def interactive_selection(music_path):
    """Interactive selection of file from list."""
    if music_path[-1] != os.path.sep:
        music_path += os.path.sep
    filename = inquirer.filepath(
        message="Please enter a path or select file from list:\n",
        amark="✔️",
        qmark=">",
        validate=PathValidator(is_file=True, message="Invalid file path"),
        default=f"{music_path}",
        transformer=lambda x: f"File: {os.path.basename(x)}",
        instruction="Press <tab> to list directory contents",
        long_instruction=
        "Use <up> and <down> arrow keys to navigate list, then <enter> to select"
    ).execute()
    return os.path.expanduser(filename)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--path',
              '-p',
              type=click.Path(exists=True, dir_okay=True, resolve_path=True),
              help="Path to the audio file or its parent directory")
def main(ctx, path):
    hello()
    if ctx.invoked_subcommand is None:
        # if path and os.path.isdir(path):
        #     click.echo("Path provided is a directory, please select a file")
        #     path = interactive_selection(path)
        # ctx.obj = path
        # if ctx.obj is None:
        #     ctx.obj = interactive_selection(set_default_path())
        # menu(ctx)
        if path:
            if os.path.isdir(path):
                click.echo("Path provided is a directory, please select a file")
                path = interactive_selection(path)
            ctx.obj = path
        else:
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
                                       amark="✔️",
                                       qmark=">").execute()

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
    valid_fields = {
        "artist": None,
        "album": None,
        "title": None,
        "track": None,
        "genre": None,
        "year": None,
        "comment": None
    }
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
        updates.append(
            inquirer.text(message=f"{key}:", qmark=">", amark="✔️").execute())
    ctx.invoke(update,
               file_path=[fp],
               tags=tuple([
                   f"{key}={value}"
                   for key, value in zip(selected_fields, updates)
               ]))


@click.command()
@click.argument('file_path',
                type=click.Path(exists=True, resolve_path=True,
                                dir_okay=False))
@click.option('--all_t', '-a', is_flag=True, help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              help='Show only existing metadata.')
@click.option('--missing', '-m', is_flag=True, help='Show missing metadata.')
def show(file_path, all_t, existing, missing):
    if all_t:
        print(f"Displaying all metadata for {file_path}")
    elif existing:
        print(f"Displaying existing metadata for {file_path}")
    elif missing:
        print(f"Displaying missing metadata for {file_path}")
    else:
        print(f"Displaying existing metadata for {file_path}")


@click.command()
@click.argument('file_path',
                type=click.Path(exists=True, resolve_path=True,
                                dir_okay=False))
@click.argument('tags', nargs=-1)
def update(file_path, tags):
    print(f"Updating tags for {file_path}")
    click.echo("Your updates:")
    print(tags)


@click.command()
@click.argument('file_path',
                type=click.Path(exists=True, resolve_path=True,
                                dir_okay=False))
def delete(file_path):
    proceed = inquirer.confirm(
        message="Are you sure you want to delete all tags?",
        default=False).execute()
    if proceed:
        end_color = Color.random
        gradient_scroll(f"Deleting tags for {file_path}",
                        start_color=Color.gold,
                        end_color=end_color,
                        delay=0.01)
    else:
        gradient_scroll("Aborting...",
                        start_color=Color.red,
                        end_color=Color.blue)


main.add_command(update)
main.add_command(delete)
main.add_command(show)

if __name__ == "__main__":
    main()
