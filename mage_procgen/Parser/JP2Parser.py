import os

import numpy as np
import rasterio
from rasterio.windows import Window

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Parser.ShapeFileParser import ShapeFileParser


# TODO: Maybe this should'nt be called Parser since it does more than that ?
class JP2Parser:
    @staticmethod
    def create_texture_img(
        file_folder: str,
        geo_window: GeoWindow,
        slab_file: str,
        texture_file_path: str,
    ):
        bbox = geo_window.bounds
        slabs = ShapeFileParser.load(slab_file, bbox)
        slab_parts = slabs.overlay(
            geo_window.dataframe, how="intersection", keep_geom_type=True
        )

        img_parts = {}
        img_bounds = {}

        for index, row in slab_parts.iterrows():
            file_name = os.path.basename(row["NOM"])

            row_bounds = row["geometry"].bounds
            img_bounds[index] = row_bounds

            with rasterio.open(os.path.join(file_folder, file_name)) as src:
                invert_transform = src.profile["transform"].__invert__()

            upper_left = (row_bounds[0], row_bounds[3])
            lower_right = (row_bounds[2], row_bounds[1])

            # Pixel position of the corners
            p_upper_left = invert_transform * upper_left
            p_lower_right = invert_transform * lower_right

            window_width = p_lower_right[0] - p_upper_left[0]
            window_height = p_lower_right[1] - p_upper_left[1]

            img_window = Window(
                p_upper_left[0], p_upper_left[1], window_width, window_height
            )

            # Need to use a 2nd "with" because read fails if it's not done right after the "open"
            with rasterio.open(os.path.join(file_folder, file_name)) as src:
                # TODO: evaluate downsampling: https://rasterio.readthedocs.io/en/stable/topics/resampling.html
                img_data = src.read((1, 2, 3), window=img_window)

            # Moving from channel first to channel last
            img_data = np.moveaxis(img_data, 0, -1)

            img_parts[index] = img_data

        img_full = None

        match len(img_parts):
            case 0:
                raise ValueError("Error during slab stitching: cannot have 0 slabs")
            case 3:
                # Should not ever get into a position where you have 3 slabs,
                # because RGE of a region is strictly contained inside the BDORTHO
                raise ValueError("Error during slab stitching: cannot have 3 slabs")
            case 1:
                # Nothing special to do
                img_full = img_parts[0]
            case 2:
                if img_bounds[0][0] == img_bounds[1][0]:
                    # If the xmin are the same, meaning if one image is on top of the other

                    if img_bounds[0][1] < img_bounds[1][1]:
                        top_part = img_parts[1]
                        bottom_part = img_parts[0]
                    else:
                        top_part = img_parts[0]
                        bottom_part = img_parts[1]

                    img_full = np.concatenate((top_part, bottom_part), axis=0)
                else:
                    # In the other case, one is on the left of the other
                    if img_bounds[0][0] < img_bounds[1][0]:
                        left_part = img_parts[0]
                        right_part = img_parts[1]
                    else:
                        left_part = img_parts[1]
                        right_part = img_parts[0]
                    img_full = np.concatenate((left_part, right_part), axis=1)
            case 4:
                # Image is split in 4 parts
                bottom_left = None
                bottom_right = None
                top_left = None
                top_right = None
                for i in range(4):
                    if img_bounds[i][0] == bbox[0]:
                        # Left side
                        if img_bounds[i][1] == bbox[1]:
                            # Bottom part
                            bottom_left = img_parts[i]
                        else:
                            # Top part
                            top_left = img_parts[i]
                    else:
                        # Right side
                        if img_bounds[i][1] == bbox[1]:
                            # Bottom part
                            bottom_right = img_parts[i]
                        else:
                            # Top part
                            top_right = img_parts[i]

                if bottom_left is None:
                    raise ValueError("Bottom left not atributed")
                if top_left is None:
                    raise ValueError("top left not atributed")
                if bottom_right is None:
                    raise ValueError("Bottom right not atributed")
                if top_right is None:
                    raise ValueError("top right not atributed")

                top_part = np.concatenate((top_left, top_right), axis=1)
                bottom_part = np.concatenate((bottom_left, bottom_right), axis=1)
                img_full = np.concatenate((top_part, bottom_part), axis=0)

        # Switching back to channel first and changing type to be able to write the image
        img_full = np.rollaxis(img_full, axis=2).astype(rasterio.uint8)

        # TODO: currently YCBCR requires jpeg compression. Evaluate if there is a better way
        with rasterio.open(
            texture_file_path,
            "w",
            driver="GTiff",
            width=img_full.shape[1],
            height=img_full.shape[2],
            count=3,
            dtype=rasterio.uint8,
            compress="JPEG",
            photometric="YCBCR",
        ) as dst:
            dst.write(img_full)
