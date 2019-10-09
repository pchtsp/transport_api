
import os
import api_consumer as api

try:
    import keyring as k
except ImportError:
    raise ImportError('You need to have manually created your own keyring file. See README.txt')


class Tisseo(api.API):

    def __init__(self):
        super().__init__(key=dict(key=k.tisseo['key']), cache_dir='data_tisseo', api="https://api.tisseo.fr/v1/")

    def get_stop_areas(self, cache=True):
        return self.get_service_cache('stop_areas.json', cache=cache)

    def get_lines(self, cache=True):
        return self.get_service_cache('lines.json', cache=cache)

    def get_schedules(self, stopAreaId, cache=0, **kwargs):
        # This one is different because the backup is per stopAreaId instead of all in the same file
        # if cache==1 => read and write.
        # if cache==2 => only read
        # if cache==3 => only write
        service_name = 'stops_schedules.json'
        base, ext = os.path.splitext(service_name)
        directory = os.path.join(self.cache_dir, base)
        filename = stopAreaId + ext
        if cache in [1, 2]:
            cache_data = self.get_cache(filename, directory=directory)
            if cache_data is not None:
                return cache_data
        json_data = self.get_service_cache(service_name, cache=False, stopAreaId=stopAreaId, **kwargs)
        if cache in [1, 3]:
            self.set_cache(filename, json_data, directory=directory)
        return json_data

    def get_all_schedules(self):
        stop_areas = self.get_stop_areas()
        stop_area_codes = [c['id'] for c in stop_areas['stopAreas']['stopArea']]
        args = dict(number=100000, displayRealTime=0, maxDays=7, datetime='2019-10-14 05:00')
        stop_area_codes_f = stop_area_codes
        for stopArea in stop_area_codes_f:
            schedule = self.get_schedules(stopAreaId=stopArea, cache=1, **args)


if __name__ == '__main__':
    self = Tisseo()
    self.get_all_schedules()