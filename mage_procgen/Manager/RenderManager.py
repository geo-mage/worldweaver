from bpy import data as D
import math
import geopandas as g
from shapely.geometry import MultiPolygon, Polygon, mapping, LineString
from mage_procgen.Utils.Utils import PolygonList, TerrainData
from mage_procgen.Utils.Utils import RenderingData, GeoWindow
from mage_procgen.Utils.Config import Config
from mage_procgen.Utils.Rendering import (
    configure_render,
    rendering_collection_name,
    cars_collection_name,
    terrain_collection_name,
    buildings_collection_name,
)

from mage_procgen.Renderer import (
    BuildingRenderer,
    ForestRenderer,
    RoadRenderer,
    WaterRenderer,
    TerrainRenderer,
    FloodRenderer,
)


class RenderManager:
    def __init__(
        self,
        terrain_data: list[TerrainData],
        rendering_data: RenderingData,
        geowindow: GeoWindow,
        crs: int,
        config: Config,
    ):
        self.terrain_data = terrain_data
        self.rendering_data = rendering_data
        self.window = geowindow
        self.crs = crs
        self.config = config
        self.current_zone = None
        configure_render(self.window.center_deg)
        self.terrain_renderer = TerrainRenderer.TerrainRenderer(
            self.config.terrain_resolution, 1
        )
        self.building_renderer = BuildingRenderer.BuildingRenderer(
            self.terrain_data, self.config.building_render_config
        )
        self.malls_renderer = BuildingRenderer.MallRenderer(
            self.terrain_data, self.config.mall_render_config
        )
        self.churches_renderer = BuildingRenderer.ChurchRenderer(
            self.terrain_data, self.config.church_render_config
        )
        self.factories_renderer = BuildingRenderer.FactoryRenderer(
            self.terrain_data, self.config.factory_render_config
        )
        self.flowing_water_renderer = WaterRenderer.FlowingWaterRenderer(
            self.terrain_data, self.config.water_render_config
        )
        self.flood_renderer = FloodRenderer.FloodRenderer(
            self.config.flood_render_config
        )
        self.forests_renderer = ForestRenderer.ForestRenderer(
            self.terrain_data, self.config.forest_render_config
        )
        self.road_renderer = RoadRenderer.RoadRenderer(
            self.terrain_data,
            self.config.road_render_config,
            self.config.car_render_config,
        )
        self.still_water_renderer = WaterRenderer.StillWaterRenderer(
            self.terrain_data, self.config.water_render_config
        )

    def draw_flood_interactors(self):
        # Rendering objects that interact with flood
        print("Rendering objects that interact with flood")
        self.terrain_renderer.render(
            self.terrain_data,
            self.window,
            terrain_collection_name,
            self.config.use_sat_img,
        )
        print("Terrain rendered")

        flowing_water = self.__extract_geom(self.rendering_data.flowing_water.geometry)
        if (
            self.rendering_data.ocean is not None
            and not self.rendering_data.ocean.empty
        ):
            oceans_geom = self.__extract_geom(self.rendering_data.ocean.geometry)
            flowing_water.extend(oceans_geom)
        self.flowing_water_renderer.render(
            flowing_water, self.window.center, rendering_collection_name
        )
        print("Objects that interact with flood rendered")

    def draw_flood(self, flood_data):
        self.flood_renderer.render(flood_data, rendering_collection_name)

    def beautify_zone(self, restrict_to_camera):

        zone_window = self.window

        if restrict_to_camera:
            camera = D.objects["Camera"]
            origin = camera.location

            # camera Z should be by far the highest so this rule of thumb should hold
            max_distance = 2 * origin[2]

            vector_coord = math.tan(camera.data.angle / 2)

            # To draw more than the actual view
            vector_multiplier = 1.2

            vector_ul = (
                -vector_multiplier * vector_coord,
                -vector_multiplier * vector_coord,
                -1,
            )
            vector_ur = (
                vector_multiplier * vector_coord,
                -vector_multiplier * vector_coord,
                -1,
            )
            vector_ll = (
                -vector_multiplier * vector_coord,
                vector_multiplier * vector_coord,
                -1,
            )
            vector_lr = (
                vector_multiplier * vector_coord,
                vector_multiplier * vector_coord,
                -1,
            )

            zone_delimiters = (
                self.__corner_coord(vector_ul, max_distance, origin),
                self.__corner_coord(vector_ur, max_distance, origin),
                self.__corner_coord(vector_ll, max_distance, origin),
                self.__corner_coord(vector_lr, max_distance, origin),
            )

            try:
                zone_x_min = (
                    min([c[0][0] for c in zone_delimiters]) + self.window.center[0]
                )
                zone_x_max = (
                    max([c[0][0] for c in zone_delimiters]) + self.window.center[0]
                )
                zone_y_min = (
                    min([c[0][1] for c in zone_delimiters]) + self.window.center[1]
                )
                zone_y_max = (
                    max([c[0][1] for c in zone_delimiters]) + self.window.center[1]
                )

                zone_window = GeoWindow.from_square(
                    zone_x_min, zone_x_max, zone_y_min, zone_y_max, self.crs, self.crs
                )

            except:
                raise ValueError(
                    "Zone to beautify is outside of the boundaries of the scene"
                )

        buildings_zone = self.rendering_data.default_buildings.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        buildings = self.__extract_buildings_data(buildings_zone)
        self.building_renderer.render(
            buildings, self.window.center, buildings_collection_name
        )

        churches_zone = self.rendering_data.churches.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        churches = self.__extract_buildings_data(churches_zone)
        self.churches_renderer.render(
            churches, self.window.center, buildings_collection_name
        )

        factories_zone = self.rendering_data.factories.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        factories = self.__extract_buildings_data(factories_zone)
        self.factories_renderer.render(
            factories, self.window.center, buildings_collection_name
        )

        malls_zone = self.rendering_data.malls.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        malls = self.__extract_buildings_data(malls_zone)
        self.malls_renderer.render(malls, self.window.center, buildings_collection_name)

        forests_zone = self.rendering_data.forests.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        forests = self.__extract_geom(forests_zone.geometry)
        self.forests_renderer.render(
            forests, self.window.center, rendering_collection_name
        )

        road_zone = self.rendering_data.roads.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )

        road = self.__extract_geom(road_zone.geometry)
        lanes_zone = self.__window_lanes(zone_window)
        self.road_renderer.render(
            road,
            self.window.center,
            rendering_collection_name,
            lanes_zone,
            cars_collection_name,
        )

        still_water_zone = self.rendering_data.still_water.overlay(
            zone_window.dataframe, how="intersection", keep_geom_type=True
        )
        still_water = self.__extract_geom(still_water_zone.geometry)
        self.still_water_renderer.render(
            still_water, self.window.center, rendering_collection_name
        )

        return zone_window

    def clean_zone(self):
        self.forests_renderer.clear_object()

        self.road_renderer.clear_object()

        self.still_water_renderer.clear_object()

        self.building_renderer.clear_object()

        self.churches_renderer.clear_object()

        self.malls_renderer.clear_object()

        self.factories_renderer.clear_object()

    def __corner_coord(self, ray_direction, max_distance, origin):

        terrain_collection = D.collections["Terrain"].objects

        coord = None

        terrain_hit = None

        for terrain in terrain_collection:
            ray_result = terrain.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                coord = ray_result[1]
                terrain_hit = terrain.name

        return coord, terrain_hit

    def __extract_geom(self, geometry_list: g.GeoSeries) -> PolygonList:
        to_return = []
        for x in geometry_list:
            # If it's a multipolygon, it has multiple polygons inside of it that we need to separate for later
            if type(x) == MultiPolygon:
                for y in x.geoms:
                    to_return.append(y)
            else:
                to_return.append(x)

        return to_return

    def __extract_buildings_data(self, buildings: g.GeoDataFrame) -> PolygonList:
        to_return = []

        data = [
            (x[0], x[1])
            for x in buildings[["NB_ETAGES", "geometry"]].to_numpy().tolist()
        ]
        for x in data:
            # If it's a multipolygon, it has multiple polygons inside of it that we need to separate for later
            if type(x[1]) == MultiPolygon:
                for y in x[1].geoms:
                    to_return.append((x[0], y))
            else:
                to_return.append(x)

        return to_return

    def __window_lanes(self, zone_window):

        windowed_lanes = []

        for lane in self.rendering_data.lanes:

            windowed_lane = []
            for point in lane.coords:

                if (
                    zone_window.bounds[0] < point[0] < zone_window.bounds[2]
                    and zone_window.bounds[1] < point[1] < zone_window.bounds[3]
                ):
                    windowed_lane.append(point)

            if len(windowed_lane) > 1:
                windowed_lanes.append(LineString(windowed_lane))

        return windowed_lanes
