import TisseoR.analize_tisseo as anali
import unittest

def test_create_no_stop():
    lat = 43.5956501
    lon = 1.483844
    min_hour = "08:00:00"
    max_hour = "09:00:00"
    max_dist_km_walk = 0.3
    tables = anali.get_tables()
    info = anali.get_info_object(tables, min_hour=min_hour, max_hour=max_hour)
    node = anali.create_no_stop_node(lat=lat, lon=lon, min_hour=min_hour, max_dist_km_walk=max_dist_km_walk, info=info)
    neighbors = node.get_neighbors_in_stop()
    no_neighbors = node.get_neighbors_in_trip()
    assert len(neighbors) == 8
    assert len(no_neighbors) == 0

if __name__ == '__main__':
    test_create_no_stop()