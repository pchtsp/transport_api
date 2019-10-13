import api_consumer as api
import pytups as pt
import os
import click


class CityBikes(api.API):

    def __init__(self, cache_dir='city_bikes'):
        self.all_networks = 'v2/networks'
        super().__init__(key=None,
                         cache_dir=cache_dir,
                         api="http://api.citybik.es/")

    def get_stations(self, cache=True):
        return self.get_service_cache(self.all_networks, ext='.json', cache=cache)

    def download_backup_dynamic(self):
        try:
            apis = self.get_relevant_networks()
        except:
            # if not found, get all...
            apis = self.get_networks()
        apis_data = apis.to_dict(None).vapply(self.get_service_cache, ext='.json', cache=False)
        ts = self.get_timestamp(format="%Y-%m-%dT%H%M%S")
        for key, data in apis_data.items():
            self.set_cache(key + '/' + ts, data, ext='.json')

    def get_networks(self, cache=True):
        return self.get_service_cache(self.all_networks, ext='.json', cache=cache)

    def get_relevant_networks(self):
        filename = os.path.join(self.cache_dir, 'v2/relevant_networks.txt')
        with open(filename, 'r') as f:
            content = f.readlines()
        return pt.TupList(content).apply(str.strip)



@click.group()
def cli():
    pass


@click.option('--path', default='', help='Absolute path to directory.')
@cli.command()
def dynamic(path):
    self = CityBikes(path)
    self.download_backup_dynamic()
    click.echo('Dynamic download succesfully')


if __name__ == '__main__':
    cli()
