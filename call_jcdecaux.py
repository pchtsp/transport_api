import click
import jcdecaux as jc

@click.group()
def cli():
    pass

@click.option('--path', default='', help='Absolute path to directory.')
@cli.command()
def dynamic(path):
    self = jc.JCDecaux(path)
    self.download_backup_dynamic()
    click.echo('Dynamic download succesfully')

@click.option('--path', default='', help='Absolute path to directory.')
@cli.command()
def static(path):
    self = jc.JCDecaux(path)
    self.download_backup_static()
    click.echo('Static download succesfully')


if __name__ == '__main__':
    cli()
