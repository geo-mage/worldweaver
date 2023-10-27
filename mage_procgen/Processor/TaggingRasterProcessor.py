from bpy import data as D

from mathutils import *

import numpy as np

import os
import math


class TaggingRasterProcessor:
    @staticmethod
    def compute(base_path, file_name, resolution, tagging_order):

        camera = D.objects["Camera"]
        origin = camera.location

        # camera Z should be by far the highest so this rule of thumb should hold
        max_distance = 2 * origin[2]

        vector_coord = math.tan(camera.data.angle / 2)

        # This holds every vector that will be the direction of the rays. They recreate the vectors used for the rendering (or at least a sampling of them)
        ray_direction = np.array(
            [
                [
                    Vector(
                        [
                            ((2 * (x / (resolution - 1)) - 1) * vector_coord),
                            ((-2 * (y / (resolution - 1)) + 1) * vector_coord),
                            -1,
                        ]
                    )
                    for x in range(int(resolution))
                ]
                for y in range(int(resolution))
            ]
        )

        # Preparing for the mapping of the tagging function. Signature is necessary because elevation works on a 3 dimensional vector (position) and returns another (RGB)
        tagging_function = np.vectorize(
            TaggingRasterProcessor.__tag, excluded={1, 2, 3}, signature="(3)->(7)"
        )

        tagged = tagging_function(ray_direction, max_distance, origin, tagging_order)

        full_path = os.path.join(base_path, file_name + ".npy")

        np.save(full_path, tagged)

    @staticmethod
    def __tag(ray_direction, max_distance, origin, tagging_order):

        tag_result = np.full(len(tagging_order), -9999)

        render_collection = D.collections["Rendering"]

        for layer in render_collection.objects:
            ray_result = layer.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]
                tag_result[tagging_order.index(layer.name)] = elevation

        for collection in render_collection.children:
            for layer in collection.objects:
                ray_result = layer.ray_cast(
                    origin, ray_direction, distance=max_distance
                )

                if ray_result[0]:
                    elevation = ray_result[1][2]
                    tag_result[tagging_order.index(collection.name)] = elevation
                    break

        return tag_result
