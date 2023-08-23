import click
import curses
# from app.api.controllers import search_controller, album_controller, tagging_controller

def load_file(file_path):
    """Load a file and return its content."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        click.echo(f"File not found: {file_path}")
        return None

def show_menu(stdscr):
    """Display a menu and allow keyboard navigation to select options."""
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    options = ["Search for audio files", "Manage albums", "Tag audio files"]
    selected_option = 0

    while True:
        stdscr.clear()

        for i, option in enumerate(options):
            if i == selected_option:
                stdscr.addstr(i, 0, option, curses.A_REVERSE)
            else:
                stdscr.addstr(i, 0, option)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and selected_option > 0:
            selected_option -= 1
        elif key == curses.KEY_DOWN and selected_option < len(options) - 1:
            selected_option += 1
        elif key == 10:  # Enter key
            break

    stdscr.clear()
    stdscr.refresh()

    file_path = click.prompt("Enter the file path:", type=click.Path(exists=True))
    content = load_file(file_path)

    if content is not None:
        if selected_option == 0:
            search_controller.search(content)
        elif selected_option == 1:
            # Split the content as needed for the 'album' action
            # For example: album_controller.manage(album_name, artist_name)
            pass
        elif selected_option == 2:
            tagging_controller.tag(content, tags=None)

@click.group()
def cli():
    """CLI Autotagging Tool - Manage and tag audio files."""
    pass

@cli.command()
@click.option('--query', '-q', help='Search query for audio files')
def search(query):
    """Search for audio files."""
    if query:
        search_controller.search(query)
    else:
        click.echo("Please provide a search query using --query or -q.")

@cli.command()
@click.argument('album_name', required=True)
@click.argument('artist_name', required=True)
def album(album_name, artist_name):
    """Manage albums."""
    album_controller.manage(album_name, artist_name)

@cli.command()
@click.argument('file_path', required=True, type=click.Path(exists=True))
@click.option('--tags', '-t', help='Tags to add to the audio file')
def tag(file_path, tags):
    """Tag audio files."""
    if tags:
        tagging_controller.tag(file_path, tags)
    else:
        click.echo("Please provide tags to add using --tags or -t.")

@cli.command()
def load():
    """Load a file and choose an action interactively."""
    curses.wrapper(show_menu)

if __name__ == '__main__':
    cli()
