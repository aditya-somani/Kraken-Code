import click

"""
@click.command()
@click.argument("class_name")
@click.option("--name", default="World", help="The name to greet.")
def main(class_name, name):
    click.echo(f"Class name: {class_name}")
    click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    main()

Example:
    H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
    $ python notebooks/test02.py "God" --name "Aditya"
    Class name: God
    Hello, Aditya!
"""
"""
@click.group()
def cli():
    "This is my main database tool."
    pass

@cli.command()
def init():
    click.echo('Initializing Database...')

@cli.command()
def drop():
    click.echo('Dropping Database...')

if __name__ == '__main__':
    cli()

# Example:
    H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
    $ python notebooks/test02.py init
    Initializing Database...
---------------------------------------------------------------------
    H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
    $ python notebooks/test02.py drop
    Dropping Database...
---------------------------------------------------------------------
    H.P@DESKTOP-0COHH16 MINGW64 ~/Desktop/Kraken Code (main)
    $ python notebooks/test02.py --help
    Usage: test02.py [OPTIONS] COMMAND [ARGS]...

    This is my main database tool.

    Options:
    --help  Show this message and exit.

    Commands:
    drop
    init
"""