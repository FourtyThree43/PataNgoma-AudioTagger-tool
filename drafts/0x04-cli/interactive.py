import os
import sys
import click
import rich
from rich.panel import Panel
from rgbprint import gradient_scroll, Color
from InquirerPy import inquirer
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
    # selection = inquirer.filepath(message="Please select a file:",
    #                               path_type="file",
    #                               only_files=True,
    #                               only_directories=False,
    #                               validate=lambda x: os.path.exists(x)).execute()
    files = [
        i for i in os.listdir(music_path)
        if not os.path.isdir(f"{music_path}/{i}")
    ]
    choices = [f"{i+1}. {file}" for i, file in enumerate(files)]
    selection = inquirer.select(message="Please select a file:",
                                choices=choices,
                                transformer=lambda x: ".".join(x.split(".")[1:]).strip(),
                                amark=">").execute()
    index = int(selection.split(".")[0]) - 1
    return os.path.join(music_path, files[index])


def file_handler(filename):
    pass


def main():
    rich.print(Panel.fit("[bright_red]PataNgoma", title="Welcome",
                         subtitle="Giving a face to your music", padding=(0, 15)))
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

    click.secho(f"The file '{filename}' has been selected", fg="bright_green")


if __name__ == "__main__":
    main()
