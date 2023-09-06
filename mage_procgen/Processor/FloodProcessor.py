import math

from bpy import data as D

from scipy.sparse.csgraph import dijkstra

from mathutils import *

import numpy as np

from scipy.sparse import bsr_array

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from math import floor, ceil

from math import exp, pow


class FloodProcessor:
    @staticmethod
    def flood(
        geo_window: GeoWindow,
        max_flood_height: float,
        flood_threshold: float,
        flood_cell_size: float,
    ):

        bounds = geo_window.bounds
        center = geo_window.center

        # We will only flood on the geowindow, but we also need to round up the coords
        lower_left = (bounds[0], bounds[1], 0)
        upper_right = (bounds[2], bounds[3], 0)
        centered_ll = center_point(lower_left, center)
        centered_ur = center_point(upper_right, center)
        rounded_ll = (ceil(centered_ll[0]), ceil(centered_ll[1]), 0)
        rounded_ur = (floor(centered_ur[0]), floor(centered_ur[1]), 0)

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
        init_flood_state = np.vectorize(
            FloodProcessor.__init_flood_state, excluded={1, 2}, signature="(3)->(3)"
        )

        flood_init = init_flood_state(comp_plane, max_distance, ray_direction)

        # Compute for each pixel the height of the flood, if applicable
        flood_state_rows = flood_init.shape[0]
        flood_state_cols = flood_init.shape[1]

        # To get the coordinates of a cell's neighbors
        coord_modifiers = [
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ]

        sources_index = []
        rows = []
        cols = []
        data = []

        for row in range(flood_state_rows):
            for column in range(flood_state_cols):
                point_distance_index = row * flood_state_cols + column
                point_value = flood_init[row][column]

                # If a point is a source
                if point_value[2]:
                    sources_index.append(point_distance_index)

                for mod in coord_modifiers:
                    comp_row = row + mod[0]
                    comp_col = column + mod[1]

                    # If the neighbor is actually inside the grid (no out of bounds)
                    if (
                        comp_row >= 0
                        and comp_row < flood_state_rows
                        and comp_col >= 0
                        and comp_col < flood_state_cols
                    ):
                        mod_index = comp_row * flood_state_cols + comp_col
                        mod_value = flood_init[comp_row][comp_col]
                        rows.append(point_distance_index)
                        cols.append(mod_index)

                        # Compute the cell to cell distance
                        data.append(
                            FloodProcessor.distance_function(point_value, mod_value)
                        )

        a_rows = np.array(rows)
        a_cols = np.array(cols)
        a_data = np.array(data)

        flood_graph = bsr_array(
            (a_data, (a_rows, a_cols)),
            shape=(
                flood_state_rows * flood_state_cols,
                flood_state_rows * flood_state_cols,
            ),
        )

        flood_graph_distances, predecessors, sources = dijkstra(
            flood_graph,
            indices=sources_index,
            min_only=True,
            limit=1.1 * flood_threshold,
            return_predecessors=True,
        )

        flood_result = np.zeros((flood_state_rows, flood_state_cols))
        for row in range(flood_state_rows):
            for column in range(flood_state_cols):
                point_index = row * flood_state_cols + column

                point_source = sources[point_index]
                source_row = point_source // flood_state_cols
                source_column = point_source % flood_state_cols
                source_elevation = flood_init[source_row][source_column][0]

                flood_result[row][column] = FloodProcessor.flood_height(
                    max_flood_height,
                    flood_threshold,
                    flood_graph_distances[point_index],
                    flood_init[row][column][0],
                    flood_init[row][column][1],
                    source_elevation,
                )

        return (
            flood_init,
            flood_result,
            rounded_ll,
            rounded_ur,
            flood_cell_size,
        )

    @staticmethod
    def __init_flood_state(point, max_distance, ray_direction):

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

        building_height = 0

        if building_ray_result[0]:
            # TODO: check should not be necessary here ?
            if building_ray_result[1][2] > elevation:
                building_height = building_ray_result[1][2]

        flowing_water = D.objects["Flowing_Water"]

        flowing_water_ray_result = flowing_water.ray_cast(
            point, ray_direction, distance=max_distance
        )

        is_source = 0

        if flowing_water_ray_result[0]:
            is_source = 1

        return np.array([elevation, building_height, is_source])

    # TODO: take buildings into account somehow
    # TODO: generally, calibrate this
    @staticmethod
    def distance_function(point_a, point_b):
        return exp(point_b[0] - point_a[0])

    @staticmethod
    def flood_height(
        max_flood_height,
        flood_threshold,
        distance_to_source,
        terrain_height,
        building_height,
        source_height,
    ):
        if distance_to_source > flood_threshold:
            return 0
        else:
            flood_value = max_flood_height * pow(
                (distance_to_source - flood_threshold) / flood_threshold, 2
            )
            if flood_value + terrain_height > source_height + max_flood_height:
                corrected_flood_value = (
                    source_height + max_flood_height - terrain_height
                )
                if corrected_flood_value < 0:
                    return 0
                else:
                    return flood_value
            else:
                return flood_value
