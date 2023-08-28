import math

from bpy import data as D

from mathutils import *

import numpy as np

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from math import floor, ceil

from datetime import datetime
import os
import rasterio


class TaggingRasterProcessor:
    @staticmethod
    def compute(base_path, lower_left, upper_right, resolution, tagging_colors):

        camera = D.objects["Camera"]
        origin = camera.location

        # camera Z should be by far the highest so this rule of thumb should hold
        max_distance = 2 * origin[2]

        # This holds every vector that will be the direction of the rays
        ray_direction = np.array(
            [
                [
                    Vector([x - origin[0], y - origin[1], 0 - origin[2]])
                    for x in np.arange(lower_left[0], upper_right[0], resolution)
                ]
                for y in np.arange(upper_right[1], lower_left[1], -resolution)
            ]
        )

        # Preparing for the mapping of the tagging function. Signature is necessary because elevation works on a 3 dimensional vector (position) and returns another (RGB)
        tagging_function = np.vectorize(
            TaggingRasterProcessor.__tag, excluded={1, 2, 3}, signature="(3)->(3)"
        )

        tagged = tagging_function(ray_direction, max_distance, origin, tagging_colors)

        now = datetime.now()
        now_str = now.strftime("%Y_%m_%d:%H:%M:%S:%f")

        full_path = os.path.join(base_path, now_str + ".png")

        # Switching back to channel first and changing type to be able to write the image
        img_full = np.rollaxis(tagged, axis=2).astype(rasterio.uint8)

        # TODO: currently YCBCR requires jpeg compression. Evaluate if there is a better way
        with rasterio.open(
            full_path,
            "w",
            driver="GTiff",
            width=img_full.shape[1],
            height=img_full.shape[2],
            count=3,
            dtype=rasterio.uint8,
            compress="LZW",
            photometric="RGB",
        ) as dst:
            dst.write(img_full)

    @staticmethod
    def __tag(ray_direction, max_distance, origin, tagging_colors):

        collisions = {}

        render_collection = D.collections["Rendering"].objects

        for layer in render_collection:
            ray_result = layer.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]
                collisions[layer.name] = elevation

        highest_col_name = ""
        highest_col_elevation = -math.inf

        for layer_name, collision_elevation in collisions.items():
            if collision_elevation > highest_col_elevation:
                highest_col_name = layer_name
                highest_col_elevation = collision_elevation

        if highest_col_name in tagging_colors:
            return np.array(tagging_colors[highest_col_name])
        else:
            return np.array([0, 0, 0])
