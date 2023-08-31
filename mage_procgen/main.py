# Need to import dependencies of packages, and this folder is not in blender's pythonpath
import sys

sys.path.append("/usr/lib/python3/dist-packages/")

from numpy import arange

from datetime import datetime

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
from mage_procgen.Processor.TaggingRasterProcessor import TaggingRasterProcessor
from mage_procgen.Utils.Rendering import (
    configure_render,
    setup_export_folder,
    export_rendered_img,
    setup_img,
    rendering_collection_name,
)


def main():

    config = ConfigLoader.load("/home/verstraa/Work/maps/config.json")

    geo_window = GeoWindow(
        config.geo_window.x_min,
        config.geo_window.x_max,
        config.geo_window.y_min,
        config.geo_window.y_max,
        config.geo_window.crs_from,
        config.geo_window.crs_to,
    )

    # 77
    # Fublaines
    # geo_window = GeoWindow(2.9185, 2.9314, 48.9396, 48.9466, CRS_degrees, CRS_fr)
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

    # 06
    # Nice
    #geo_window = GeoWindow(7.285, 7.30800, 43.68439, 43.69156, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow(7.293, 7.30800, 43.68439, 43.69156, CRS_degrees, CRS_fr)
    # Saint Sauveur sur Tinée
    geo_window = GeoWindow(7.097, 7.11500, 44.077, 44.09, CRS_degrees, CRS_fr)


    geo_center = geo_window.center

    geo_data = Loader.load(geo_window)

    print("Files loaded")

    print("Starting preprocessing")
    processor = Preprocessor(geo_data, geo_window, CRS_fr)
    rendering_data = processor.process(config.remove_landlocked_plots)
    print("Preprocessing done")

    print("Starting rendering")
    configure_render(geo_window.center_deg)

    if config.render_terrain:
        terrain_renderer = TerrainRenderer.TerrainRenderer(config.terrain_resolution, 1)
        terrain_renderer.render(
            geo_data.terrain, geo_window, rendering_collection_name, config.use_sat_img
        )
        print("Terrain rendered")

    if config.render_objects:
        # fields_renderer = PlotRenderer.FieldRenderer(
        #    geo_data.terrain, config.field_render_config
        # )
        # fields_renderer.render(
        #    rendering_data.fields, geo_center, rendering_collection_name
        # )
        # print("Fields rendered")

        # gardens_renderer = PlotRenderer.GardenRenderer(
        #    geo_data.terrain, config.garden_render_config
        # )
        # gardens_renderer.render(
        #    rendering_data.gardens, geo_center, rendering_collection_name
        # )
        # print("Gardens rendered")

        fences_renderer = PlotRenderer.FenceRenderer(
            geo_data.terrain, config.fence_render_config
        )
        fences_renderer.render(
            rendering_data.fences, geo_center, rendering_collection_name
        )
        print("Fences rendered")

        forest_renderer = ForestRenderer.ForestRenderer(
            geo_data.terrain, config.forest_render_config
        )
        forest_renderer.render(
            rendering_data.forests, geo_center, rendering_collection_name
        )
        print("Forests rendered")

        building_renderer = BuildingRenderer.BuildingRenderer(
            geo_data.terrain, config.building_render_config
        )
        building_renderer.render(
            rendering_data.buildings, geo_center, rendering_collection_name
        )
        print("Buildings rendered")

        road_renderer = RoadRenderer.RoadRenderer(
            geo_data.terrain, config.road_render_config
        )
        road_renderer.render(
            rendering_data.roads, geo_center, rendering_collection_name
        )
        print("Roads rendered")

        water_renderer = WaterRenderer.WaterRenderer(
            geo_data.terrain, config.water_render_config
        )
        water_renderer.render(
            rendering_data.water, geo_center, rendering_collection_name
        )
        print("Water rendered")

        # background_renderer = BackgroundRenderer.BackgroundRenderer(
        #    geo_data.terrain, config.background_render_config
        # )
        # background_renderer.render(
        #    rendering_data.background, geo_center, rendering_collection_name
        # )
        # print("Background rendered")

    if config.flood:
        flood_data = FloodProcessor.flood(
            geo_window, config.flood_height, config.flood_cell_size
        )
        flood_renderer = FloodRenderer.FloodRenderer(config.flood_render_config)
        flood_renderer.render(flood_data, rendering_collection_name)

        if config.export_img:

            base_export_path = setup_export_folder(geo_data.departements[0])

            img_size = config.out_img_resolution * config.out_img_pixel_size

            camera_step = img_size * 0.9

            camera_x_min = flood_data[2][0] + img_size / 2
            camera_x_max = flood_data[3][0] - img_size / 2
            camera_y_min = flood_data[2][1] + img_size / 2
            camera_y_max = flood_data[3][1] - img_size / 2

            # tagging_colors = {
            #    layer_name: hex_color_to_tuple(hex_code)
            #    for layer_name, hex_code in config.tagging_config.items()
            # }

            for camera_x in arange(camera_x_min, camera_x_max, camera_step):
                for camera_y in arange(camera_y_min, camera_y_max, camera_step):
                    now = datetime.now()
                    now_str = now.strftime("%Y_%m_%d:%H:%M:%S:%f")

                    setup_img(
                        config.out_img_resolution,
                        config.out_img_pixel_size,
                        (camera_x, camera_y, 0),
                    )

                    export_rendered_img(base_export_path, now_str)

                    lower_left = (camera_x - img_size / 2, camera_y - img_size / 2)
                    upper_right = (camera_x + img_size / 2, camera_y + img_size / 2)

                    TaggingRasterProcessor.compute(
                        base_export_path,
                        now_str,
                        lower_left,
                        upper_right,
                        config.out_img_pixel_size,
                        config.tag_result_order,
                    )


if __name__ == "__main__":
    main()
