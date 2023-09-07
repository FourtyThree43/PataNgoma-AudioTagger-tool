from tags import TrackInfo
import click

# Example usage
click.echo("Provide file path to Manipulate tags ...")
file_path = click.prompt("File Path", type=click.Path(exists=True))
track = TrackInfo(file_path)

# Show original metadata
print("Original Metadata:")
track.show_metadata()

# Update metadata
click.echo("")
click.echo("Editing existing tags")
cmd_choices = ["Single tag", "All tags"]
for index, choice in enumerate(cmd_choices, start=1):
    click.echo(f"{index}: {choice}")

choice = click.prompt("Choice", type=click.IntRange(min=1, max=len(cmd_choices)))

tag_choices = ["title", "artist", "album", "genres"]
if choice == 1:
    click.echo("")
    for index, tag in enumerate(tag_choices, start=1):
        click.echo(f"{index}: {tag}")

    tagg = click.prompt("Tag", type=click.IntRange(min=1, max=len(tag_choices)))
    new_value = click.prompt("Enter new value")

    updates = [f"{tag_choices[tagg - 1]}={new_value}"]
    track.update_metadata(updates)
elif choice == 2:
    pass

# Show updated metadata
print("\nUpdated Metadata:")
track.show_metadata()

# Save the updated metadata
track.save()
