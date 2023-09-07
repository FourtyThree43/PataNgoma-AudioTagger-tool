#!/usr/bin/env python3
"""Creating a CLI which is the main entry
   point to the PataNgoma Auto-tagging tool"""

import click
from mediafile import MediaFile


@click.group()
def cli():
    """Nesting all other commands"""
    click.echo("Welcome")
    click.echo("Enjoy personalizing your Music files")


@cli.command()
def tag():
    """Responding to users needs"""
    choices = [
        "View existing tags",
        "Extract new tags",
        "Edit tags"
    ]

    click.echo("")
    click.echo("Select an action:")
    for index, choice in enumerate(choices, start=1):
        click.echo(f"{index}: {choice}")

    choice = click.prompt("Choice", type=click.IntRange(min=1,
                                                        max=len(choices)))

    if choice == 1:
        click.echo("Provide file path to view existing tags ...")
        file_path = click.prompt("File Path", type=click.Path(exists=True))

        tag = MediaFile(file_path)

        click.echo(f"\tTitle: {tag.title}")
        click.echo(f"\tArtist: {tag.albumartist}")
        click.echo(f"\tAlbum: {tag.album}")
        click.echo(f"\tDuration: {tag.length} seconds")

    elif choice == 2:
        click.echo("Extracting new tags ...")
    elif choice == 3:
        click.echo("Editing tags ...")


if __name__ == '__main__':
    cli()
