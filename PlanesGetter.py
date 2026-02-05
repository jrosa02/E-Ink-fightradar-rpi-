from collections import namedtuple
from pyopensky.rest import REST
import pandas as pd

BBox = namedtuple("BBox", ["min_lon", "min_lat", "max_lon", "max_lat"])

class PlanesGetter():
    def __init__(self) -> None:
        self.osky_rest = REST()

    def get_all_planes(self):
        all = self.osky_rest.states()
        df_all = pd.DataFrame(all)
        return df_all
    
    def filter_by_geo(self, df_all, bbox:BBox):
        min_lon, min_lat, max_lon, max_lat = bbox
    
        return df_all[
            (df_all["longitude"] >= min_lon) &
            (df_all["longitude"] <= max_lon) &
            (df_all["latitude"]  >= min_lat) &
            (df_all["latitude"]  <= max_lat)
        ]
    
