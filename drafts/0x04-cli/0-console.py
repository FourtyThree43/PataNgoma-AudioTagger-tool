from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rgbprint import gradient_scroll, Color
from rich.panel import Panel
import click
import rich


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--file_path',
              '-f',
              type=click.Path(exists=True),
              help="Path to the audio file")
def cli(ctx, file_path):
    rich.print(
        Panel.fit("\n[green]PataNgoma AutoTagger\n",
                  title="Welcome",
                  subtitle="Enjoy personalizing your Music files",
                  padding=(0, 15)))

    ctx.obj = {"file_path": file_path}

    if ctx.invoked_subcommand is None:
        show_menu(ctx)


def show_menu(ctx):
    """Display a menu of available actions."""
    if ctx.obj["file_path"] is None:
        print(
            f"[{Color.red}CRITICAL{Color.reset}] File path must be provided with {Color.green}-f, --file_path{Color.reset} or use {Color.green}--help{Color.reset} to see options"
        )
        return

    action = inquirer.select(message="Select an action:",
                             choices=[
                                 "Show-tags",
                                 "Update-Tags",
                                 "Delete-Tags",
                                 Choice(value=None, name="Exit"),
                             ],
                             default=None,
                             amark="✔️").execute()

    if action == "Show-tags":
        show_tags(ctx.obj["file_path"])
    elif action == "Update-Tags":
        update_tags(ctx.obj["file_path"])
    elif action == "Delete-Tags":
        delete_tags(ctx.obj["file_path"])


def show_tags(file_path):
    print(f"Showing tags for {file_path}")


def update_tags(file_path):
    print(f"Updating tags for {file_path}")


def delete_tags(file_path):
    print(f"Deleting tags for {file_path}")


if __name__ == "__main__":
    cli()
