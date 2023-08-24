import click
from tags import TrackInfo

@click.group()
def cli():
    click.echo("Welcome to the Music CLI")
    click.echo("=" * 30)
    click.echo()
    pass

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--all', is_flag=True, help='Show all metadata, including None values.')
@click.option('--existing', is_flag=True, help='Show existing metadata, excluding "art" and None values.')
@click.option('--missing', is_flag=True, help='Show missing metadata, including None values.')
def show(file_path, all, existing, missing):
    """Show metadata for a media file."""
    track = TrackInfo(file_path)

    if all:
        track.show_all_metadata()
    elif existing:
        track.show_existing_metadata()
    elif missing:
        track.show_missing_metadata()
    else:
        # If no option is specified, show existing metadata by default
        track.show_existing_metadata()

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('updates', nargs=-1)
def update(file_path, updates):
    """Update metadata for a media file."""
    track = TrackInfo(file_path)
    track.update_metadata(updates)
    track.save()

@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def delete(file_path):
    """Delete metadata for a media file."""
    track = TrackInfo(file_path)
    track.delete()

def show_menu():
    pass

cli.add_command(show)
cli.add_command(update)
cli.add_command(delete)

if __name__ == '__main__':
    cli()
