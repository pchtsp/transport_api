import os
import ujson as json
import pytups as pt
import pprint

data_dir = 'data_tisseo/stops_schedules/'

def read_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

# we read lines
lines = read_json('data_tisseo/lines.json')
stop_areas = read_json('data_tisseo/stop_areas.json')

# we read stops
files = os.listdir(data_dir)
files_data = pt.TupList(files).apply(lambda v: data_dir + v).apply(read_json)
one_stop = files_data[0]

get_line_time = lambda v: (v['line']['shortName'], v['dateTime'])
all_visits = \
    pt.TupList(one_stop['departures']['departure']).\
    apply(get_line_time).\
    to_dict(1).\
    vapply(sorted)

all_visits