
# "GET https://api.jcdecaux.com/vls/v1/stations?contract={contract_name}&apiKey={api_key}"

import api_consumer as api
try:
    import keyring as k
except ImportError:
    raise ImportError('You need to have manually created your own keyring file. See README.txt')


class JCDecaux(api.API):

    def __init__(self):
        super().__init__(key=dict(apiKey=k.jcdecaux['key']), cache_dir='data_velo', api="https://api.jcdecaux.com/vls/")

    def get_stations(self):
        return self.get_service_cache('v3/stations', ext='.json')

def get_key():
  return k.jcdecaux['key']

def get_url(service_name):
    return "https://api.jcdecaux.com/vls/v1/" + service_name

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
    stations = self.get_stations()