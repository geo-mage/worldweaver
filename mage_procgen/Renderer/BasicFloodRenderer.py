import os
import bpy
from bpy import data as D, context as C
import bmesh


class BasicFloodRenderer:

    _mesh_name = "Flood"
    _AssetsFolder = "Assets"

    def __init__(self, object_config):
        self.config = object_config
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )

        # Render
        filepath = os.path.realpath(
            os.path.join(
                _location, "..", self._AssetsFolder, self.config.geometry_node_file
            )
        )
        try:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.node_groups = [self.config.geometry_node_name]
        except Exception as _:
            raise Exception(
                'Unable to load the Geometry Nodes setup with the name "'
                + self.config.geometry_node_name
                + '"'
                + "from the file "
                + filepath
            )

        # A Geometry Nodes setup with name object_config.geometry_node_name may already exist.
        self.geometry_node_name = data_to.node_groups[0].name

    def render(self, flood_data, parent_collection_name):

        flood_pixels = flood_data[0]
        flood_plan_z = flood_data[1]
        lower_left = flood_data[2]
        upper_right = flood_data[3]
        cellsize = flood_data[4]

        mesh = bmesh.new()

        corner_coord = cellsize / 2

        cell_coords = [
            (-corner_coord, corner_coord),
            (-corner_coord, -corner_coord),
            (corner_coord, -corner_coord),
            (corner_coord, corner_coord),
        ]

        for y in range(len(flood_pixels)):

            current_point_y = upper_right[1] - y * cellsize

            for x in range(len(flood_pixels[y])):

                if flood_pixels[y][x]:

                    current_point_x = lower_left[0] + x * cellsize

                    current_point_coords = [
                        current_point_x,
                        current_point_y,
                        flood_plan_z,
                    ]

                    new_face_verts = [
                        (
                            cell[0] + current_point_coords[0],
                            cell[1] + current_point_coords[1],
                            current_point_coords[2],
                        )
                        for cell in cell_coords
                    ]

                    face = mesh.faces.new(mesh.verts.new(pt) for pt in new_face_verts)

        mesh_name = self._mesh_name
        mesh_data = D.meshes.new(mesh_name)
        mesh.to_mesh(mesh_data)
        mesh.free()
        mesh_obj = D.objects.new(mesh_data.name, mesh_data)
        D.collections[parent_collection_name].objects.link(mesh_obj)

        m = mesh_obj.modifiers.new("", "NODES")
        m.node_group = D.node_groups[self.geometry_node_name]
