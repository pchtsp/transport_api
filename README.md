# Wrangling with transport data

## Download and install

```
git clone http://github.com/pchtsp/transport_api
cd transport_api
pipenv install
```

## Keyring

You need to create a file named `keyring.py` with the same structure:

```python
jcdecaux = dict(key='SOME_KEY')
tisseo = dict(key='SOME_OTHER_KEY')
```

## Using existing APIs

To access bike statios status for JCDecaux bikes, just run the following:

```python
from jcdecaux import *
api = JCDecaux()
stations = api.get_stations(cache=False)
print(stations)
```

## To create a new API

A new file, following the examples (`jcdecaux.py`, `tisseo.py`) should be created and a class implementing the main api is advised.
That way, some things are taken into account, such as *cache* and *requests*.
