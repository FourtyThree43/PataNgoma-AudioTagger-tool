from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rgbprint import Color
from rich.panel import Panel
import click
import rich


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--path',
              '-p',
              type=click.Path(exists=True, dir_okay=False),
              help="Path to the audio file")
def cli(ctx, path):
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))

    ctx.obj = {"path": path}

    if ctx.invoked_subcommand is None:
        show_menu(ctx)


def show_menu(ctx):
    """Display a menu of available actions."""
    if ctx.obj["path"] is None:
        print(f"[{Color.red}CRITICAL{Color.reset}]" +
              "File path must be provided using " +
              f"{Color.green}-p, --path{Color.reset}"
              f" or use {Color.green}--help{Color.reset} to see options")
        return

    action = inquirer.select(message="Select an action:",
                             choices=[
                                 "Show-Tags",
                                 "Update-Tags",
                                 "Delete-Tags",
                                 Choice(value=None, name="Exit"),
                             ],
                             default=None,
                             amark="✔️").execute()
    fp = ctx.obj["path"]

    if action == "Show-Tags":
        _show_submenu(ctx)
    elif action == "Update-Tags":
        update_tags([fp])
    elif action == "Delete-Tags":
        delete_tags([fp])


def _show_submenu(ctx):
    """Display a submenu for 'Show-tags' options."""
    fp = ctx.obj["path"]

    show_tags_choices = [
        Choice(name="Show all metadata", value="all"),
        Choice(name="Show existing metadata", value="existing"),
        Choice(name="Show missing metadata", value="missing"),
        Choice(name="Go back", value="Back"),
    ]

    show_tags_action = inquirer.select(message="Select a 'Show-tags' option:",
                                       choices=show_tags_choices,
                                       default="Back",
                                       amark="✔️").execute()

    # print(f"show_tags_action: {show_tags_action}")
    if show_tags_action == "all":
        ctx.invoke(show_tags, file_path=[fp], all_t=True)
    elif show_tags_action == "existing":
        ctx.invoke(show_tags, file_path=[fp], existing=True)
    elif show_tags_action == "missing":
        ctx.invoke(show_tags, file_path=[fp], missing=True)
    elif show_tags_action == "Back":
        show_menu(ctx)


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--all_t', '-a', is_flag=True, help='Show all metadata.')
@click.option('--existing',
              '-e',
              is_flag=True,
              help='Show only existing metadata.')
@click.option('--missing', '-m', is_flag=True, help='Show missing metadata.')
def show_tags(file_path, all_t, existing, missing):
    """Show metadata for a media file."""
    if all_t:
        print(f"Displaying all metadata for {file_path}")
    elif existing:
        print(f"Displaying existing metadata for {file_path}")
    elif missing:
        print(f"Displaying missing metadata for {file_path}")
    else:
        print(f"Displaying existing metadata for {file_path}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def update_tags(file_path):
    print(f"Updating tags for {file_path}")


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def delete_tags(file_path):
    print(f"Deleting tags for {file_path}")


cli.add_command(update_tags)
cli.add_command(delete_tags)
cli.add_command(show_tags)

if __name__ == "__main__":
    cli()
