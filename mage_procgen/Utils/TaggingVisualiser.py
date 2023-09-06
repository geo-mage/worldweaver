import os

import rasterio
import re
import numpy as np

from PIL import Image
from tqdm import tqdm

from mage_procgen.Loader.ConfigLoader import ConfigLoader

hex_color_regex = re.compile("^#[0-9a-fA-F]{6}$")
hex_color_split_regex = re.compile("..")


def tagging_file_to_png(file_name, flood_height, highest_object):

    base_file_name = os.path.splitext(file_name)[0]

    config = ConfigLoader.load("/home/verstraa/Work/maps/config.json")
    tagging_colors = {
        layer_name: hex_color_to_tuple(hex_code)
        for layer_name, hex_code in config.tagging_config.items()
    }
    tagging_raster = np.load(file_name)

    if flood_height:
        # Preparing for the mapping of the flood height function.
        flood_height_function = np.vectorize(
            __flood_height, excluded={1}, signature="(7)->()"
        )

        flood_height_raster = flood_height_function(
            tagging_raster, config.tag_result_order
        ).astype(rasterio.uint8)

        flood_height_file = base_file_name + "_flood_height.png"

        img_flood = Image.fromarray(flood_height_raster)
        img_flood.save(flood_height_file)

    if highest_object:
        # Preparing for the mapping of the highest object function.
        highest_object_function = np.vectorize(
            __highest_object, excluded={1, 2}, signature="(7)->(3)"
        )

        highest_object_raster = highest_object_function(
            tagging_raster, tagging_colors, config.tag_result_order
        )

        highest_object_file = base_file_name + "_highest_object.png"

        # Switching back to channel first and changing type to be able to write the image
        img_full_2 = np.rollaxis(highest_object_raster, axis=2).astype(rasterio.uint8)

        with rasterio.open(
            highest_object_file,
            "w",
            driver="GTiff",
            width=img_full_2.shape[1],
            height=img_full_2.shape[2],
            count=3,
            dtype=rasterio.uint8,
            compress="LZW",
            photometric="RGB",
        ) as highest_object_file_handle:
            highest_object_file_handle.write(img_full_2)


def tagging_files_to_png(folder, flood_height, highest_object):
    for file in tqdm(os.listdir(folder)):
        if ".npy" in file:
            tagging_file_to_png(
                os.path.join(folder, file), flood_height, highest_object
            )


def __flood_height(tagging_info, tag_result_order):

    flood_index = tag_result_order.index("Flood")
    terrain_index = tag_result_order.index("Terrain")

    if (
        tagging_info[flood_index] != -9999
        and tagging_info[terrain_index] != -9999
        and tagging_info[flood_index] > tagging_info[terrain_index]
    ):
        return tagging_info[flood_index] - tagging_info[terrain_index]
    else:
        return 0


def __highest_object(tagging_info, tagging_colors, tag_result_order):

    # Terrain should not be taken into account for the highest
    index_of_highest = np.argmax(tagging_info[:-1])

    highest_layer_name = tag_result_order[index_of_highest]

    if highest_layer_name in tagging_colors and tagging_info[index_of_highest] > -9999:
        return np.array(tagging_colors[highest_layer_name])
    else:
        return np.array([0, 0, 0])


def hex_color_to_tuple(hex_code):
    # Checking if it's a valid hex code with RGB values
    match = hex_color_regex.match(hex_code)
    if match:
        # Extracting the 3 values R, G and B
        colors_hex = hex_color_split_regex.findall(hex_code.strip("#"))
        # Convert hex to int
        colors = [int(c, 16) for c in colors_hex]
        return (colors[0], colors[1], colors[2])
    else:
        raise ValueError("Invalid hex string: " + hex_code)
