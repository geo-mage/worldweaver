import math

from mage_procgen.Renderer.BaseRenderer import BaseRenderer
from bpy import data as D
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
from mage_procgen.Utils.Utils import BuildingList, Point

class BuildingRenderer(BaseRenderer):
    _mesh_name = "Buildings"

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
