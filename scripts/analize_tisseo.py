import os
import ujson as json
import pytups as pt
import numpy as np
import pandas as pd
import tisseo as ti
import pprint
import datetime


def read_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)


def _treat_stop_area(one_stop):
    get_line_time = lambda v: (v['line']['shortName'], v['dateTime'])
    return pt.TupList(one_stop['departures']['departure']).\
        apply(get_line_time).\
        to_dict(1).\
        vapply(sorted)


def write_table(timetable, filename):
    _test = timetable.apply(lambda v: ','.join(v))
    with open( filename ,'w') as f:
        f.write('\n'.join(_test))


def generate_timetable():
    data_dir = 'data_tisseo/stops_schedules/'
    files = os.listdir(data_dir)
    _get_name = lambda v: os.path.splitext(v)[0]
    files_data = \
        pt.TupList(files). \
            to_dict(None). \
            vapply(_get_name). \
            reverse(). \
            vapply(lambda v: data_dir + v). \
            vapply(read_json)

    all_passing = \
        files_data. \
            vapply(_treat_stop_area). \
            to_dictup(). \
            to_tuplist()

    return all_passing

class Node(object):

    # consists of a trip arriving at a stop at a certain time (in a seq)
    def __init__(self, trip_id, stop_sequence, info):
        self.seq = stop_sequence
        self.trip = trip_id
        data = info['stop_times'][trip_id][stop_sequence]
        self.stop = data['stop_id']
        self.time = data['arrival_time']
        self.info = info
        self.route = self.info['trips'][self.trip]['route_id']
        self.hash = hash(self.__key())
        return

    def __repr__(self):
        route_name = self.info['routes'][self.route]['route_short_name']
        stop_name = self.info['stops'][self.stop]['stop_name']
        time = self.time.strftime('%H:%M')
        return repr('{} @ {} Line:{}'.format(stop_name, time, route_name))

    def get_all_neighbors(self, max_time=None):
        return self.get_neighbors_in_trip(max_time) + self.get_neighbors_in_stop(max_time)

    def get_neighbors_in_trip(self, max_time=None):
        data = self.info['stop_times'][self.trip]
        if max_time is not None:
            data = data.clean(func=lambda v: v['arrival_time'] < max_time)
        last = max(data.keys())
        return [Node(self.trip, seq, self.info)
                for seq in range(self.seq+1, last+1)]

    def get_neighbors_in_stop(self, max_time=None, delta_min=10):
        # we make a look for other trips in the same stop filtered by time (5 min wait?)
        # also: they should not share the same route_id.
        min_time = self.time + datetime.timedelta(minutes=1)
        _max_time = self.time + datetime.timedelta(minutes=delta_min)
        if max_time is None:
            max_time = _max_time
        else:
            max_time = min(_max_time, max_time)
        # we get the pandas data frame corresponding to that stop
        # and filter it accordingly
        other_lines = self.info['stop_times_2'].loc[self.stop]
        _filter = (other_lines.arrival_time.between(min_time, max_time)) & \
                  (other_lines.route_id != self.route)
        candidates = other_lines[_filter]
        return table_to_candidates(candidates, self.info)

    def __key(self):
        return (self.trip, self.seq)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.__key() == other.__key()


def table_to_candidates(stop_times, info):
    candidates = stop_times[['trip_id', 'stop_sequence']].to_records(index=False)
    return [Node(*can, info) for can in candidates]

def read_table(name, directory):
    return pd.read_csv(directory + name + '.txt', dtype=str)

def get_tables(directory = 'data_tisseo/tisseo_gtfs/'):
    names = pt.TupList(['stop_times', 'trips', 'routes', 'stops', 'calendar'])
    return names.to_dict(None).vapply(read_table, directory=directory)

def get_info_object(tables, day_ok_week='monday', min_hour='11:00:00', max_hour='12:00:00'):

    trips = tables['trips']
    calendar = tables['calendar']
    calendar_r = calendar[calendar[day_ok_week]=='1']
    trips = trips.merge(calendar_r, on='service_id')
    trip_info = trips.\
        set_index('trip_id')[['route_id', 'direction_id']].\
        to_dict(orient='index')
    trip_info = pt.SuperDict.from_dict(trip_info)

    stop_times = tables['stop_times']
    # TODO: fix this so we do not need to chop the end of the day
    stop_times_info = \
        stop_times\
            [stop_times.arrival_time.str.slice(stop=2) < '24'].\
            merge(trips, on='trip_id')
    stop_times_info = \
        stop_times_info[
            stop_times_info.arrival_time.
            between(min_hour, max_hour)].\
            copy()
    stop_times_info.arrival_time = pd.to_datetime(stop_times_info.arrival_time, format='%H:%M:%S')
    stop_times_info.stop_sequence = stop_times_info.stop_sequence.astype(int)
    stop_times_info_1 = \
        stop_times_info.\
        set_index(['trip_id', 'stop_sequence'])\
        [['arrival_time', 'stop_id']].\
        to_dict(orient='index')
    stop_times_info_1 = pt.SuperDict.from_dict(stop_times_info_1).to_dictdict()

    # Maybe make it a dictionary indexed by the stop.
    stop_times_2_info = \
        stop_times_info. \
        set_index('stop_id')[['arrival_time', 'trip_id', 'route_id', 'stop_sequence']]

    route_info = tables['routes'].set_index('route_id').to_dict(orient='index')
    route_info = pt.SuperDict.from_dict(route_info)

    stops_info = tables['stops'].set_index('stop_id').to_dict(orient='index')
    stops_info = pt.SuperDict.from_dict(stops_info)

    return pt.SuperDict(trips=trip_info,
                        stop_times=stop_times_info_1,
                        stop_times_2=stop_times_2_info,
                        routes=route_info,
                        stops=stops_info)

