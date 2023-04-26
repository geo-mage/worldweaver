import os
import bpy
from bpy import data as D, context as C, ops as O
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
import math
from collections import deque
from mage_procgen.Utils.Utils import PolygonList, Point, GeoWindow


class TerrainRenderer:

    _mesh_name = "Terrain"

    def __init__(self, render_resolution: float, file_resolution: float):

        self.render_resolution = render_resolution
        self.file_resolution = file_resolution

        if render_resolution / file_resolution != render_resolution // file_resolution:
            raise ValueError(
                "terrain render resolution has to be a mutliple of file resolution"
            )

    def render(self, terrain_data, geo_window: GeoWindow):
        mesh = bmesh.new()

        center = geo_window.center

        box = geo_window.bounds

        current_terrain = terrain_data[0]

        global_x_min = min([x.x_min for x in terrain_data])
        global_x_max = max([x.x_max for x in terrain_data])
        global_y_min = min([x.y_min for x in terrain_data])
        global_y_max = max([x.y_max for x in terrain_data])

        total_pts_number_x = int((global_x_max - global_x_min) / self.render_resolution)
        total_pts_number_y = int((global_y_max - global_y_min) / self.render_resolution)

        range_x = range(total_pts_number_x)
        range_y = range(total_pts_number_y)

        previous_terrain_line = None

        for x in range_x:

            current_terrain_line = []

            current_point_x = global_x_min + x * self.render_resolution

            for y in range_y:

                current_point_y = global_y_min + y * self.render_resolution

                # Checking if the current point is in the current dataset
                is_point_in_current_terrain = True
                is_point_in_current_terrain &= current_point_x >= current_terrain.x_min
                is_point_in_current_terrain &= current_point_x < current_terrain.x_max
                is_point_in_current_terrain &= current_point_y >= current_terrain.y_min
                is_point_in_current_terrain &= current_point_y < current_terrain.y_max

                if not is_point_in_current_terrain:

                    for terrain in terrain_data:
                        is_point_in_terrain = True
                        is_point_in_terrain &= current_point_x >= terrain.x_min
                        is_point_in_terrain &= current_point_x < terrain.x_max
                        is_point_in_terrain &= current_point_y >= terrain.y_min
                        is_point_in_terrain &= current_point_y < terrain.y_max

                        if is_point_in_terrain:
                            current_terrain = terrain
                            break

                current_point_index_x = (
                    current_point_x - current_terrain.x_min
                ) / self.file_resolution
                # Y axis is pointing north so the index needs to be inversed
                current_point_index_y = 999 - (
                    (current_point_y - current_terrain.y_min) / self.file_resolution
                )

                if (
                    current_point_index_x != int(current_point_index_x)
                    or current_point_index_x > current_terrain.nbcol
                    or current_point_index_y != int(current_point_index_y)
                    or current_point_index_y > current_terrain.nbrow
                ):
                    print("INVALID POINT INDEX: ")
                    print("x: " + str(current_point_x) + " y: " + str(current_point_y))
                    print(
                        "i_x "
                        + str(current_point_index_x)
                        + " i_y: "
                        + str(current_point_index_y)
                    )
                    raise ValueError()

                # WARNING
                current_point_z = current_terrain.data.values[
                    int(current_point_index_y)
                ][int(current_point_index_x)]

                current_point_coords = [
                    current_point_x,
                    current_point_y,
                    current_point_z,
                ]

                current_point_centered_coords = [
                    current_point_coords[0] - center[0],
                    current_point_coords[1] - center[1],
                    current_point_coords[2] - center[2],
                ]

                current_terrain_line.append(current_point_centered_coords)

                if previous_terrain_line is not None and y > 0:

                    new_face_verts = [
                        current_terrain_line[y],
                        current_terrain_line[y - 1],
                        previous_terrain_line[y - 1],
                        previous_terrain_line[y],
                    ]

                    face = mesh.faces.new(mesh.verts.new(pt) for pt in new_face_verts)

            previous_terrain_line = current_terrain_line

        mesh_name = self._mesh_name
        mesh_data = D.meshes.new(mesh_name)
        mesh.to_mesh(mesh_data)
        mesh.free()
        mesh_obj = D.objects.new(mesh_data.name, mesh_data)
        C.collection.objects.link(mesh_obj)
