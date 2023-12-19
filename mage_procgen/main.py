# Need to import dependencies of packages, and this folder is not in blender's pythonpath
import sys

sys.path.append("/usr/lib/python3/dist-packages/")

from numpy import arange

from datetime import datetime

from mage_procgen.Utils.Utils import GeoWindow, CRS_fr, CRS_degrees
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
    setup_compositing_flood,
    switch_compositing_render,
    switch_compositing_flood,
)


def main():

    config = ConfigLoader.load("/home/verstraa/Work/maps/config.json")

    geo_window: GeoWindow = GeoWindow.from_square(
        config.geo_window.x_min,
        config.geo_window.x_max,
        config.geo_window.y_min,
        config.geo_window.y_max,
        config.geo_window.crs_from,
        config.geo_window.crs_to,
    )

    # 77
    # Fublaines
    # geo_window = GeoWindow.from_square(2.9185, 2.9314, 48.9396, 48.9466, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.93, 2.945, 48.9350, 48.94, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.9, 2.955, 48.93, 48.945, CRS_degrees, CRS_fr)

    # Choisy-en-Brie
    # geo_window = GeoWindow.from_square(3.2050, 3.2350, 48.7545, 48.7650, CRS_degrees, CRS_fr)

    # Meaux
    # geo_window = GeoWindow.from_square(2.8733, 2.9249, 48.9459, 48.9633, CRS_degrees, CRS_fr)

    # geo_window = GeoWindow.from_square(2.8675, 2.8893, 48.9469, 48.9612, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.8977, 2.9083, 48.9459, 48.9501, CRS_degrees, CRS_fr)

    # La Ferté-sous-Jouarre
    # geo_window = GeoWindow.from_square(3.1, 3.16, 48.93, 48.97, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(3.11, 3.15, 48.933, 48.964, CRS_degrees, CRS_fr)

    # 42 38 69
    # La Chapelle-Villars
    # geo_window = GeoWindow.from_square(4.6900, 4.7340, 45.4765, 45.4550, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(4.6900, 4.74, 45.4600, 45.493, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(4.6900, 4.8000, 45.4400, 45.5000, CRS_degrees, CRS_fr)

    # 06
    # Nice shore
    # geo_window = GeoWindow.from_square(7.285, 7.30800, 43.68439, 43.69156, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(7.293, 7.30800, 43.68439, 43.69156, CRS_degrees, CRS_fr)
    # Nice inland
    # geo_window = GeoWindow.from_square(7.245, 7.27800, 43.698, 43.716, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(7.26, 7.275, 43.698, 43.7050, CRS_degrees, CRS_fr)
    # Saint Sauveur sur Tinée
    # geo_window = GeoWindow.from_square(7.097, 7.11500, 44.077, 44.09, CRS_degrees, CRS_fr)
    geo_window = GeoWindow.from_square(7.1, 7.11, 44.077, 44.09, CRS_degrees, CRS_fr)

    # 62
    # Loos-en-gohelle
    # geo_window = GeoWindow.from_square(2.7735, 2.8117, 50.4409, 50.4659, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.7817, 2.8092, 50.4511, 50.4659, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.769, 2.7892, 50.44, 50.4518, CRS_degrees, CRS_fr)
    # geo_window = GeoWindow.from_square(2.7789, 2.7874, 50.4428, 50.4483, CRS_degrees, CRS_fr)

    geo_data = Loader.load(geo_window)

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
        setup_compositing_flood()
        flood_threshold = 1000
        flood_data = FloodProcessor.flood(
            geo_window,
            config.flood_height,
            flood_threshold,
            config.flood_cell_size,
        )

        render_manager.draw_flood(flood_data)

        if not config.export_img:

            setup_img_persp(
                config.out_img_resolution,
                config.out_img_pixel_size,
                (0, 0, 0),
            )

            render_manager.beautify_zone(False)

        if config.export_img:

            switch_compositing_render()

            first_dpt_code = geo_data.departements["INSEE_DEP"][0]

            base_export_path = setup_export_folder(first_dpt_code)

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

                        setup_img_persp(
                            config.out_img_resolution,
                            config.out_img_pixel_size,
                            (camera_x, camera_y, 0),
                        )

                        # Beautify
                        zone_window = render_manager.beautify_zone(True)

                        export_rendered_img(base_export_path, now_str)

                        TaggingRasterProcessor.compute(
                            base_export_path,
                            now_str,
                            config.out_img_resolution,
                            config.tag_result_order,
                            zone_window,
                            geo_window.center,
                        )

                        # Clean
                        render_manager.clean_zone()

                    except Exception as error:
                        print("Could not generate an image: ", error)


if __name__ == "__main__":
    main()
