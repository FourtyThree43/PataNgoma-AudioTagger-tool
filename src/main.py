#!/home/kemboiray/PataNgoma-AudioTagger-tool/env/bin/python3

from dotenv import load_dotenv
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from rgbprint import gradient_print, gradient_scroll, Color
from src.patangoma.track import TrackInfo
from mediafile import MediaFile
import click
import os
import toml


sep = os.sep
PROJECT_SPECS = os.path.normpath(f"{os.path.expanduser('~')}/PataNgoma-AudioTagger-tool/pyproject.toml")


def get_app_info():
    # Load the toml file
    data = toml.load(PROJECT_SPECS)

    # Get the application name and version
    app_name = data.get('project', {}).get('name')
    app_version = data.get('project', {}).get('version')

    return app_name, app_version

def app_info():
    """Print a welcome message."""
    app_name, app_version = get_app_info()

    gradient_print(f"            ♥ {app_name} - {app_version} ♥", start_color='red', end_color='gold', end='\n')
    gradient_print(' ──────────────────────────────────────────────────', start_color='orange', end_color='red', end='\n')
    gradient_print('  │ GitHub  : https://github.com/FourtyThree43/  │ ', start_color='red', end_color='orange', end='\n')
    gradient_print('  │           PataNgoma-AudioTagger-tool         │ ', start_color='red', end_color='orange', end='\n')
    gradient_print('  │ Authors : @FourtyThree43                     │ ', start_color='red', end_color='orange', end='\n')
    gradient_print('  │           @Kemboiray                         │ ', start_color='red', end_color='orange', end='\n')
    gradient_print('  │           @Patrick-052                       │ ', start_color='red', end_color='orange', end='\n')
    gradient_print(' ──────────────────────────────────────────────────', start_color='red', end_color='orange')


def set_default_path():
    """Set default path to music directory."""
    load_dotenv()
    tail = os.getenv("MUSIC_PATH")

    if tail:
        tail = os.path.normpath(tail)  # Normalize path separator
        music_path = os.path.join(os.path.expanduser('~'), tail)
    else:
        click.secho(
            "Path to music directory not set, defaulting to current directory",
            fg="yellow")
        music_path = os.getcwd()
    return music_path

def is_valid(file):
    if not isinstance(file, str):
        file = file[0]
    try:
        MediaFile(file)
        return True
    except:
        click.secho("Error: Invalid or unsupported file format, exiting", fg="red")
        return False

def interactive_selection(music_path):
    """Interactive selection of file from list."""
    if music_path[-1] != sep:
        music_path += sep
    filename = inquirer.filepath(
        message="Please enter a path or select file from list:\n",
        amark="✔️",
        qmark=">",
        validate=PathValidator(is_file=True, message="Input is not a file"),
        default=f"{music_path}",
        transformer=lambda x: f"File: {os.path.basename(x)}",
        instruction="Press <tab> to list directory contents",
        long_instruction=
        "Use: <enter> to select/deselect, <up>/<down> to navigate").execute()
    return os.path.expanduser(filename)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--path',
              '-p',
              type=click.Path(exists=True, dir_okay=True, resolve_path=True),
              help="Path to the audio file or its parent directory")
def main(ctx, path):
    """ Main entry point for the CLI."""
    app_info()

    if ctx.invoked_subcommand is None:
        if path:
            if os.path.isdir(path):
                click.echo("Path provided is a directory, please select a file")
                path = interactive_selection(path)
            ctx.obj = path
        else:
            ctx.obj = interactive_selection(set_default_path())
        if is_valid(ctx.obj):
            _main_menu(ctx)
        else:
            exit(1)


def _main_menu(ctx):
    """Display the Main menu of available actions."""

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
        _submenu_show(ctx)
    elif action == "Update-Tags":
        _submenu_update(ctx)
    elif action == "Delete-Tags":
        delete([fp])


