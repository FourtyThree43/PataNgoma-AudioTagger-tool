import os
import sys
import click
from InquirerPy import inquirer
from dotenv import load_dotenv

load_dotenv()
music_path = os.getenv("MUSIC_PATH")


def interactive_selection():
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


def main():
    if len(sys.argv) < 2:
        print("No file selected")
        filename = interactive_selection()
    else:
        filename = sys.argv[1]

    if os.path.isdir(filename):
        click.secho(f"'{filename}' is a directory", fg="yellow")
        filename = interactive_selection()

    elif not os.path.exists(filename):
        if os.path.sep not in filename:
            filename = os.path.join(music_path, filename)

            if os.path.exists(filename):
                if os.path.isdir(filename):
                    click.secho(f"'{filename}' is a directory", fg="yellow")
                    filename = interactive_selection()
            else:
                click.secho(f"The file '{filename}' does not exist", fg="bright_red")
                filename = interactive_selection()
        else:
            click.secho(f"The file '{filename}' does not exist", fg="bright_red")
            filename = interactive_selection()

    click.secho(f"The file '{filename}' has been selected", fg="bright_green")


if __name__ == "__main__":
    main()
