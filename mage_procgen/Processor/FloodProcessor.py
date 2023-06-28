from bpy import data as D
from skimage.segmentation import flood, flood_fill
from skimage.morphology import closing
from skimage.morphology import disk

from mathutils import *

import numpy as np

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from math import floor, ceil


class FloodProcessor:
    @staticmethod
    def flood(geo_window: GeoWindow, flood_height: float):

        bounds = geo_window.bounds
        center = geo_window.center

        # We will only flood on the geowindow, but we also need to round up the coords
        lower_left = (bounds[0], bounds[1], 0)
        upper_right = (bounds[2], bounds[3], 0)
        centered_ll = center_point(lower_left, center)
        centered_ur = center_point(upper_right, center)
        rounded_ll = (ceil(centered_ll[0]), ceil(centered_ll[1]), 0)
        rounded_ur = (floor(centered_ur[0]), floor(centered_ur[1]), 0)

        # TODO: find a way to calculate those so they fit every case
        comp_plane_z = 250
        max_distance = 300
        disk_size = 2

        # This holds every coordinate from which rays will be fired towards the terrain to get the height
        comp_plane = np.array(
            [
                [
                    Vector([x, y, comp_plane_z])
                    for x in range(rounded_ll[0], rounded_ur[0])
                ]
                for y in range(rounded_ur[1], rounded_ll[1], -1)
            ]
        )

        ray_direction = Vector([0, 0, -1])

        # Preparing for the mapping of the elevation function. Signature is necessary because elevation works on a 3 dimensional vector
        elevation_function = np.vectorize(
            FloodProcessor.__find_elevation, excluded={1, 2}, signature="(3)->()"
        )

        elevation = elevation_function(comp_plane, max_distance, ray_direction)

        min_height = elevation.min()
        min_index = np.argmin(elevation)
        min_row_index = min_index // elevation.shape[1]
        min_col_index = min_index % elevation.shape[1]

        # Mask holding, for each pixel, if it is part of the flood or not
        flooded = flood(
            elevation, (min_row_index, min_col_index), tolerance=flood_height
        )

        # Cleaning edges
        footprint = disk(disk_size)
        closed = closing(flooded, footprint)

        return (closed, min_height + flood_height, rounded_ll, rounded_ur)

    @staticmethod
    def __find_elevation(point, max_distance, ray_direction):

        terrain_collection = D.collections["Terrain"].objects

        elevation = None

        for terrain in terrain_collection:
            ray_result = terrain.ray_cast(point, ray_direction, distance=max_distance)

            if ray_result[0]:
                elevation = ray_result[1][2]

        # No collision with terrain, should not happen
        if elevation is None:
            raise ValueError("Could not find elevation of point " + str(point))

        buildings = D.objects["Buildings"]

        building_ray_result = buildings.ray_cast(
            point, ray_direction, distance=max_distance
        )

        if building_ray_result[0]:
            # TODO: check should not be necessary here ?
            if building_ray_result[1][2] > elevation:
                elevation = building_ray_result[1][2]

        return elevation
