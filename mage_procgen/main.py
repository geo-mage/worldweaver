# Need to import dependencies of packages, and this folder is not in blender's pythonpath
import shutil
import sys

sys.path.append("/usr/lib/python3/dist-packages/")

import os
from numpy import arange
import fiona

from datetime import datetime

from mage_procgen.Utils.Utils import GeoWindow, CRS_fr, CRS_degrees
from mage_procgen.Utils.Config import Config
from mage_procgen.Utils.DataFiles import (
    config_folder,
    base_config_file,
    default_config_file,
    check_shapefiles_presence,
)
from mage_procgen.Loader.Loader import Loader
from mage_procgen.Loader.ConfigLoader import ConfigLoader
from mage_procgen.Processor.Preprocessor import Preprocessor
from mage_procgen.Processor.FloodProcessor import FloodProcessor
from mage_procgen.Manager.RenderManager import RenderManager
from mage_procgen.Processor.BasicFloodProcessor import BasicFloodProcessor
from mage_procgen.Processor.TaggingRasterProcessor import TaggingRasterProcessor
from mage_procgen.Utils.Rendering import (
    setup_export_folder,
    export_rendered_img,
    setup_img_persp,
    setup_img_ortho,
    setup_img_ortho_res,
    setup_compositing_render,
    set_compositing_render_image_name,
    check_is_sun_activated,
)


def main(filepath):

    # Loading config
    if len(filepath) > 0:
        print("Using config file path given by user")
        config_filepath = filepath
    else:
        print("Falling back to default conf")
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        config_filepath = os.path.realpath(
            os.path.join(_location, config_folder, default_config_file)
        )

        if not os.path.isfile(config_filepath):
            print("No config file found, copying base config")
            shutil.copyfile(
                os.path.join(_location, config_folder, base_config_file),
                config_filepath,
            )

    config = ConfigLoader.load(config_filepath)
    if ".." in config.base_folder:
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        config.base_folder = os.path.realpath(
            os.path.join(_location, config.base_folder)
        )

    # Pre-run checks
    check_is_sun_activated()

    check_shapefiles_presence(config.base_folder)

    geo_window = None

    match config.window_type:
        case "TOWN":
            town = Loader.load_town_shape(
                config.base_folder, config.town_dpt, config.town_name
            )

            geo_window = GeoWindow(town.geometry[0], CRS_fr, CRS_fr)
        case "FILE":
            file_window = fiona.open(config.window_shapefile)
            window_crs = int(file_window.crs.to_string().split(":")[1])
            file_bounds = file_window.bounds
            geo_window = GeoWindow.from_square(
                file_bounds[0],
                file_bounds[2],
                file_bounds[1],
                file_bounds[3],
                window_crs,
                CRS_fr,
            )
        case "COORDS":
            geo_window: GeoWindow = GeoWindow.from_square(
                config.geo_window.x_min,
                config.geo_window.x_max,
                config.geo_window.y_min,
                config.geo_window.y_max,
                config.geo_window.crs_from,
                CRS_fr,
            )
        case _:
            raise ValueError(
                "Invalid config: invalid window type: ", config.window_type
            )

    geo_data = Loader.load(config.base_folder, geo_window)

    print("Files loaded")

    print("Starting preprocessing")
    processor = Preprocessor(geo_data, geo_window, config, CRS_fr)
    rendering_data = processor.process()
    print("Preprocessing done")

    render_manager = RenderManager(
        geo_data.terrain, rendering_data, geo_window, CRS_fr, config
    )
    render_manager.draw_flood_interactors()

    if not config.flood:
        render_manager.beautify_zone(False)

    if config.flood:

        # First render: writing a height map
        print("Computing height map")
        FloodProcessor.generate_height_map(
            config.base_folder,
            geo_window,
            config.flood_cell_size,
        )

        render_manager.change_terrain_visibility(False)

        # Second render: getting a semantic map without terrain
        # We have to hide terrain because it's very irregular is rivers, and thus terrain often clips through river surface,
        # Making flood init worse
        print("Computing sources")
        FloodProcessor.generate_semantic_map(
            config.base_folder,
            geo_window,
            config.flood_cell_size,
        )

        render_manager.change_terrain_visibility(True)

        flood_threshold = 1000
        flood_data = FloodProcessor.flood(
            config.base_folder,
            geo_window,
            config.flood_height,
            flood_threshold,
            config.flood_cell_size,
        )

        render_manager.draw_flood(flood_data)

        if not config.export_img:
            first_dpt_code = geo_data.departements["INSEE_DEP"][0]

            base_export_path = setup_export_folder(config.base_folder, first_dpt_code)

            config_filename = os.path.basename(config_filepath)
            shutil.copyfile(
                config_filepath,
                os.path.join(base_export_path, config_filename),
            )

            setup_compositing_render(base_export_path, config)
            now = datetime.now()
            now_str = now.strftime("%Y_%m_%d:%H:%M:%S:%f")
            set_compositing_render_image_name(now_str + "_tagging")

            if not config.use_camera_ortho:
                setup_img_persp(
                    config.out_img_resolution,
                    config.out_img_pixel_size,
                    (0, 0, 0),
                )

            else:
                setup_img_ortho_res(
                    config.out_img_resolution,
                    config.out_img_pixel_size,
                    (0, 0, 0),
                )

            render_manager.beautify_zone(False)
            export_rendered_img(base_export_path, now_str)

        if config.export_img:

            first_dpt_code = geo_data.departements["INSEE_DEP"][0]

            base_export_path = setup_export_folder(config.base_folder, first_dpt_code)

            config_filename = os.path.basename(config_filepath)
            shutil.copyfile(
                config_filepath,
                os.path.join(base_export_path, config_filename),
            )

            setup_compositing_render(base_export_path, config)

            img_size = config.out_img_resolution * config.out_img_pixel_size

            camera_step = img_size * 0.9

            camera_x_min = flood_data[3][0] + img_size / 2
            camera_x_max = flood_data[4][0] - img_size / 2
            camera_y_min = flood_data[3][1] + img_size / 2
            camera_y_max = flood_data[4][1] - img_size / 2

            for camera_x in arange(camera_x_min, camera_x_max, camera_step):
                for camera_y in arange(camera_y_min, camera_y_max, camera_step):
                    try:
                        now = datetime.now()
                        now_str = now.strftime("%Y_%m_%d:%H:%M:%S:%f")

                        if not config.use_camera_ortho:
                            setup_img_persp(
                                config.out_img_resolution,
                                config.out_img_pixel_size,
                                (camera_x, camera_y, 0),
                            )
                            # Beautify
                            zone_window = render_manager.beautify_zone(True, True)
                        else:
                            setup_img_ortho_res(
                                config.out_img_resolution,
                                config.out_img_pixel_size,
                                (camera_x, camera_y, 0),
                            )
                            zone_window = render_manager.beautify_zone(True)

                        set_compositing_render_image_name(now_str + "_tagging")

                        export_rendered_img(base_export_path, now_str)

                        # TaggingRasterProcessor.compute(
                        #     base_export_path,
                        #     now_str,
                        #     config.out_img_resolution,
                        #     config.tag_result_order,
                        #     zone_window,
                        #     geo_window.center,
                        # )

                        # Clean
                        render_manager.clean_zone()

                    except Exception as error:
                        print("Could not generate an image: ", error)


if __name__ == "__main__":
    main("")
