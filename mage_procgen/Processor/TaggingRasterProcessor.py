from bpy import data as D

from mathutils import *

import numpy as np

import os
import math

from mage_procgen.Utils.Rendering import buildings_collection_name


class TaggingRasterProcessor:
    @staticmethod
    def compute(base_path, file_name, resolution, tagging_order, zone_window, scene_center):

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

        # buildings_in_zone = []
        # buildings = D.collections[buildings_collection_name]
        #
        # window_box = zone_window.bounds
        # for layer in buildings.objects:
        #     layer_box = layer.bound_box
        #     layer_x_min = min([coord[0] for coord in layer_box]) + scene_center[0]
        #     layer_x_max = max([coord[0] for coord in layer_box]) + scene_center[0]
        #     layer_y_min = min([coord[1] for coord in layer_box]) + scene_center[1]
        #     layer_y_max = max([coord[1] for coord in layer_box]) + scene_center[1]
        #
        #     is_building_in_zone = False
        #     is_building_in_zone |= window_box[0] < layer_x_min < window_box[2] and window_box[1] < layer_y_min < window_box[3]
        #     is_building_in_zone |= window_box[0] < layer_x_min < window_box[2] and window_box[1] < layer_y_max < window_box[3]
        #     is_building_in_zone |= window_box[0] < layer_x_max < window_box[2] and window_box[1] < layer_y_min < window_box[3]
        #     is_building_in_zone |= window_box[0] < layer_x_max < window_box[2] and window_box[1] < layer_y_max < window_box[3]
        #
        #     if is_building_in_zone:
        #         buildings_in_zone.append(layer.name)
        #
        # print("Tagging using buildings: ", buildings_in_zone)

        # Preparing for the mapping of the tagging function. Signature is necessary because elevation works on a 3 dimensional vector (position) and returns another (RGB)
        tagging_function = np.vectorize(
            TaggingRasterProcessor.__tag, excluded={1, 2, 3}, signature="(3)->(7)"
        )

        tagged = tagging_function(ray_direction, max_distance, origin, tagging_order)#, buildings_in_zone)

        full_path = os.path.join(base_path, file_name + ".npy")

        np.save(full_path, tagged)

    @staticmethod
    def __tag(ray_direction, max_distance, origin, tagging_order):#, buildings_list):

        tag_result = np.full(len(tagging_order), -9999)

        render_collection = D.collections["Rendering"]

        for layer in render_collection.objects:
            ray_result = layer.ray_cast(origin, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]
                tag_result[tagging_order.index(layer.name)] = elevation

        for collection in render_collection.children:
            #if collection.name != buildings_collection_name:
            for layer in collection.objects:
                ray_result = layer.ray_cast(
                    origin, ray_direction, distance=max_distance
                )

                if ray_result[0]:
                    elevation = ray_result[1][2]
                    tag_result[tagging_order.index(collection.name)] = elevation
                    break

        # for building_name in buildings_list:
        #     building_object = D.objects[building_name]
        #     ray_result = building_object.ray_cast(
        #         origin, ray_direction, distance=max_distance
        #     )
        #
        #     if ray_result[0]:
        #         elevation = ray_result[1][2]
        #         tag_result[tagging_order.index(buildings_collection_name)] = elevation
        #         break

        return tag_result
