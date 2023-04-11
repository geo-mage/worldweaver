import geopandas as g
import math
from shapely.geometry import Polygon, mapping

from dataclasses import dataclass


class GeoWindow:
    # x_min: float
    # x_max: float
    # y_min: float
    # y_max: float
    # from_crs: int
    # to_crs: int

    def __init__(self, x_min, x_max, y_min, y_max, from_crs, to_crs):
        window_s = g.GeoSeries(
            [
                Polygon(
                    [
                        (x_min, y_min),
                        (x_max, y_min),
                        (x_max, y_max),
                        (x_min, y_max),
                    ]
                )
            ]
        )
        self.dataframe = g.GeoDataFrame(
            {"geometry": window_s, "df": [1]}, crs=from_crs
        ).to_crs(to_crs)

        centroid = self.dataframe.geometry[0].centroid
        self.center = (centroid.coords[0][0], centroid.coords[0][1], 0)

        self.bounds = self.dataframe.geometry[0].bounds

    # def to_dataframe(self):
    #    window_s = g.GeoSeries(
    #        [
    #            Polygon(
    #                [
    #                    (self.x_min, self.y_min),
    #                    (self.x_max, self.y_min),
    #                    (self.x_max, self.y_max),
    #                    (self.x_min, self.y_max),
    #                ]
    #            )
    #        ]
    #    )
    #    window_df = g.GeoDataFrame(
    #        {"geometry": window_s, "df": [1]}, crs=self.from_crs
    #    ).to_crs(self.to_crs)
    #    return window_df


@dataclass
class GeoData:
    plots: g.GeoDataFrame
    buildings: g.GeoDataFrame
    forests: g.GeoDataFrame
    # residentials: g.GeoDataFrame
    roads: g.GeoDataFrame
    # water: g.GeoDataFrame


@dataclass
class RenderingData:
    fields: list
    forests: list
    gardens: list
    fences: list
    buildings: list
    roads: list


CRS_degrees = 4326
CRS_fr = 2154
