import math

from bpy import data as D
from skimage.segmentation import flood, flood_fill
from skimage.morphology import closing
from skimage.morphology import disk

from mathutils import *

import numpy as np

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from math import floor, ceil


class BasicFloodProcessor:
    @staticmethod
    def flood(geo_window: GeoWindow, flood_height: float, flood_cell_size: float):

        bounds = geo_window.bounds
        center = geo_window.center

        # We will only flood on the geowindow, but we also need to round up the coords
        lower_left = (bounds[0], bounds[1], 0)
        upper_right = (bounds[2], bounds[3], 0)
        centered_ll = center_point(lower_left, center)
        centered_ur = center_point(upper_right, center)
        rounded_ll = (ceil(centered_ll[0]), ceil(centered_ll[1]), 0)
        rounded_ur = (floor(centered_ur[0]), floor(centered_ur[1]), 0)

        # TODO: check this value
        disk_size = 2

        max_z = -math.inf
        min_z = math.inf

        # Calculating the maximum height of the scene, using terrain and buildings
        # TODO: check if there are edge cases where this does not hold
        terrain_collection = D.collections["Terrain"].objects
        for terrain in terrain_collection:
            terrain_box = terrain.bound_box
            z_coords = [v[2] for v in terrain_box]
            cur_z_max = max(z_coords)
            cur_z_min = min(z_coords)
            if cur_z_max > max_z:
                max_z = cur_z_max
            if cur_z_min < min_z:
                min_z = cur_z_min
        building_box_vertices = D.objects["Buildings"].bound_box
        building_z_coords = [v[2] for v in building_box_vertices]
        cur_z_max = max(building_z_coords)
        cur_z_min = min(building_z_coords)
        if cur_z_max > max_z:
            max_z = cur_z_max
        if cur_z_min < min_z:
            min_z = cur_z_min

        # Plane from which the rays shoot need to be above the scene. Margin on 50m is taken to be sure.
        comp_plane_z = max_z + 50
        max_distance = (comp_plane_z - min_z) + 50

        # This holds every coordinate from which rays will be fired towards the terrain to get the height
        # Step on Y in negative because y axis is north pointing
        comp_plane = np.array(
            [
                [
                    Vector([x, y, comp_plane_z])
                    for x in np.arange(rounded_ll[0], rounded_ur[0], flood_cell_size)
                ]
                for y in np.arange(rounded_ur[1], rounded_ll[1], -flood_cell_size)
            ]
        )

        ray_direction = Vector([0, 0, -1])

        # Preparing for the mapping of the elevation function. Signature is necessary because elevation works on a 3 dimensional vector
        elevation_function = np.vectorize(
            BasicFloodProcessor.__find_elevation, excluded={1, 2}, signature="(3)->()"
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

        return (
            closed,
            min_height + flood_height,
            rounded_ll,
            rounded_ur,
            flood_cell_size,
        )

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
