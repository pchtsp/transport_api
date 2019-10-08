import click
import jcdecaux as jc

@click.group()
def cli():
    pass

@cli.command()
def dynamic():
    self = jc.JCDecaux()
    self.download_backup_dynamic()
    click.echo('Dynamic download succesfully')

@cli.command()
def static():
    self = jc.JCDecaux()
    self.download_backup_static()
    click.echo('Static download succesfully')


if __name__ == '__main__':
    cli()
