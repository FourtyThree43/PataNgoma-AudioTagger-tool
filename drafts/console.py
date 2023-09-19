import click
import typing
from mediafile import MediaFile


@click.group()
def cli():
    """A simple CLI for managing your music library."""
    click.echo("Welcome")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def info(file_path):
    """Display metadata for an audio file."""
    tag = MediaFile(file_path)
    click.echo(f"Title: {tag.title}")
    click.echo(f"Artist: {tag.albumartist}")
    click.echo(f"Album: {tag.album}")
    click.echo(f"Duration: {tag.length} seconds")


if __name__ == '__main__':
    cli()
