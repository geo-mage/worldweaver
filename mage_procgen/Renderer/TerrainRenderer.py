import os
import bpy
from bpy import data as D, context as C, ops as O
import bmesh

import math

from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Utils.Geometry import center_point
from mage_procgen.Loader import Loader


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

    def render(
        self,
        terrain_data,
        geo_window: GeoWindow,
        parent_collection_name,
        use_sat_img: bool = False,
    ):

        terrain_collection = D.collections[parent_collection_name]

        center = geo_window.center

        box = geo_window.bounds

        current_terrain = terrain_data[0]
        terrain_index = 0
        previous_point_terrain_index = 0

        meshes = {x: TerrainMeshInfo(bmesh.new()) for x in range(len(terrain_data))}
        meshes_points = {x: {} for x in range(len(terrain_data))}

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
                    or current_point_index_x < 0
                    or current_point_index_y < 0
                ):
                    # TODO: Fix this.
                    # Sometimes slabs are missing, when they're too far out to sea.
                    # This make the terrain render correctly but it attaches the points lying in the missing slab to another slab, which screws up the texture.

                    # print("INVALID POINT INDEX: ")
                    # print("x: " + str(current_point_x) + " y: " + str(current_point_y))
                    # print(
                    #    "i_x "
                    #    + str(current_point_index_x)
                    #    + " i_y: "
                    #    + str(current_point_index_y)
                    # )

                    # raise ValueError()
                    current_point_z = 0
                else:
                    current_point_z = current_terrain.data.values[
                        int(current_point_index_y)
                    ][int(current_point_index_x)]

                current_point_coords = [
                    current_point_x,
                    current_point_y,
                    current_point_z,
                ]

                current_terrain_line.append(current_point_coords)

                if previous_terrain_line is not None and x > 0:

                    new_face_verts = [
                        center_point(current_terrain_line[x], center),
                        center_point(current_terrain_line[x - 1], center),
                        center_point(previous_terrain_line[x - 1], center),
                        center_point(previous_terrain_line[x], center),
                    ]

                    # Some checks will be superfluous, but better be safe than sorry
                    TerrainRenderer.__check_boundaries(
                        current_terrain_line[x], meshes[previous_point_terrain_index]
                    )
                    TerrainRenderer.__check_boundaries(
                        current_terrain_line[x - 1],
                        meshes[previous_point_terrain_index],
                    )
                    TerrainRenderer.__check_boundaries(
                        previous_terrain_line[x - 1],
                        meshes[previous_point_terrain_index],
                    )
                    TerrainRenderer.__check_boundaries(
                        previous_terrain_line[x], meshes[previous_point_terrain_index]
                    )

                    new_face_mesh_verts = []
                    for pt in new_face_verts:
                        if pt not in meshes_points[previous_point_terrain_index]:
                            meshes_points[previous_point_terrain_index][pt] = meshes[
                                previous_point_terrain_index
                            ].mesh.verts.new(pt)
                        new_face_mesh_verts.append(
                            meshes_points[previous_point_terrain_index][pt]
                        )

                    face = meshes[previous_point_terrain_index].mesh.faces.new(
                        new_face_mesh_verts
                    )

                previous_point_terrain_index = terrain_index

            previous_terrain_line = current_terrain_line

        for index, mesh_info in meshes.items():

            pts_number_x = int(
                (mesh_info.x_max - mesh_info.x_min) / self.render_resolution
            )
            pts_number_y = int(
                (mesh_info.y_max - mesh_info.y_min) / self.render_resolution
            )

            mesh_name = self._mesh_name + "_" + str(index)
            mesh_data = D.meshes.new(mesh_name)

            mesh_info.mesh.to_mesh(mesh_data)
            mesh_info.mesh.free()
            mesh_obj = D.objects.new(mesh_data.name, mesh_data)
            mesh_material = D.materials[self._BaseMaterialName].copy()

            if use_sat_img:

                try:
                    texture_file_path = Loader.Loader.load_texture(
                        (
                            mesh_info.x_min,
                            mesh_info.y_min,
                            mesh_info.x_max,
                            mesh_info.y_max,
                        )
                    )

                    D.images.load(texture_file_path)

                    mesh_material.node_tree.nodes["Image Texture"].image = D.images[
                        os.path.basename(texture_file_path)
                    ]
                except Exception as e:
                    print("Couldn't add texture image to slab: " + str(e))

            mesh_data.materials.append(mesh_material)

            terrain_collection.objects.link(mesh_obj)

            uv_coords = [
                (1 / (pts_number_x), 1 / (pts_number_y)),
                (0, 1 / (pts_number_y)),
                (0, 0),
                (1 / (pts_number_x), 0),
            ]

            uvlayer = mesh_obj.data.uv_layers.new(name="UVMap_Terrain")

            for face in mesh_obj.data.polygons:

                # Each face has 4 loops (sides), and starts in the lower left corner (xmin, ymin)
                start_coord_x = (
                    1 / pts_number_x * ((face.loop_start // 4) % pts_number_x)
                )
                start_coord_y = (
                    1 / pts_number_y * (face.loop_start // (pts_number_x * 4))
                )

                start_coord = (start_coord_x, start_coord_y)
                for loop_idx in face.loop_indices:
                    cur_coord = uv_coords[loop_idx % 4]
                    uvlayer.data[loop_idx].uv = (
                        start_coord[0] + cur_coord[0],
                        start_coord[1] + cur_coord[1],
                    )

        bpy.ops.object.select_all(action="DESELECT")
        C.view_layer.objects.active = D.collections[parent_collection_name].objects[0]
        for terrain_obj in D.collections[parent_collection_name].objects:
            terrain_obj.select_set(True)

        O.object.join()

    @staticmethod
    def __check_boundaries(point, terrain_mesh_info):

        if point[0] < terrain_mesh_info.x_min:
            terrain_mesh_info.x_min = point[0]
        if point[0] > terrain_mesh_info.x_max:
            terrain_mesh_info.x_max = point[0]
        if point[1] < terrain_mesh_info.y_min:
            terrain_mesh_info.y_min = point[1]
        if point[1] > terrain_mesh_info.y_max:
            terrain_mesh_info.y_max = point[1]


class TerrainMeshInfo:
    def __init__(self, mesh):

        self.mesh = mesh
        self.x_min = math.inf
        self.x_max = -math.inf
        self.y_min = math.inf
        self.y_max = -math.inf
