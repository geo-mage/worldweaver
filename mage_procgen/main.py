# Need to import dependencies of packages, and this folder is not in blender's pythonpath
import sys

sys.path.append("/usr/lib/python3/dist-packages/")

from mage_procgen.Renderer import (
    BuildingRenderer,
    ForestRenderer,
    PlotRenderer,
    RoadRenderer,
    WaterRenderer,
    BackgroundRenderer,
    TerrainRenderer,
    FloodRenderer,
)
from mage_procgen.Utils.Utils import GeoWindow, CRS_fr, CRS_degrees
from mage_procgen.Loader.Loader import Loader
from mage_procgen.Loader.ConfigLoader import ConfigLoader
from mage_procgen.Processor.Preprocessor import Preprocessor
from mage_procgen.Processor.FloodProcessor import FloodProcessor
from mage_procgen.Utils.Rendering import (
    configure_render,
    export_rendered_img,
    setup_img,
)


def main():

    config = ConfigLoader.load("/home/verstraa/Work/maps/config.json")

    geo_window = GeoWindow(
        config.x_min,
        config.x_max,
        config.y_min,
        config.y_max,
        config.crs_from,
        config.crs_to)

    # 77
    # Fublaines
    geo_window = GeoWindow(2.9185, 2.9314, 48.9396, 48.9466, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(2.93, 2.945, 48.9350, 48.94, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(2.9, 2.955, 48.93, 48.945, CRS_degrees, CRS_fr)

    # Choisy-en-Brie
    # geo_window = GeoWindow(3.2050, 3.2350, 48.7545, 48.7650, CRS_degrees, CRS_fr)

    # Meaux
    # TODO: ne marche pas a cause de pb sur les opérations d'overlay sur les geodf
    # geo_window = GeoWindow(2.8733, 2.9249, 48.9459, 48.9633, CRS_degrees, CRS_fr)

    # geo_window = GeoWindow(2.8675, 2.8893, 48.9469, 48.9612, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(2.8977, 2.9083, 48.9459, 48.9501, CRS_degrees, CRS_fr)

    # La Ferté-sous-Jouarre
    # TODO: ne marchent pas a cause de pb sur les opérations d'overlay sur les geodf
    # geo_window = GeoWindow(3.1, 3.16, 48.93, 48.97, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(3.11, 3.15, 48.933, 48.964, CRS_degrees, CRS_fr)

    # 42 38 69
    # La Chapelle-Villars
    # geo_window = GeoWindow(4.6900, 4.7340, 45.4765, 45.4550, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(4.6900, 4.74, 45.4600, 45.493, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(4.6900, 4.8000, 45.4400, 45.5000, CRS_degrees, CRS_fr)

    geo_center = geo_window.center

    geo_data = Loader.load(geo_window)

    print("Files loaded")

    print("Starting preprocessing")
    processor = Preprocessor(geo_data, geo_window, CRS_fr)
    rendering_data = processor.process(config.remove_landlocked_plots)
    print("Preprocessing done")

    print("Starting rendering")
    configure_render(geo_window.center_deg)

    if config.render_objects:
        fields_renderer = PlotRenderer.FieldRenderer(geo_data.terrain)
        fields_renderer.render(rendering_data.fields, geo_center)
        print("Fields rendered")

        gardens_renderer = PlotRenderer.GardenRenderer(geo_data.terrain)
        gardens_renderer.render(rendering_data.gardens, geo_center)
        print("Gardens rendered")

        fences_renderer = PlotRenderer.FenceRenderer(geo_data.terrain)
        fences_renderer.render(rendering_data.fences, geo_center)
        print("Fences rendered")

        forest_renderer = ForestRenderer.ForestRenderer(geo_data.terrain)
        forest_renderer.render(rendering_data.forests, geo_center)
        print("Forests rendered")

        building_renderer = BuildingRenderer.BuildingRenderer(geo_data.terrain)
        building_renderer.render(rendering_data.buildings, geo_center)
        print("Buildings rendered")

        road_renderer = RoadRenderer.RoadRenderer(geo_data.terrain)
        road_renderer.render(rendering_data.roads, geo_center)
        print("Roads rendered")

        water_renderer = WaterRenderer.WaterRenderer(geo_data.terrain)
        water_renderer.render(rendering_data.water, geo_center)
        print("Water rendered")

        background_renderer = BackgroundRenderer.BackgroundRenderer(geo_data.terrain)
        background_renderer.render(rendering_data.background, geo_center)
        print("Background rendered")

    if config.render_terrain:
        terrain_renderer = TerrainRenderer.TerrainRenderer(config.terrain_resolution, 1)
        terrain_renderer.render(geo_data.terrain, geo_window, config.use_sat_img)
        print("Terrain rendered")

    if config.flood:
        flood_data = FloodProcessor.flood(geo_window, config.flood_height, config.flood_cell_size)
        flood_render = FloodRenderer.FloodRenderer()
        flood_render.render(flood_data)

    if config.export_img:
        setup_img(config.out_img_resolution, config.out_img_pixel_size, (250, 250, 0))
        export_rendered_img()


if __name__ == "__main__":
    main()
