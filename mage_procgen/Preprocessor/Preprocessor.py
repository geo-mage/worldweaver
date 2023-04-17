import geopandas as g
from mage_procgen.Utils.Utils import RenderingData, GeoData
from mage_procgen.Utils.Geometry import polygonise
from shapely.geometry import MultiPolygon


# Maybe this souldn't have like 10 subtypes, but it should take raw data and conf as input, and output a set of sorted, cleaned up and tagged data
# So it has to hold literally everything, and cross-check if plot x touches object y to caracterise it.


class Preprocessor:
    _window_threshold = 1e-2
    _minimal_size = 20
    _building_inter_threshold = 1

    def __init__(self, geo_data, geowindow, crs):
        self.geo_data = geo_data
        self.window = geowindow.dataframe  # .to_crs(crs)
        self.crs = crs

    def process(self):
        # First pass: selection
        print("Selecting regions")

        new_plots = self.geo_data.plots
        new_buildings = self.geo_data.buildings
        new_forests = self.geo_data.forests
        new_roads = self.geo_data.roads
        new_water = self.geo_data.water

        # TODO: find if needed. would prob be useful to split this function
        # new_geo_data = GeoData(new_plots, new_buildings, new_forests)
        print("Selection done")

        # Second pass: processing
        print("Processing")
        # TODO: need to take into account polygons with holes. 2 possibilities:
        #   - Holes are faces, we extrude them and bool with the base face
        #   - We find the closest segment between the hole and the hull, and we use it to insert the hole here
        #   like in https://blender.stackexchange.com/a/33325
        #   => tried a first version with the "closest segment" approach.
        #   Need to be vigilant to artifacts that might appear in certain cases (holes added in the "wrong" order)

        # TODO For now just pass the lists of geom, tagging will be handled later

        # Transform the Polylines into polygons to allow geometry operations with other dataframes
        new_roads["geometry"] = [
            polygonise(x[0], x[1])
            for x in new_roads[["geometry", "LARGEUR"]].to_numpy().tolist()
        ]

        # Removing roads from plots
        new_plots = new_plots.overlay(new_roads, how="difference", keep_geom_type=True)
        # Removing water from plots
        new_plots = new_plots.overlay(new_water, how="difference", keep_geom_type=True)

        # TODO: check this. otherwise, just remove roads from forests
        # Forests should be restricted to plots
        new_forests = new_forests.overlay(
            new_plots, how="intersection", keep_geom_type=True
        )

        # Forests can intersect buildings, which we don't want
        cleaned_forests = new_forests.overlay(
            new_buildings, how="difference", keep_geom_type=True
        )

        # Plots can either be forests, gardens or fields. We need to eliminate the forests, and distinguish between gardens and fields
        # TODO: add road distinction. add case for "field inside residential", which should be more or less a garden
        non_forest_plots = new_plots.overlay(
            new_forests, how="difference", keep_geom_type=True
        )
        plot_building_inters = new_plots.overlay(
            new_buildings, how="intersection", keep_geom_type=True
        )

        # Removing rounding errors (builinds that sometimes very slightly clip inside a plot
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

        fences = plots_with_building

        # Allowing roads inside fields for the time being (too many false positives)
        # fields_tmp = non_forest_plots.query(
        #    "IDU not in @plots_with_building.IDU.values"
        # )
        #
        # road_plots = new_roads.overlay(fields_tmp, how="intersection")
        # fields = fields_tmp.query("IDU not in @road_plots.IDU.values")
        fields_tmp = non_forest_plots.query(
            "IDU not in @plots_with_building.IDU.values"
        )
        fields = fields_tmp.overlay(new_roads, how="difference", keep_geom_type=True)

        forests_geom = Preprocessor.extract_geom(cleaned_forests.geometry)
        fields_geom = Preprocessor.extract_geom(fields.geometry)
        gardens_geom = Preprocessor.extract_geom(gardens.geometry)
        fences_geom = Preprocessor.extract_geom(fences.geometry)
        buildings_geom = Preprocessor.extract_geom(new_buildings.geometry)
        roads_geom = Preprocessor.extract_geom(new_roads.geometry)
        water_geom = Preprocessor.extract_geom(new_water.geometry)

        rendering_data = RenderingData(
            fields_geom,
            forests_geom,
            gardens_geom,
            fences_geom,
            buildings_geom,
            roads_geom,
            water_geom,
        )

        return rendering_data

    @staticmethod
    def extract_geom(geometry_list):
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
    def extract_line_geom(geometry_list):
        return [x for x in geometry_list]
