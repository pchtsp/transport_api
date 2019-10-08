
import os
import api_consumer as api

try:
    import keyring as k
except ImportError:
    raise ImportError('You need to have manually created your own keyring file. See README.txt')


class Tisseo(api.API):

    def __init__(self):
        super().__init__(key=dict(key=k.tisseo['key']), cache_dir='data_tisseo', api="https://api.tisseo.fr/v1/")

    def get_stop_areas(self):
        return self.get_service_cache('stop_areas.json')

    def get_lines(self):
        return self.get_service_cache('lines.json')

    def get_schedules(self, stopAreaId, cache=False, **kwargs):
        # This one is different because the backup is per stopAreaId instead of all in the same file

        service_name = 'stops_schedules.json'
        base, ext = os.path.splitext(service_name)
        directory = self.cache_dir + base + '/'
        filename = stopAreaId + ext
        if cache:
            cache_data = self.get_cache(filename, directory=directory)
            if cache_data is not None:
                return cache_data
        json_data = self.get_service_cache(service_name, cache=False, stopAreaId=stopAreaId, **kwargs)
        if cache:
            self.set_cache(filename, json_data, directory=directory)
        return json_data


if __name__ == '__main__':
    import pprint
    self = Tisseo()
    stop_areas = self.get_stop_areas()
    lines = self.get_lines()
    # lines['lines']['line'][10]['id']
    stop_area_codes = [c['id'] for c in stop_areas['stopAreas']['stopArea']]
    # r = get_schedules(lineId='11821953316814891', cache=False)
    args = dict(number=10000, displayRealTime=0, maxDays=2)
    stop_area_codes_f = stop_area_codes[99:200]
    for stopArea in stop_area_codes_f:
        schedule = self.get_schedules(stopAreaId=stopArea, cache=True, **args)
    # schedule = get_schedules(stopAreaId='1970324837185612', cache=True, **args)
    # 'datetime' date and time at which we request the schedules
    # pprint.pprint(schedule['departures']['departure'])
    len(schedule['departures']['departure'])
    # print(r)