def graph_from_node(current, max_hour):
    # TODO: make it possible to do multiple hops and not only two
    initial = current
    arcs = pt.SuperDict()
    max_time = pd.to_datetime(max_hour, format="%H:%M:%S")
    # nodes that I have not yet seen neighbors
    remaining = [current]
    iter = 0
    while len(remaining) > 0 and iter < 10000:
        iter += 1
        current = remaining.pop()
        if current in arcs:
            # if I've seen this node before:
            # it means I already added all arcs
            continue
        print('iter={}, current={}'.format(iter, current))
        neighbors  = current.get_neighbors_in_trip(max_time)
        if current.trip == initial.trip:
            # if we have not yet changed trip, we can search for a change
            neighbors += current.get_neighbors_in_stop(max_time)
        for node in neighbors:
            arcs.set_m(current, node, value=1)
            remaining.append(node)
    return arcs

def get_lats_longs_from_node(directory, trip, sequence, min_hour, max_hour):
    sequence = int(sequence)
    tables = get_tables(directory)
    info = get_info_object(tables, min_hour=min_hour, max_hour=max_hour)
    current = Node(trip, sequence, info)
    arcs = graph_from_node(current, max_hour=max_hour)
    return get_lats_longs(arcs, info)

def get_lats_longs(arcs, info):
    lats = set()
    longs = set()
    get_lat = lambda v: info['stops'][v.stop]['stop_lat']
    get_lon = lambda v: info['stops'][v.stop]['stop_lon']
    for node, neighbors in arcs.items():
        lats.add(get_lat(node))
        longs.add(get_lon(node))
        for node2 in neighbors:
            lats.add(get_lat(node2))
            longs.add(get_lon(node2))
    return lats, longs

if __name__ == '__main__':

    tables = get_tables()
    routes_r = tables['routes'][['route_id', 'route_short_name']]
    trip_r = tables['trips'][['route_id', 'trip_id']].merge(routes_r, on='route_id')

    min_hour = '08:00:00'
    max_hour = '09:00:00'
    info = get_info_object(tables, min_hour=min_hour, max_hour=max_hour)
    filtered_data = info['stop_times_2'].reset_index()[['trip_id', 'stop_sequence', 'stop_id', 'arrival_time']]
    max_hour_dt = pd.to_datetime(max_hour, format='%H:%M:%S')
    min_hour_dt = pd.to_datetime(min_hour, format='%H:%M:%S')
    stoptimes_L1 = \
        trip_r[trip_r.route_short_name == 'L1']. \
        merge(filtered_data, on='trip_id').\
        merge(tables['stops'], on='stop_id').\
        query('"{}"<=arrival_time<="{}"'.format(min_hour_dt, max_hour_dt)).\
        query('stop_name=="Cité de l\'Hers"').sort_values('arrival_time')

    # stoptimes_L1[:5][['trip_id', 'stop_sequence', 'arrival_time']]
    candidates = table_to_candidates(stoptimes_L1[:5], info)
    current = candidates[0]
    arcs = graph_from_node(current, max_hour=max_hour)
    lats, longs = get_lats_longs(arcs, info)

    # route: ruta (linea de bus)
    # trip: viaje concreto dentro de una ruta
    # service: ligado a un calendario.

    # all_passing = generate_timetable()
    # write_table(all_passing, 'timetables.txt')
    #
    # _testnp = np.genfromtxt('timetables.txt', delimiter=',', dtype=np.dtype('U19'))
    # This way we get a multidimensional numpy
    # _testnp = np.array(all_passing, dtype=np.dtype('U19'))

    # This way we get an array of different types:
    # _testnp = np.array(_test, dtype=np.dtype('U16, U8, U19'))

    # get all rows where second column (line) is equal to 'L1':
    # _testnp[_testnp[:,1]=='L1']

    # get all rows of
    # '2019-10-14 06:09:00' and '2019-10-15 06:09:00'
    # _filter = (_testnp[:,1]=='L1') &  (_testnp[:,2] <= '2019-10-16 03:00:00') & (_testnp[:,2] >= '2019-10-15 03:00:00')
    # data = _testnp[_filter]
    # data_sorted = np.sort(np.unique(data, axis=0), axis=0)

    # we read lines
    # lines = read_json('data_tisseo/lines.json')
    # we read stops
    # def _temp():
    #     from importlib import reload
    #     reload(ti)
    # tisseo = ti.Tisseo()
    # stop_areas = tisseo.get_stop_areas(cache=True,
    #                                    displayLines=1,
    #                                    displayCoordXY=1,
    #                                    timeFrame=7)
    # stop_areas = {a['id']: a for a in stop_areas['stopAreas']['stopArea']}
    # stop_areas = pt.SuperDict.from_dict(stop_areas)
    # stop_areas.values_tl()[0]