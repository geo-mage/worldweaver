import geopandas as g
import pandas as p
import math
from shapely.geometry import Polygon, mapping

from dataclasses import dataclass

Point = tuple[float, float, float]
PolygonList = list[Polygon]

CRS_degrees = 4326
CRS_fr = 2154


class GeoWindow:
    def __init__(
        self,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        from_crs: int,
        to_crs: int,
    ):
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
        # Used to geometrically center all the objects in render
        self.center = (centroid.coords[0][0], centroid.coords[0][1], 0.0)

        centroid_deg = self.dataframe.to_crs(CRS_degrees).geometry[0].centroid
        # Used to configure the sun object in render
        self.center_deg = (centroid_deg.coords[0][0], centroid_deg.coords[0][1], 0.0)

        # Order is Xmin, Ymin, Xmax, Ymax
        self.bounds = self.dataframe.geometry[0].bounds


@dataclass
class RenderingData:
    fields: PolygonList
    forests: PolygonList
    gardens: PolygonList
    fences: PolygonList
    buildings: PolygonList
    roads: PolygonList
    water: PolygonList
    background: PolygonList


@dataclass
class TaggingData:
    tagging_background: PolygonList
    buildings: PolygonList
    roads: PolygonList
    water: PolygonList


@dataclass
class TerrainData:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    resolution: float
    nbcol: int
    nbrow: int
    no_data: float
    data: p.DataFrame


TerrainDataList = list[TerrainData]


@dataclass
class GeoData:
    plots: g.GeoDataFrame
    buildings: g.GeoDataFrame
    forests: g.GeoDataFrame
    # residentials: g.GeoDataFrame
    roads: g.GeoDataFrame
    water: g.GeoDataFrame
    terrain: TerrainDataList
