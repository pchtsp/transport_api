import os
import ujson as json
import pytups as pt
import pandas as pd
import datetime
import numpy as np

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
    def __init__(self, trip_id, stop_sequence, info, hops=0):
        """

        :param trip_id: the trip (mission, bus)
        :param stop_sequence: sequence of the stop in trip
        :param info: static information on the line
        :param int hops: number of previous transfers before getting into this node
        """
        # convert this to integer has a lot to do with R and
        # it being unable to pass integer arguments
        stop_sequence = int(stop_sequence)
        self.seq = stop_sequence
        self.trip = trip_id
        data = info['stop_times'][trip_id][stop_sequence]
        self.stop = data['stop_id']
        self.time = data['arrival_time']
        self.info = info
        self.route = info['trips'][trip_id]['route_id']
        self.hash = hash(self.__key())
        self.hops = hops
        return

    def __repr__(self):
        route_name = self.info['routes'][self.route]['route_short_name']
        stop_name = self.info['stops'][self.stop]['stop_name']
        time = self.time.strftime('%H:%M')
        return repr('{} @ {} Line:{}'.format(stop_name, time, route_name))

    def get_neighbors_in_trip(self, max_time=None):
        data = self.info['stop_times'][self.trip]
        if max_time is not None:
            data = data.clean(func=lambda v: v['arrival_time'] < max_time)
        if not data:
            return []
        last = max(data.keys())
        return [Node(self.trip, seq, self.info, hops=self.hops)
                for seq in range(self.seq+1, last+1)]

    def get_neighbors_in_stop(self, max_time=None, delta_min=10, walk_speed=5):
        # we take a look for other trips in the same stop filtered by time (5 min wait?)
        # also: they should not share the same route_id.
        _max_time = self.time + datetime.timedelta(minutes=delta_min)
        if max_time is None:
            max_time = _max_time
        else:
            max_time = min(_max_time, max_time)
        # we get the pandas data frame corresponding to that stop or close stops
        # and filter it accordingly
        neighbors = self.info['stops_neigh'][self.stop]
        other_lines = self.info['stop_times_2'].loc[neighbors.keys()]
        other_lines['max_time'] = max_time

        # the minimum time will depend on the distance to that stop
        # other_lines['min_time'] = self.time + datetime.timedelta(minutes=1)
        other_lines['min_time_delta'] = other_lines.index.map(neighbors) * 60/walk_speed + 1
        other_lines['min_time'] = self.time + pd.to_timedelta(other_lines.min_time_delta, unit='minute')

        _filter = (other_lines.arrival_time >= other_lines.min_time) & \
                  (other_lines.arrival_time <= other_lines.max_time) & \
                  (other_lines.route_id != self.route)
        candidates = other_lines[_filter]
        return table_to_candidates(candidates, info=self.info, hops=self.hops+1)

    def __key(self):
        return (self.trip, self.seq)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.__key() == other.__key()


def table_to_candidates(stop_times, **kwargs):
    candidates = stop_times[['trip_id', 'stop_sequence']].to_records(index=False)
    return [Node(*can, **kwargs) for can in candidates]

def read_table(name, directory):
    return pd.read_csv(directory + name + '.txt', dtype=str)

def get_tables(directory = 'data_tisseo/tisseo_gtfs/'):
    names = pt.TupList(['stop_times', 'trips', 'routes', 'stops', 'calendar'])
    return names.to_dict(None).vapply(read_table, directory=directory)

def get_info_object(tables, day_of_week='monday', min_hour='11:00:00', max_hour='12:00:00',
                    max_dist_km_walk = 0.5, **kwargs):

    trips = tables['trips']
    calendar = tables['calendar']
    calendar_r = calendar[calendar[day_of_week] == '1']
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

    stop_times_2_info = \
        stop_times_info. \
        set_index('stop_id')[['arrival_time', 'trip_id', 'route_id', 'stop_sequence']]

    # we want the backup in the table. This is becuase R has problems with no-unique indeces.
    stop_times_2_info['stop_id_backup'] = stop_times_2_info.index

    route_info = tables['routes'].set_index('route_id').to_dict(orient='index')
    route_info = pt.SuperDict.from_dict(route_info)

    stops_neighbors = get_positions_table(tables['stops'], stop_times_2_info)

    complete_graph = \
        stops_neighbors.\
        merge(stops_neighbors, on=['stop_lon_g', 'stop_lat_g'])

    stops_neighbors = get_distance_dict(complete_graph, max_dist_km_walk)

    stops_info = tables['stops'].set_index('stop_id').to_dict(orient='index')
    stops_info = pt.SuperDict.from_dict(stops_info)

    return pt.SuperDict(trips=trip_info,  # trip: {info}
                        stop_times=stop_times_info_1,  # (route, sequence): time and stop
                        stop_times_2=stop_times_2_info,  # indexed table
                        routes=route_info,  # route: {info}
                        stops=stops_info,  # stop: {info}
                        stops_neigh=stops_neighbors  # stop: {stop: dist}
                        )


def get_positions_table(stop_table, stop_times_2_info):
    stops_neighbors = \
        stop_table.\
        set_index('stop_id').\
        loc[stop_times_2_info.index.unique()].\
        reset_index().\
        filter(['stop_id', 'stop_lat', 'stop_lon'])

    stops_neighbors.stop_lat = stops_neighbors.stop_lat.astype(float)
    stops_neighbors.stop_lon = stops_neighbors.stop_lon.astype(float)
    stops_neighbors['stop_lat_g'] = stops_neighbors.stop_lat.round(2)
    stops_neighbors['stop_lon_g'] = stops_neighbors.stop_lon.round(2)
    return stops_neighbors


