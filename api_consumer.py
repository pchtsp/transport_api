import json
import requests
import os
import datetime


class API(object):

    def __init__(self, key, cache_dir, api):
        """

        :param key: dictionary with name and value for passing key argument
        :param cache_dir: name of folder to do backups
        :param api: slice of url to make calls
        """
        self.api = api
        self.key = key
        self.cache_dir = cache_dir

    def get_key(self):
        return self.key

    def get_url(self, service_name):
        return self.api + service_name

    def get_cache(self, file_name, directory=None, ext=None):
        if directory is None:
            directory = self.cache_dir
        cache = os.path.join(directory, file_name)
        if ext:
            cache += ext
        if os.path.exists(cache):
            print('found the file, loading cache')
            with open(cache, 'r') as f:
                return json.load(f)
        return None

    def set_cache(self, file_name, json_data, directory=None, ext=None):
        if directory is None:
            directory = self.cache_dir
        cache = os.path.join(directory, file_name)
        if ext:
            cache += ext
        cache_base = os.path.dirname(cache)
        if not os.path.exists(cache_base):
            os.makedirs(cache_base)
        with open(cache, 'w') as f:
            json.dump(json_data, f, indent=4)

    def get_service_cache(self, service_name, cache=True, ext=None, **kwargs):
        if cache:
            cache_data = self.get_cache(service_name, ext=ext)
            if cache_data is not None:
                return cache_data
        print('did not find the file.')
        url = self.get_url(service_name)
        key = self.get_key()
        payload = dict(**key, **kwargs)
        result = requests.get(url, params=payload)
        json_data = result.json()
        if cache:
            print('writing cache.')
            self.set_cache(service_name, json_data, ext=ext)
        return json_data

    def get_timestamp(self, format="%Y-%m-%dT%H"):
        """
        Useful for naming downloaded files
        :return:
        """
        return datetime.datetime.utcnow().strftime(format)