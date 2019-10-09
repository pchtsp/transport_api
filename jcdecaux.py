
# "GET https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}"

import api_consumer as api
import pytups as pt
import os
try:
    import keyring as k
except ImportError:
    raise ImportError('You need to have manually created your own keyring file. See README.txt')


class JCDecaux(api.API):

    def __init__(self, cache_dir='data_velo'):
        self.all_stations = 'v3/stations'
        super().__init__(key=dict(apiKey=k.jcdecaux['key']),
                         cache_dir=cache_dir,
                         api="https://api.jcdecaux.com/vls/")

    def get_stations(self, cache=True):
        return self.get_service_cache(self.all_stations, ext='.json', cache=cache)

    @staticmethod
    def get_static(station):
        static = ['number', 'contractName', 'name', 'address', 'position', 'banking', 'bonus', 'overflow', 'shape']
        return pt.SuperDict.from_dict(station).filter(static)

    @staticmethod
    def get_dynamic(station):
        dynamic = ['number', 'contractName', 'name', 'status', 'connected', 'totalStands', 'mainStands', 'overflowStands', 'lastUpdate']
        return pt.SuperDict.from_dict(station).filter(dynamic)

    def download_backup_dynamic(self):
        stations = self.get_stations(cache=False)
        dynamic = pt.TupList(stations).apply(self.get_dynamic)
        ts = self.get_timestamp()
        self.set_cache(self.all_stations + '/dynamic/' + ts, dynamic, ext='.json')

    def download_backup_static(self):
        stations = self.get_stations(cache=False)
        static = pt.TupList(stations).apply(self.get_static)
        ts = self.get_timestamp()
        self.set_cache(self.all_stations + '/static/' + ts, static, ext='.json')

    def get_contrats(self, cache=True):
        return self.get_service_cache('v3/contracts', ext='.json', cache=cache)

Contrat = \
{
  "name" : "Lyon",
  "commercial_name" : "Vélo'v",
  "country_code" : "FR",
  "cities" : [
    "Lyon",
    "Villeurbanne",
    ...
  ]
}

# contrats
# https://api.jcdecaux.com/vls/v3/contract

# stations
# https://api.jcdecaux.com/vls/v3/station

# 1 station
# https://api.jcdecaux.com/vls/v3/stations/{station_number}?contract={contract_name}

# station par contrat
# https://api.jcdecaux.com/vls/v3/stations?contract={contract_name}

# parkings par contrat
# https://api.jcdecaux.com/parking/v1/contracts/{contract_name}/parks

# 1 parking
# https://api.jcdecaux.com/parking/v1/contracts/{contract_name}/parks/{park_number}

if __name__ == '__main__':

    self = JCDecaux()
    contrats = self.get_contrats()