def get_distance_dict(complete_graph, max_dist_km_walk):
    complete_graph['distance'] = \
        haversine_np(complete_graph.stop_lon_x, complete_graph.stop_lat_x,
                    complete_graph.stop_lon_y, complete_graph.stop_lat_y)
    complete_graph['distance'] = complete_graph['distance'].round(4)
    complete_graph = complete_graph[complete_graph.distance < max_dist_km_walk]

    data_neighbors = \
        complete_graph.\
        filter(['stop_id_x', 'stop_id_y', 'distance']).\
        to_records(index=False)

    return \
        pt.TupList(data_neighbors). \
        to_dict(result_col=2, is_list=False).\
        to_dictdict()


def create_no_stop_node(lat, lon, info, min_hour, max_dist_km_walk):
    # node_table => stop_id
    trip_id = 'FAKE'
    stop_seq = -1
    stop_id = 'FAKE'
    route_id = 'FAKE'
    route_short_name = 'FAKE'
    stop_name = 'FAKE'
    # we update the info object with this fake node

    # stop_ids and arrival_times
    _tup = ('stop_times', trip_id, stop_seq, 'stop_id')
    info.set_m(*_tup, value=stop_id)
    _tup = ('stop_times', trip_id, stop_seq, 'arrival_time')
    value = datetime.datetime.strptime(min_hour, "%H:%M:%S")
    info.set_m(*_tup, value=value)

    # route_id:
    _tup = ('trips', trip_id, 'route_id')
    info.set_m(*_tup, value=route_id)

    # names for representation:
    _tup = ('routes', route_id, 'route_short_name')
    info.set_m(*_tup, value=route_short_name)
    _tup = ('stops', stop_id, 'stop_name')
    info.set_m(*_tup, value=stop_name)

    # we get the distances to those nodes to update the neighbors info
    data = dict(stop_id=[stop_id],
                stop_lat=[lat],
                stop_lon=[lon],
                stop_lat_g= [round(lat, 2)],
                stop_lon_g= [round(lon, 2)])
    stop_position = pd.DataFrame(data)
    stop_table = info['stops'].to_df(orient='index').rename_axis('stop_id').reset_index()
    neighbors_positions = get_positions_table(stop_table, info['stop_times_2'])

    complete_graph = \
        stop_position.\
        merge(neighbors_positions, on=['stop_lon_g', 'stop_lat_g'])

    neighbors = get_distance_dict(complete_graph, max_dist_km_walk).get(stop_id)
    _tup = ('stops_neigh', stop_id)
    info.set_m(*_tup, value=neighbors)

    # finally, we create the node and return the graph
    # since this artificial node is not a real line, we reduce the default hop number
    return Node(trip_id=trip_id, stop_sequence=stop_seq, info=info, hops=-1)

def graph_from_nodes(lat, lon, info, min_hour, max_dist_km_walk, **kwargs):
    current = create_no_stop_node(lat, lon, info, min_hour, max_dist_km_walk)
    return graph_from_node(current, **kwargs)

def graph_from_node(current, max_hour, max_hops=1):
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
        if current.hops < max_hops:
            # if we have not yet reached the max number of trips,
            # we can search for a change of trip
            neighbors += current.get_neighbors_in_stop(max_time)
        for node in neighbors:
            arcs.set_m(current, node, value=1)
            remaining.append(node)
    return arcs

def get_lats_longs_from_node(directory, trip, sequence, min_hour, max_hour):
    tables = get_tables(directory)
    info = get_info_object(tables, min_hour=min_hour, max_hour=max_hour)
    current = Node(trip, sequence, info)
    arcs = graph_from_node(current, max_hour=max_hour)
    return get_lats_longs(arcs, info)

def get_lats_longs(arcs, info):
    nodes = set()
    for node, neighbors in arcs.items():
        nodes.add(node)
        for node2 in neighbors:
            nodes.add(node2)
    get_lat = lambda v: float(info['stops'][v.stop]['stop_lat'])
    get_lon = lambda v: float(info['stops'][v.stop]['stop_lon'])
    get_route = lambda v: info['routes'][v.route]['route_short_name']
    get_trip = lambda v: v.trip
    get_seq = lambda v: v.seq
    get_time = lambda v: v.time.strftime('%H:%M')
    get_name = lambda v: info['stops'][v.stop]['stop_name']
    get_all = lambda v: dict(lat=get_lat(v),
                             long=get_lon(v),
                             time=get_time(v),
                             route=get_route(v),
                             name=get_name(v),
                             trip=get_trip(v),
                             seq=get_seq(v))
    return pt.TupList(nodes).to_dict(None).vapply(get_all).to_df(orient='index').reset_index(drop=True)


def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)

    All args must be of equal length.

    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km

if __name__ == '__main__':

    tables = get_tables()
    routes_r = tables['routes'][['route_id', 'route_short_name']]
    trip_r = tables['trips'][['route_id', 'trip_id']].merge(routes_r, on='route_id')

    min_hour = '08:00:00'
    max_hour = '09:00:00'
    max_hops = 1
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
    candidates = table_to_candidates(stoptimes_L1[:5], info=info)
    current = candidates[0]
    arcs = graph_from_node(current, max_hour=max_hour, max_hops=max_hops)
    table = get_lats_longs(arcs, info)

    # route: ruta (linea de bus)
    # trip: viaje concreto dentro de una ruta
    # service: ligado a un calendario.

