import geopandas as g
from mage_procgen.Utils.Utils import (
    RenderingData,
    TaggingData,
    GeoData,
    GeoWindow,
    PolygonList,
)
from mage_procgen.Utils.Geometry import polygonise
from shapely.geometry import MultiPolygon, Polygon, mapping


class Preprocessor:
    _window_threshold = 1e-2
    _minimal_size = 20
    _building_inter_threshold = 1

    def __init__(self, geo_data: g.GeoDataFrame, geowindow: GeoWindow, crs: int):
        self.geo_data = geo_data
        self.window = geowindow.dataframe
        self.crs = crs

    def process(self, remove_landlocked: bool) -> RenderingData:

        print("Processing")

        # Background should be the whole area minus every other object
        background = self.window.copy()
        background = background.overlay(
            self.geo_data.plots, how="difference", keep_geom_type=True
        )
        background = background.overlay(
            self.geo_data.buildings, how="difference", keep_geom_type=True
        )
        background = background.overlay(
            self.geo_data.water, how="difference", keep_geom_type=True
        )

        new_plots = self.geo_data.plots.overlay(
            self.window, how="intersection", keep_geom_type=True
        )
        new_buildings = self.geo_data.buildings.overlay(
            self.window, how="intersection", keep_geom_type=True
        )
        new_forests = self.geo_data.forests.overlay(
            self.window, how="intersection", keep_geom_type=True
        )
        new_water = self.geo_data.water.overlay(
            self.window, how="intersection", keep_geom_type=True
        )
        # Windowing the roads before polygonising them leads to errors
        # Related thread: https://github.com/geopandas/geopandas/issues/1724
        new_roads = self.geo_data.roads

        # TODO For now just pass the lists of geom, tagging will be handled later

        # Transform the Polylines into polygons to allow geometry operations with other dataframes
        new_roads["geometry"] = [
            polygonise(x[0], x[1])
            for x in new_roads[["geometry", "LARGEUR"]].to_numpy().tolist()
        ]

        # Now that roads are polygons, we can apply the window on them and remove them from the background
        new_roads = new_roads.overlay(
            self.window, how="intersection", keep_geom_type=True
        )
        background = background.overlay(
            new_roads, how="difference", keep_geom_type=True
        )

        if remove_landlocked:
            # Removing plots that are contained inside other plots
            new_plots = Preprocessor.remove_landlocked_plots(new_plots)

        new_plots = new_plots.overlay(new_roads, how="difference", keep_geom_type=True)

        # TODO: check this. otherwise, just remove roads from forests
        # Forests should be restricted to plots
        new_forests = new_forests.overlay(
            new_plots, how="intersection", keep_geom_type=True
        )

        # Forests can intersect buildings, which we don't want
        cleaned_forests = new_forests.overlay(
            new_buildings, how="difference", keep_geom_type=True
        )

        # Removing water from forests
        cleaned_forests = cleaned_forests.overlay(
            new_water, how="difference", keep_geom_type=True
        )

        # Plots can either be forests, gardens or fields. We need to eliminate the forests, and distinguish between gardens and fields
        # TODO: add road distinction. add case for "field inside residential", which should be more or less a garden
        non_forest_plots = new_plots.overlay(
            new_forests, how="difference", keep_geom_type=True
        )
        plot_building_inters = new_plots.overlay(
            new_buildings, how="intersection", keep_geom_type=True
        )

        # Removing rounding errors (buildings that sometimes very slightly clip inside a plot
        plot_building_inters_area = plot_building_inters.assign(
            inter_area=lambda x: x.geometry.area
        )
        plot_building_inters_area_selected = plot_building_inters_area.query(
            "inter_area > @self._building_inter_threshold"
        )
        plots_with_building = new_plots.query(
            "IDU in @plot_building_inters_area_selected.IDU.values"
        )

        # From the plots that contains buildings, need to remove the geometry of forests and buildings
        gardens_w_builings = plots_with_building.overlay(
            cleaned_forests, how="difference", keep_geom_type=True
        )
        gardens = gardens_w_builings.overlay(
            new_buildings, how="difference", keep_geom_type=True
        )

        # Removing water from gardens
        gardens = gardens.overlay(new_water, how="difference", keep_geom_type=True)

        fences = plots_with_building

        fields_tmp = non_forest_plots.query(
            "IDU not in @plots_with_building.IDU.values"
        )
        fields = fields_tmp.overlay(new_roads, how="difference", keep_geom_type=True)

        # Removing water from fields
        fields = fields.overlay(new_water, how="difference", keep_geom_type=True)

        forests_geom = Preprocessor.extract_geom(cleaned_forests.geometry)
        fields_geom = Preprocessor.extract_geom(fields.geometry)
        gardens_geom = Preprocessor.extract_geom(gardens.geometry)
        fences_geom = Preprocessor.extract_geom(fences.geometry)
        buildings_geom = Preprocessor.extract_geom(new_buildings.geometry)
        roads_geom = Preprocessor.extract_geom(new_roads.geometry)
        water_geom = Preprocessor.extract_geom(new_water.geometry)
        background_geom = Preprocessor.extract_geom(background.geometry)

        rendering_data = RenderingData(
            fields_geom,
            forests_geom,
            gardens_geom,
            fences_geom,
            buildings_geom,
            roads_geom,
            water_geom,
            background_geom,
        )

        background_tagging = background.overlay(
            gardens, how="union", keep_geom_type=True
        )
        background_tagging = background_tagging.overlay(
            fields, how="union", keep_geom_type=True
        )
        background_tagging = background_tagging.overlay(
            cleaned_forests, how="union", keep_geom_type=True
        )
        background_tagging_geom = Preprocessor.extract_geom(background_tagging.geometry)

        tagging_data = TaggingData(
            background_tagging_geom, buildings_geom, roads_geom, water_geom
        )

        return rendering_data, tagging_data

    @staticmethod
    def extract_geom(geometry_list: g.GeoSeries) -> PolygonList:
        to_return = []
        for x in geometry_list:
            # If it's a multipolygon, it has multiple polygons inside of it that we need to separate for later
            if type(x) == MultiPolygon:
                for y in x.geoms:
                    to_return.append(y)
            else:
                to_return.append(x)

        return to_return

    @staticmethod
    def remove_landlocked_plots(plots: g.GeoDataFrame) -> g.GeoDataFrame:

        # First, finding plots that are contained inside another
        landlocked_plots_IDU = {}
        for plot_IDU in plots.IDU:
            plot_df = plots.query("IDU == @plot_IDU")
            plot_intersection = plot_df.overlay(
                plots, how="intersection", keep_geom_type=False
            )

            if plot_intersection.shape[0] == 2:
                # One line will be the plot itself. If there is only one other line, it means the plot is contained
                # inside another one.
                # There are edge cases near some roads that are not plots, but this is handled later.
                # TODO : maybe it could be handled here, by checking that the geometry of the intersection is closed ?
                containing_plot_IDU = None
                for IDU in plot_intersection.IDU_2:
                    if IDU is not plot_IDU:
                        containing_plot_IDU = IDU

                landlocked_plots_IDU[plot_IDU] = containing_plot_IDU

        # Then, remove the corresponding hole
        for plot_IDU, containing_plot_IDU in landlocked_plots_IDU.items():
            containing_plot = plots.query("IDU == @containing_plot_IDU")
            containing_plot_index = containing_plot.index[0]
            containing_plot_geometry = containing_plot.geometry[containing_plot_index]

            landlocked_plot = plots.query("IDU == @plot_IDU")
            landlocked_plot_index = landlocked_plot.index[0]
            landlocked_plot_geometry = landlocked_plot.geometry[landlocked_plot_index]

            # TODO: find out if there are nested landlocked plots and if there is a need to adress them specifically
            landlocked_plot_geometry_points = mapping(landlocked_plot_geometry)[
                "coordinates"
            ][0]

            # First element of mapping coordinates is the base shape, the rest are holes
            base_shape = mapping(containing_plot_geometry)["coordinates"][0]
            holes = [x for x in mapping(containing_plot_geometry)["coordinates"]][1:]

            hole_index = 0
            hole_found = False
            for hole in holes:
                # TODO: This test is not failproof, but sometimes geometries can be rotated and this set test works for that.
                # Find out if it needs to be improved.
                if set(hole) == set(landlocked_plot_geometry_points):
                    hole_found = True
                    break
                hole_index += 1

            if hole_found:
                # This if condition is here to ensure that we don't fall into the edge case where a plot only has 1 neighbor
                # but is not contained inside it.
                del holes[hole_index]
                plots.geometry[containing_plot_index] = Polygon(base_shape, holes=holes)
                plots = plots.drop(landlocked_plot_index)

        return plots
