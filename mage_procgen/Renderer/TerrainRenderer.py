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

    _BaseMaterialName = "Base_Terrain"
    _MaterialFile = "Terrain.blend"
    _AssetsFolder = "Assets"

    def __init__(self, render_resolution: float, file_resolution: float):

        self.render_resolution = render_resolution
        self.file_resolution = file_resolution

        if render_resolution / file_resolution != render_resolution // file_resolution:
            raise ValueError(
                "terrain render resolution has to be a mutliple of file resolution"
            )

        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        filepath = os.path.realpath(
            os.path.join(_location, "..", self._AssetsFolder, self._MaterialFile)
        )
        try:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.materials = data_from.materials
        except Exception as _:
            raise Exception(
                "Unable to load the terrain material " + "from the file " + filepath
            )

        self._base_material = data_to.materials[0]

    def render(self, terrain_data, geo_window: GeoWindow, use_sat_img: bool = False):

        center = geo_window.center

        box = geo_window.bounds

        current_terrain = terrain_data[0]
        terrain_index = 0
        previous_point_terrain_index = 0

        meshes = {x: bmesh.new() for x in range(len(terrain_data))}

        global_x_min = min([x.x_min for x in terrain_data])
        global_x_max = max([x.x_max for x in terrain_data])
        global_y_min = min([x.y_min for x in terrain_data])
        global_y_max = max([x.y_max for x in terrain_data])

        total_pts_number_x = int((global_x_max - global_x_min) / self.render_resolution)
        total_pts_number_y = int((global_y_max - global_y_min) / self.render_resolution)

        range_x = range(total_pts_number_x)
        range_y = range(total_pts_number_y)

        previous_terrain_line = None

        for y in range_y:

            current_terrain_line = []

            current_point_y = global_y_min + y * self.render_resolution

            for x in range_x:

                current_point_x = global_x_min + x * self.render_resolution

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
                            terrain_index = terrain_data.index(current_terrain)
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

                if previous_terrain_line is not None and x > 0:

                    new_face_verts = [
                        current_terrain_line[x],
                        current_terrain_line[x - 1],
                        previous_terrain_line[x - 1],
                        previous_terrain_line[x],
                    ]

                    face = meshes[previous_point_terrain_index].faces.new(
                        meshes[previous_point_terrain_index].verts.new(pt)
                        for pt in new_face_verts
                    )

                previous_point_terrain_index = terrain_index

            previous_terrain_line = current_terrain_line

        i = 0
        for index, mesh in meshes.items():

            pts_number_x = int(
                (terrain_data[index].x_max - terrain_data[index].x_min)
                / self.render_resolution
            )
            pts_number_y = int(
                (terrain_data[index].y_max - terrain_data[index].y_min)
                / self.render_resolution
            )

            mesh_name = self._mesh_name + "_" + str(i)
            mesh_data = D.meshes.new(mesh_name)

            mesh.to_mesh(mesh_data)
            mesh.free()
            mesh_obj = D.objects.new(mesh_data.name, mesh_data)
            mesh_data.materials.append(D.materials[self._BaseMaterialName])

            C.collection.objects.link(mesh_obj)

            uv_coords = [
                (1 / (pts_number_x), 1 / (pts_number_y)),
                (0, 1 / (pts_number_y)),
                (0, 0),
                (1 / (pts_number_x), 0),
            ]

            uvlayer = mesh_obj.data.uv_layers.new(name="UVMap_Terrain")

            for face in mesh_obj.data.polygons:

                start_coord_x = (
                    1 / pts_number_x * ((face.loop_start // 4) % pts_number_x)
                )
                start_coord_y = (
                    1 / pts_number_y * (face.loop_start // (pts_number_x * 4))
                )

                if terrain_data[index].x_max == global_x_max:
                    start_coord_x = (
                        1 / pts_number_x * ((face.loop_start // 4) % (pts_number_x - 1))
                    )
                    start_coord_y = (
                        1 / pts_number_y * (face.loop_start // ((pts_number_x - 1) * 4))
                    )
                    if terrain_data[index].y_min == global_y_min:
                        start_coord_y = (
                            1
                            / pts_number_y
                            * ((face.loop_start // ((pts_number_x - 1) * 4)) + 1)
                        )
                else:
                    if terrain_data[index].y_min == global_y_min:
                        start_coord_y = (
                            1
                            / pts_number_y
                            * ((face.loop_start // (pts_number_x * 4)) + 1)
                        )

                start_coord = (start_coord_x, start_coord_y)
                for loop_idx in face.loop_indices:
                    cur_coord = uv_coords[loop_idx % 4]
                    uvlayer.data[loop_idx].uv = (
                        start_coord[0] + cur_coord[0],
                        start_coord[1] + cur_coord[1],
                    )

            i += 1
