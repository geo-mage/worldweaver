from bpy import data as D

from mathutils import *

import numpy as np

import os


class TaggingRasterProcessor:
    @staticmethod
    def compute(
        base_path, file_name, lower_left, upper_right, resolution, tagging_order
    ):

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
            TaggingRasterProcessor.__tag, excluded={1, 2, 3}, signature="(3)->(6)"
        )

        tagged = tagging_function(ray_direction, max_distance, origin, tagging_order)

        full_path = os.path.join(base_path, file_name + ".npy")

        np.save(full_path, tagged)

    @staticmethod
    def __tag(ray_direction, max_distance, origin, tagging_order):

        tag_result = np.full(6, -9999)

        render_collection = D.collections["Rendering"].objects
        terrain_collection = D.collections["Terrain"].objects

        for layer in render_collection:
            ray_result = layer.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]
                tag_result[tagging_order.index(layer.name)] = elevation

        for layer in terrain_collection:
            ray_result = layer.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]
                tag_result[tagging_order.index("Terrain")] = elevation

        return tag_result
