import geopandas as g
from mage_procgen.Utils.Utils import RenderingData, GeoWindow, CRS_fr
from mage_procgen.Utils.Geometry import polygonise
from shapely.geometry import MultiPolygon, Polygon, mapping
from functools import reduce
from mage_procgen.Utils.Config import Config
from mage_procgen.Loader.Loader import Loader


class Preprocessor:
    _window_threshold = 1e-2
    _minimal_size = 20
    _building_inter_threshold = 1

    def __init__(
        self, geo_data: g.GeoDataFrame, geowindow: GeoWindow, config: Config, crs: int
    ):
        self.geo_data = geo_data
        self.window = geowindow
        self.crs = crs
        self.config = config

    def process(self) -> RenderingData:

        print("Processing")
        if self.config.restrict_to_town:
            town = Loader.load_town_shape(
                self.window, self.config.town_dpt, self.config.town_name
            )
            town.overlay(self.window.dataframe, how="intersection", keep_geom_type=True)
            self.window = GeoWindow(town.geometry[0], CRS_fr, self.crs)

        new_buildings = self.geo_data.buildings.overlay(
            self.window.dataframe, how="intersection", keep_geom_type=True
        )
        new_forests = self.geo_data.forests.overlay(
            self.window.dataframe, how="intersection", keep_geom_type=True
        )
        new_water = self.geo_data.water.overlay(
            self.window.dataframe, how="intersection", keep_geom_type=True
        )

        new_oceans = None

        if self.geo_data.ocean is not None:
            new_oceans = self.geo_data.ocean.overlay(
                self.window.dataframe, how="intersection", keep_geom_type=True
            )
            if not new_oceans.empty:
                new_oceans = new_oceans.overlay(
                    self.geo_data.departements, how="difference", keep_geom_type=True
                )

        # Windowing the roads before polygonising them leads to errors
        # Related thread: https://github.com/geopandas/geopandas/issues/1724
        new_roads = self.geo_data.roads

        # TODO For now just pass the lists of geom, tagging will be handled later

        non_car_natures = ["Chemin", "Escalier", "Sentier"]
        roads_with_cars = new_roads.query("NATURE not in @non_car_natures")
        # Transform the Polylines into polygons to allow geometry operations with other dataframes
        roads_elements = [
            polygonise(x[0], x[1], x[2], x[3])
            for x in roads_with_cars[["geometry", "LARGEUR", "NB_VOIES", "SENS"]]
            .to_numpy()
            .tolist()
        ]
        roads_with_cars["geometry"] = [x[0] for x in roads_elements]
        roads_lanes = reduce(lambda x, y: x + y, [x[1] for x in roads_elements])

        # Now that roads are polygons, we can apply the window on them and remove them from the background
        roads_with_cars = roads_with_cars.overlay(
            self.window.dataframe, how="intersection", keep_geom_type=True
        )

        # Removing roads from forests so we don't have trees on the road
        new_forests = new_forests.overlay(
            roads_with_cars, how="difference", keep_geom_type=True
        )

        # Forests can intersect buildings, which we don't want
        cleaned_forests = new_forests.overlay(
            new_buildings, how="difference", keep_geom_type=True
        )

        # Removing water from forests
        cleaned_forests = cleaned_forests.overlay(
            new_water, how="difference", keep_geom_type=True
        )

        # Splitting water between "still" and "flowing"
        # TODO: check this tag list/update it
        flowing_water_tags = ["Ecoulement naturel", "Ecoulement canalisé", "Canal"]
        flowing_water = new_water.query("NATURE in @flowing_water_tags")
        still_water = new_water.query("NATURE not in @flowing_water_tags")

        churches_tags = ["Religieux"]
        churches = new_buildings.query("USAGE1 in @churches_tags")
        non_churches = new_buildings.query("USAGE1 not in @churches_tags")
        malls_tags = ["Commercial et services"]
        malls = non_churches.query("USAGE1 in @malls_tags")
        non_malls = non_churches.query("USAGE1 not in @malls_tags")
        factories_tags = ["Industriel"]
        factories = non_malls.query("USAGE1 in @factories_tags")
        default_buildings = non_malls.query("USAGE1 not in @factories_tags")

        rendering_data = RenderingData(
            cleaned_forests,
            churches,
            malls,
            factories,
            default_buildings,
            roads_with_cars,
            roads_lanes,
            still_water,
            flowing_water,
            new_oceans,
        )

        return rendering_data
