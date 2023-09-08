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
@click.option('--all', '-a', is_flag=True, help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              help='Show only existing metadata.')
@click.option('--missing', '-m', is_flag=True, help='Show missing metadata.')
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
    md_pre_update = track.as_dict()

    track.batch_update_metadata(updates)

    if track.has_changed(track.as_dict(), md_pre_update):
        click.echo(f"Metadata changes for {track.metadata.filename}:")
        for key, value in track.as_dict().items():
            if md_pre_update[key] != value:
                if key not in ("art", "images", "lyrics"):
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


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def delete(file_path):
    """Delete's all metadata from the media file."""
    track = TrackInfo(file_path)
    if click.confirm(
            f"Confirm removal of all {track.metadata.filename} tags?"):
        track.delete()
        click.echo("Metadata tags removed!.")
    else:
        click.echo("Deletion canceled.")


def show_menu():
    pass


cli.add_command(show)
cli.add_command(update)
cli.add_command(delete)

if __name__ == '__main__':
    cli()
