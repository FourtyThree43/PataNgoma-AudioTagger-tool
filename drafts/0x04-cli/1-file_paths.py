import click
import pathlib


@click.group(invoke_without_command=True)
@click.pass_context
@click.option('--file_path',
              '-f',
              type=click.Path(exists=True),
              help="Path to file")
def cli(ctx, file_path):
    """Display a menu of available actions."""
    ctx.obj = {"file_path": file_path}

    if ctx.invoked_subcommand is None:
        fp = ctx.obj["file_path"]
        print(fp, type(fp))
        process_file([fp])


@click.command()
@click.argument('file_path', type=click.Path(exists=True))
def process_file(file_path):
    print(f'Processing file: {file_path}')


cli.add_command(process_file)

if __name__ == '__main__':
    cli()
