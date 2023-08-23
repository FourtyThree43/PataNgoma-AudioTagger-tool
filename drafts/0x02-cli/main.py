#!/usr/bin/env python3
"""Creating a CLI which is the main entry
   point to the PataNgoma Auto-tagging tool"""

import click
from tags import MetaData


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
        "Edit tags",
        "search tags"
    ]

    click.echo("")
    click.echo("Provide file path to Manipulate tags ...")
    file_path = click.prompt("File Path", type=click.Path(exists=True))
    click.echo("")
    click.echo("Select an action:")
    for index, choice in enumerate(choices, start=1):
        click.echo(f"{index}: {choice}")

    choice = click.prompt("Choice", type=click.IntRange(min=1,
                                                        max=len(choices)))

    if choice == 1:
        meta = MetaData(file_path)
        meta.show_metadata()

    elif choice == 2:
        click.echo("Edit tags ...")
        exist = ['title', 'artist', 'album', 'genres']
        click.

    elif choice == 3:
        click.echo("Search tags ...")


if __name__ == '__main__':
    cli()
