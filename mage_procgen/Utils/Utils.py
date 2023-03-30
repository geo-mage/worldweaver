import geopandas as g
from shapely.geometry import Polygon

from dataclasses import dataclass


@dataclass
class GeoWindow:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    from_crs: int
    to_crs: int

    def to_dataframe(self):
        window_s = g.GeoSeries([Polygon([(self.x_min, self.y_min),
                                         (self.x_max, self.y_min),
                                         (self.x_max, self.y_max),
                                         (self.x_min, self.y_max)])])
        window_df = g.GeoDataFrame({'geometry': window_s, 'df': [1]}, crs=self.from_crs).to_crs(self.to_crs)
        return window_df

    def center(self):
        centroid = self.to_dataframe().geometry[0].centroid
        return (centroid.coords[0][0], centroid.coords[0][1], 0)

@dataclass
class GeoData:
    plots: g.GeoDataFrame
    buildings: g.GeoDataFrame
    forests: g.GeoDataFrame
    #residentials: g.GeoDataFrame
    #roads: g.GeoDataFrame
    #water: g.GeoDataFrame


@dataclass
class RenderingData:
    fields: list
    forests: list
    gardens: list
    buildings: list

CRS_degrees = 4326
CRS_fr = 2154

