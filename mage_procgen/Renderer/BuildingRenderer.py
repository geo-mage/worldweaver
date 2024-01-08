import math

from mage_procgen.Renderer.BaseRenderer import BaseRenderer
from bpy import data as D
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
from mage_procgen.Utils.Utils import BuildingList, Point, TerrainData
import os
import bpy


class BuildingRenderer(BaseRenderer):
    _mesh_name = "Buildings"

    def __init__(self, terrain_data: list[TerrainData], object_config):
        self.config = object_config
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
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

        # A Geometry Nodes setup with name object_config.geometry_node_name may alredy exist.
        self.geometry_node_name = data_to.node_groups[0].name

        # Buildify does not realize instances of the objects it adds, so they have their own pass index.
        # In order to set it, we have to get the objects that are used by the geometry nodes.
        # This way is quite dirty and specific to Buildify, but it works.
        # We get all collections that are used in the imported geometrynode, and deduce the objects.
        added_collections = []
        for node in D.node_groups[self.geometry_node_name].nodes:
            for input in node.inputs:
                if input.type == "COLLECTION":
                    added_collections.append(input.default_value)

        for collection in set(added_collections):
            for obj in collection.objects:
                obj.pass_index = object_config.tagging_index

        self._terrain_data = terrain_data

    def render(
        self,
        buildings: BuildingList,
        geo_center: tuple[float, float, float],
        parent_collection_name,
    ):

        self._mesh_names = []

        for building in tqdm(buildings):
            mesh = bmesh.new()
            # Kind of hack because Polygon.coords is not implemented
            polygon_geometry = mapping(building[1])["coordinates"]
            points_coords = [
                (x[0], x[1], self.interpolate_z(x[0], x[1]))
                for x in polygon_geometry[0]
            ]

            if len(polygon_geometry) > 1:
                # If there are holes
                for hole in polygon_geometry[1:]:
                    points_coords_hole = [
                        (x[0], x[1], self.interpolate_z(x[0], x[1])) for x in hole
                    ]

                    points_coords = self.insert_hole(points_coords, points_coords_hole)

            # Adapting the coordinates for rendering purposes
            centered_points_coords = self.adapt_coords(points_coords, geo_center)

            # Need to remove the last point so that it's not repeated and creates a segment of 0 length
            face = mesh.faces.new(
                mesh.verts.new(x) for x in centered_points_coords[:-1]
            )

            mesh_name = self._mesh_name
            mesh_data = D.meshes.new(mesh_name)
            mesh.to_mesh(mesh_data)
            mesh.free()
            mesh_obj = D.objects.new(mesh_data.name, mesh_data)
            mesh_obj.pass_index = self.config.tagging_index
            D.collections[parent_collection_name].objects.link(mesh_obj)

            self._mesh_names.append(mesh_obj.name)

            m = mesh_obj.modifiers.new("", "NODES")
            m.node_group = D.node_groups[self.geometry_node_name]

            # If we have the info in the database, use it here
            if not math.isnan(building[0]):
                # Adding 1 to the DB value because the (flat) roof is considered as a floor
                mesh_obj.modifiers[0]["Input_6"] = int(building[0]) + 1
                mesh_obj.modifiers[0]["Input_7"] = int(building[0]) + 1

    def adapt_coords(
        self, points_coords: list[Point], geo_center: Point
    ) -> list[Point]:

        # Centering the coordinates so that Blender's internal precision is less impactful
        # Also, building rendering requires the base polygon to have constant z, so we fix every point's z to be the lowest in the set.
        z_min = min([x[2] for x in points_coords])

        centered_points_coords = [
            (x[0] - geo_center[0], x[1] - geo_center[1], z_min - geo_center[2])
            for x in points_coords
        ]

        return centered_points_coords

    def clear_object(self):

        for object_name in self._mesh_names:
            D.objects.remove(D.objects[object_name], do_unlink=True)
            D.meshes.remove(D.meshes[object_name], do_unlink=True)


class ChurchRenderer(BuildingRenderer):
    _mesh_name = "Churches"


class MallRenderer(BuildingRenderer):
    _mesh_name = "Malls"


class FactoryRenderer(BuildingRenderer):
    _mesh_name = "Factories"
