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
        ctx.invoke(pf, file_path=[fp], g=True)
        # ctx.invoke to invoke a Click command from code.
        # The arguments should be passed as keyword arguments.


# (nargs=-1). This allows us to pass a list of file paths to the function.
@click.command()
@click.option("--g", is_flag=True, show_default=True, default=False, help="G")
@click.option("--b", is_flag=True, show_default=True, default=False, help="B")
@click.argument('file_path', nargs=-1, type=click.Path(exists=True))
def pf(file_path, g, b):
    for fp in file_path:
        if g:
            print(f'Gr : {fp}')
        elif b:
            print(f'Br : {fp}')
        else:
            print(f'Processing file: {fp}')


cli.add_command(pf)

if __name__ == '__main__':
    cli()
