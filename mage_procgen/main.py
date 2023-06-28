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
from mage_procgen.Processor.Preprocessor import Preprocessor
from mage_procgen.Processor.FloodProcessor import FloodProcessor


from mage_procgen.Utils.Rendering import configure_render


def main():

    # Fublaines
    geo_window = GeoWindow(2.9185, 2.9314, 48.9396, 48.9466, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(2.93, 2.945, 48.9350, 48.94, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(2.9, 2.955, 48.93, 48.945, CRS_degrees, CRS_fr)

    # La Chapelle-Villars
    # geo_window = GeoWindow(4.6900, 4.7340, 45.4765, 45.4550, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(4.6900, 4.74, 45.4600, 45.493, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(4.6900, 4.8000, 45.4400, 45.5000, CRS_degrees, CRS_fr)

    render_objects = True

    render_terrain = True
    terrain_resolution = 1

    use_sat_img = True

    flood = True
    flood_height = 5

    geo_center = geo_window.center

    bbox = geo_window.bounds

    geo_data = Loader.load(geo_window)

    print("Files loaded")

    print("Starting preprocessing")
    processor = Preprocessor(geo_data, geo_window, CRS_fr)
    rendering_data = processor.process()
    print("Preprocessing done")

    print("Starting rendering")
    configure_render()

    if render_objects:
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

    if render_terrain:
        terrain_renderer = TerrainRenderer.TerrainRenderer(terrain_resolution, 1)
        terrain_renderer.render(geo_data.terrain, geo_window, use_sat_img)
        print("Terrain rendered")

    if flood:
        # for i in range(7):
        #    FloodProcessor.flood(geo_window, i)
        flood_data = FloodProcessor.flood(geo_window, flood_height)
        flood_render = FloodRenderer.FloodRenderer()
        flood_render.render(flood_data)


if __name__ == "__main__":
    main()
