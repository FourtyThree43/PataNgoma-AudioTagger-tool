import os
import sys
import click
import rich
from rich.panel import Panel
from rgbprint import gradient_scroll, Color
from InquirerPy import inquirer
from InquirerPy.validator import PathValidator
from mediafile import MediaFile
from dotenv import load_dotenv


def set_default_path():
    load_dotenv()
    tail = os.getenv("MUSIC_PATH")

    if tail:
        music_path = f"{os.path.expanduser('~')}{os.path.sep}{tail}"
    else:
        click.secho("Path to music directory not set, defaulting to current working directory",
                    fg="yellow")
        music_path = os.getcwd()
    return music_path


def interactive_selection(music_path):
    filename = inquirer.filepath(
        message="Please enter a file path:\n",
        amark="✔",
        validate=PathValidator(is_file=True, message="You've entered an invalid file path"),
        default=f"{music_path}{os.path.sep}",
        transformer=lambda x: f"Selected: {os.path.basename(x)}",
    ).execute()
    return filename


def file_handler(filename):
    pass


def main():
    rich.print(Panel.fit("[bright_red]PataNgoma", title="Welcome",
                         subtitle="Giving a face to your music", padding=(0, 15)), "\n", sep="")
    music_path = set_default_path()
    if len(sys.argv) < 2:
        print("No file selected")
        filename = interactive_selection(music_path)
    else:
        filename = sys.argv[1]

    if os.path.isdir(filename):
        click.secho(f"'{filename}' is a directory", fg="yellow")
        filename = interactive_selection(music_path)

    elif not os.path.exists(filename):
        if os.path.sep not in filename:
            filename = os.path.join(music_path, filename)

            if os.path.exists(filename):
                if os.path.isdir(filename):
                    click.secho(f"'{filename}' is a directory", fg="yellow")
                    filename = interactive_selection(music_path)
            else:
                click.secho(f"The file '{filename}' does not exist", fg="bright_red")
                filename = interactive_selection(music_path)
        else:
            click.secho(f"The file '{filename}' does not exist", fg="bright_red")
            filename = interactive_selection(music_path)

    click.secho(f"Processing {filename}", fg="bright_green")


if __name__ == "__main__":
    main()