def _submenu_show(ctx):
    """Display a submenu for 'Show-Tags' options."""
    fp = ctx.obj

    show_tags_choices = [
        Choice(name="Show all metadata", value="all"),
        Choice(name="Show existing metadata", value="existing"),
        Choice(name="Show missing metadata", value="missing"),
        Choice(name="Go back", value="Back"),
    ]

    show_tags_action = inquirer.select(
        message="Select a 'Show-Tags' option:",
        choices=show_tags_choices,
        default="Back",
        amark="✔️",
        qmark=">",
        instruction=
        "Use: <enter> to select/deselect, <up>/<down> to navigate"
    ).execute()

    if show_tags_action == "all":
        ctx.invoke(show, file_path=fp, all_t=True)
    elif show_tags_action == "existing":
        ctx.invoke(show, file_path=fp, existing=True)
    elif show_tags_action == "missing":
        ctx.invoke(show, file_path=fp, missing=True)
    elif show_tags_action == "Back":
        menu(ctx)


def _submenu_update(ctx):
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
        instruction="Use: <Tab> to select/deselect, <up>/<down> to navigate or type keyword to search the list"
    ).execute()
    updates = []
    click.echo("Enter new values as prompted:")
    for key in selected_fields:
        updates.append(
            inquirer.text(message=f"{key}:", qmark=">", amark="✔️").execute())
    ctx.invoke(update,
               file_path=fp,
               updates=tuple([
                   f"{key}={value}"
                   for key, value in zip(selected_fields, updates)
               ]))


@click.command()
@click.option('--all_t',
              '-a',
              is_flag=True,
              show_default=True,
              default=False,
              help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              show_default=True,
              default=True,
              help='Show only existing metadata.')
@click.option('--missing',
              '-m',
              is_flag=True,
              show_default=True,
              default=False,
              help='Show missing metadata.')
@click.argument('file_path',
                type=click.Path(exists=True, resolve_path=True,
                                dir_okay=False))
def show(file_path, all_t: bool, existing: bool, missing: bool):
    """Show metadata for a media file."""
    if is_valid(file_path):
        track = TrackInfo(file_path)

        if all_t:
            track.show_all_metadata()
        elif missing:
            track.show_missing_metadata()
        else:
            track.show_existing_metadata()
    else:
        exit(1)


@click.command()
@click.argument('file_path',
                type=click.Path(exists=True, resolve_path=True,
                                dir_okay=False))
@click.argument('updates', nargs=-1)
def update(file_path, updates):
    """Update metadata for a media file."""
    if is_valid(file_path):
        track = TrackInfo(file_path)
        md_pre_update = track.as_dict()

        track.batch_update_metadata(updates)

        if track.has_changed(track.as_dict(), md_pre_update):
            click.echo(f"Metadata changes for {track.metadata.filename}:")
            for key, value in track.as_dict().items():
                if key != "images" and md_pre_update[key] != value:
                    if key not in ("art", "lyrics"):
                        click.echo(f"{key}: {md_pre_update[key]} -> {value}")
                    else:
                        click.echo(f"{key}: changed (diff too large to display)")

            if click.confirm("Do you want to save these changes?"):
                track.save()
                click.echo("Changes saved.")
            else:
                click.echo("Changes not saved.")
        else:
            click.echo("No changes to save.")
    else:
        exit(1)


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def delete(file_path):
    """Delete all metadata from the media file."""
    if is_valid(file_path):
        track = TrackInfo(file_path)

        proceed = inquirer.confirm(
            message="Are you sure you want to delete all tags?",
            default=False).execute()
        if proceed:
            end_color = Color.random
            gradient_scroll(f"Deleting tags for {file_path}",
                            start_color=Color.gold,
                            end_color=end_color,
                            delay=0.01)
            track.delete()
        else:
            gradient_scroll("Aborting...",
                            start_color=Color.red,
                            end_color=Color.blue)
    else:
        exit(1)


main.add_command(update)
main.add_command(delete)
main.add_command(show)

if __name__ == "__main__":
    main()
