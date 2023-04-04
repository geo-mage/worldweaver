import os
import bpy
from bpy import data as D, context as C, ops as O
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
import math
from collections import deque


class BaseRenderer:
    _GNSetup = ""
    _GNFile = ""
    _AssetsFolder = "Assets"
    _mesh_name = ""

    def __init__(self):
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        filepath = os.path.realpath(
            os.path.join(_location, "..", self._AssetsFolder, self._GNFile)
        )
        try:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.node_groups = [self._GNSetup]
        except Exception as _:
            raise Exception(
                'Unable to load the Geometry Nodes setup with tha name "'
                + self._GNSetup
                + '"'
                + "from the file "
                + filepath
            )

        # TODO: Understand following comment:

        # A Geometry Nodes setup with name <self.gnSetup2d> may alredy exist.
        # That's why following line
        self.gnSetup2d = data_to.node_groups[0].name

    def render(self, polygons, geo_center):
        mesh = bmesh.new()

        for polygon in tqdm(polygons):
            # Kind of hack because Polygon.coords is not implemented
            polygon_geometry = mapping(polygon)["coordinates"]
            points_coords = [(x[0], x[1], 0) for x in polygon_geometry[0]]

            if len(polygon_geometry) > 1:
                # If there are holes
                for hole in polygon_geometry[1:]:
                    points_coords_hole = [(x[0], x[1], 0) for x in hole]

                    points_coords = self.insert_hole(points_coords, points_coords_hole)

            # Need to remove the last point so that it's not repeated and creates a segment of 0 length
            face = mesh.faces.new(mesh.verts.new(x) for x in points_coords[:-1])

        mesh_name = self._mesh_name
        mesh_data = D.meshes.new(mesh_name)
        mesh.to_mesh(mesh_data)
        mesh.free()
        mesh_obj = D.objects.new(mesh_data.name, mesh_data)
        C.collection.objects.link(mesh_obj)

        mesh_obj.select_set(True)
        mesh_obj.location[0] = -geo_center[0]
        mesh_obj.location[1] = -geo_center[1]
        mesh_obj.location[2] = -geo_center[2]
        O.object.transform_apply(location=True)
        mesh_obj.select_set(False)

        m = mesh_obj.modifiers.new("", "NODES")
        m.node_group = D.node_groups[self._GNSetup]

    def insert_hole(self, points_coords, points_coords_hole):
        min_dist = math.inf
        closest_pt_poly = None
        closest_pt_hole = None

        # Last point is always repeated to close the polygon/hole
        unique_points_coords = points_coords[:-1]
        unique_points_coords_hole = points_coords_hole[:-1]

        # Finding the closest distance between the poly and the hole, and associated points
        for pt_poly in unique_points_coords:
            for pt_hole in unique_points_coords_hole:
                distance = math.dist(pt_poly, pt_hole)
                if distance < min_dist:
                    min_dist = distance
                    closest_pt_poly = pt_poly
                    closest_pt_hole = pt_hole

        # Making the closest point of the hole the first in the list
        rotation_index = -unique_points_coords_hole.index(closest_pt_hole)
        deq = deque(unique_points_coords_hole)
        deq.rotate(rotation_index)
        rotated_hole = list(deq)

        # Splitting the orignal polygon at the correct index
        insertion_index = unique_points_coords.index(closest_pt_poly) + 1
        poly_first_part = unique_points_coords[:insertion_index]
        poly_second_part = unique_points_coords[insertion_index:]

        # Fusing the polygon with the hole
        toreturn = []
        toreturn.extend(poly_first_part)
        toreturn.extend(rotated_hole)
        toreturn.append(closest_pt_hole)
        toreturn.append(closest_pt_poly)
        toreturn.extend(poly_second_part)
        toreturn.append(poly_first_part[0])

        return toreturn
