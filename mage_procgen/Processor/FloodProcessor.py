import math

from bpy import data as D

from scipy.sparse.csgraph import dijkstra

from mathutils import *

import numpy as np

from scipy.sparse import bsr_array
from scipy.ndimage import gaussian_filter as gf


from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from mage_procgen.Utils.Rendering import (
    export_rendered_img,
    setup_img_ortho,
)

from math import floor, ceil

from math import exp, pow

from tqdm import tqdm

import mage_procgen.Utils.DataFiles as df
import os

import OpenEXR
import Imath
import array


class FloodProcessor:
    @staticmethod
    def flood(
        base_folder: str,
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

        size_x = rounded_ur[0] - rounded_ll[0]
        size_y = rounded_ur[1] - rounded_ll[1]

        camera_z = setup_img_ortho(size_x, size_y, flood_cell_size, (0, 0))

        export_rendered_img(
            os.path.join(base_folder, df.rendering, df.temp_folder),
            df.temp_rendering_file,
        )

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
        init_source_points = np.vectorize(
            FloodProcessor.__init_source_points, excluded={1, 2}, signature="(3)->()"
        )

        depth_map_file = OpenEXR.InputFile(
            os.path.join(
                base_folder,
                df.rendering,
                df.temp_folder,
                df.depth_map_file_full_name,
            )
        )

        # Compute the size
        depth_map_data_window = depth_map_file.header()["dataWindow"]
        depth_map_size = (
            depth_map_data_window.max.x - depth_map_data_window.min.x + 1,
            depth_map_data_window.max.y - depth_map_data_window.min.y + 1,
        )

        # Read the three color channels as 32-bit floats
        FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)

        depth_map = np.array(
            array.array("f", depth_map_file.channel("R", FLOAT))
        ).reshape(depth_map_size[1], depth_map_size[0])

        height_map = camera_z - depth_map
        source_points = init_source_points(comp_plane, max_distance, ray_direction)

        if height_map.shape != source_points.shape:
            raise ValueError("Height map and source raster are not the same shape")

        # Compute for each pixel the height of the flood, if applicable
        flood_state_rows = source_points.shape[0]
        flood_state_cols = source_points.shape[1]

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

                # If a point is a source
                if source_points[row][column]:
                    sources_index.append(point_distance_index)

                for mod in coord_modifiers:
                    comp_row = row + mod[0]
                    comp_col = column + mod[1]

                    # If the neighbor is actually inside the grid (no out of bounds)
                    if (
                        0 <= comp_row < flood_state_rows
                        and 0 <= comp_col < flood_state_cols
                    ):
                        mod_index = comp_row * flood_state_cols + comp_col
                        rows.append(point_distance_index)
                        cols.append(mod_index)

                        # Compute the cell to cell distance
                        data.append(
                            FloodProcessor.distance_function(
                                height_map[row][column], height_map[comp_row][comp_col]
                            )
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

        # limit=1.1 * flood_threshold,
        flood_graph_distances, predecessors, sources = dijkstra(
            flood_graph,
            indices=sources_index,
            min_only=True,
            return_predecessors=True,
        )

        flood_result = np.zeros((flood_state_rows, flood_state_cols))
        flood_state = np.zeros((flood_state_rows, flood_state_cols))
        # path_lengths = np.full((flood_state_rows, flood_state_cols), -9999)

        print("Calculating flood")

        for row in tqdm(range(flood_state_rows)):
            for column in range(flood_state_cols):
                point_index = row * flood_state_cols + column

                # Retrieving the source point of the current point
                point_source = sources[point_index]
                source_row = point_source // flood_state_cols
                source_column = point_source % flood_state_cols
                source_elevation = height_map[source_row][source_column]

                # Finding the path length
                # path_length = 0
                # predecessor = predecessors[point_index]
                #
                # while predecessor != -9999:
                #   path_length += 1
                #   predecessor = predecessors[predecessor]
                #   predecessor_row = predecessor // flood_state_cols
                #   predecessor_column = predecessor % flood_state_cols
                #
                #   # If path length for a predecessor has been found
                #   if path_lengths[predecessor_row][predecessor_column] != -9999:
                #       path_length = path_length + path_lengths[predecessor_row][predecessor_column]
                #       break
                #
                # path_lengths[row][column] = path_length
                # print("Found path ! Length: " + str(path_length))

                (is_flooded, water_height) = FloodProcessor.flood_height(
                    max_flood_height,
                    flood_threshold,
                    flood_graph_distances[point_index],
                    height_map[row][column],
                    source_elevation,
                    # path_length,
                )

                flood_state[row][column] = is_flooded

                flood_result[row][column] = water_height

        flood_result = gf(flood_result, 5)

        return (
            height_map,
            flood_result,
            flood_state,
            rounded_ll,
            rounded_ur,
            flood_cell_size,
        )

    @staticmethod
    def __init_source_points(point, max_distance, ray_direction):

        flowing_water = D.objects["Flowing_Water"]

        flowing_water_ray_result = flowing_water.ray_cast(
            point, ray_direction, distance=max_distance
        )

        is_source = 0

        if flowing_water_ray_result[0]:
            return 1
        else:
            return 0

    # TODO: take buildings into account somehow
    # TODO: generally, calibrate this
    @staticmethod
    def distance_function(point_a, point_b):
        return exp(point_b - point_a)
        # return 1

    @staticmethod
    def flood_height(
        max_flood_height,
        flood_threshold,
        distance_to_source,
        terrain_height,
        # building_height,
        source_height,
        # path_length,
    ):

        water_height = terrain_height
        is_flooded = 1

        if distance_to_source > flood_threshold:
            is_flooded = 0
            return (is_flooded, 0)

        # Water height if the cell was at the same height as the source
        flood_value = max_flood_height * pow(
            (distance_to_source - flood_threshold) / flood_threshold, 2
        )

        # Correcting for terrain
        # flood_value += source_height - terrain_height

        # water_height = terrain_height + flood_value

        # Clamping. Don't know if it's still necessary

        # if flood_value + terrain_height > source_height + max_flood_height:
        #    # Water cannot be above the source height
        #    corrected_flood_value = (
        #        source_height + max_flood_height - terrain_height
        #    )
        #    if corrected_flood_value < 0:
        #        is_flooded = 0
        #    else:
        #        water_height = terrain_height + corrected_flood_value
        # elif flood_value < 0:
        #    is_flooded = 0
        # else:
        #    water_height = terrain_height + flood_value

        water_height = flood_value + source_height

        if water_height < terrain_height + 1e-1:
            is_flooded = 0

        return (is_flooded, water_height)
