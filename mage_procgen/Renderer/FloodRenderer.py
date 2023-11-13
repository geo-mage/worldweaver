import os
import bpy
from bpy import data as D
import bmesh
from tqdm import tqdm


class FloodRenderer:

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

    # TODO: fix issue where only parts of the edge cells are made. currently, it does one where specifically the topright exists
    # Need to make sure that a cell is made once and only once
    def render(self, flood_data, parent_collection_name):

        flood_init_state = flood_data[0]
        flood_pixels = flood_data[1]
        is_flooded = flood_data[2]
        lower_left = flood_data[3]
        upper_right = flood_data[4]
        cellsize = flood_data[5]

        mesh = bmesh.new()

        corner_coord = cellsize / 2

        cell_coords = [
            (-1, -1),
            (-1, 0),
            (0, 0),
            (0, -1),
        ]

        meshes_points = {}

        print("Rendering flood")

        for y in tqdm(range(1, len(flood_pixels))):

            for x in range(1, len(flood_pixels[y])):

                # If this point is flooded
                if is_flooded[y][x]:

                    face_coords = []

                    for coord_mod in cell_coords:

                        current_x = x + coord_mod[0]
                        current_y = y + coord_mod[1]

                        current_point_y = upper_right[1] - current_y * cellsize
                        current_point_x = lower_left[0] + current_x * cellsize

                        # Either is the flood height, or 0. which is exactly what we want
                        flood_height_point = flood_pixels[current_y][current_x]
                        ## If this point exists
                        # if flood_pixels[current_point_y][current_x]:
                        #    pass
                        #
                        # else:

                        terrain_height_point = flood_init_state[current_y][current_x][0]

                        current_point_z = flood_height_point  # + terrain_height_point

                        current_point_coords = (
                            current_point_x,
                            current_point_y,
                            current_point_z,
                        )

                        if current_point_coords not in meshes_points:
                            meshes_points[current_point_coords] = mesh.verts.new(
                                current_point_coords
                            )
                        face_coords.append(meshes_points[current_point_coords])

                    # new_face_verts = [
                    #    (
                    #        cell[0] + current_point_coords[0],
                    #        cell[1] + current_point_coords[1],
                    #        current_point_coords[2],
                    #    )
                    #    for cell in cell_coords
                    # ]

                    face = mesh.faces.new(face_coords)

        mesh_name = self._mesh_name
        mesh_data = D.meshes.new(mesh_name)
        mesh.to_mesh(mesh_data)
        mesh.free()
        mesh_obj = D.objects.new(mesh_data.name, mesh_data)
        D.collections[parent_collection_name].objects.link(mesh_obj)

        m = mesh_obj.modifiers.new("", "NODES")
        m.node_group = D.node_groups[self.geometry_node_name]
