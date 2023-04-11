import os
import bpy
from bpy import data as D, context as C, ops as O
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
import math
from collections import deque


class RoadRenderer:
    _AssetFile = "Roads.blend"
    _AssetsFolder = "Assets"
    _AssetName = "Road_Piece"
    _mesh_name = "Roads"

    def __init__(self):
        _location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        filepath = os.path.realpath(
            os.path.join(_location, "..", self._AssetsFolder, self._AssetFile)
        )
        try:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.objects = [self._AssetName]
        except Exception as _:
            raise Exception(
                'Unable to load the Asset with the name "'
                + self._AssetName
                + '"'
                + "from the file "
                + filepath
            )

        # TODO: Understand following comment:

        # A Geometry Nodes setup with name <self.gnSetup2d> may alredy exist.
        # That's why following line
        self.road_asset = data_to.objects[0].name

    def render(self, lines, geo_center):
        road_collection = D.collections.new(self._mesh_name)
        C.scene.collection.children.link(road_collection)
        src_obj = D.objects[self._AssetName]

        line_index = 1

        for line in tqdm(lines):
            # mesh = bmesh.new()
            line_geometry = line.coords
            points_coords = [[x[0], x[1], 0] for x in line_geometry]

            # Centering the coordinates so that Blender's internal precision is less impactful
            # centered_points_coords = [
            #    [x[0] - geo_center[0], x[1] - geo_center[1], x[2] - geo_center[2]]
            #    for x in points_coords
            # ]

            ## Need to remove the last point so that it's not repeated and creates a segment of 0 length
            # face = mesh.faces.new(
            #    mesh.verts.new(x) for x in centered_points_coords[:-1]
            # )

            # make a new curve
            crv = D.curves.new("crv" + str(line_index), "CURVE")
            crv.dimensions = "3D"

            # make a new spline in that curve
            spline = crv.splines.new(type="NURBS")

            # a spline point for each point
            spline.points.add(
                len(points_coords) - 1
            )  # theres already one point by default

            # assign the point coordinates to the spline points
            for p, new_co in zip(spline.points, points_coords):
                p.co = new_co + [1.0]  # (add nurbs weight)

            # make a new object with the curve
            curve_to_fit = D.objects.new("curve_road" + str(line_index), crv)
            road_collection.objects.link(curve_to_fit)

            new_obj = src_obj.copy()
            new_obj.data = src_obj.data.copy()
            new_obj.name = src_obj.name + "_copy_" + str(line_index)
            road_collection.objects.link(new_obj)

            m = new_obj.modifiers.new("", "ARRAY")
            m.name = "roadarraymod"
            m.fit_type = "FIT_CURVE"
            m.curve = curve_to_fit

            m2 = new_obj.modifiers.new("", "CURVE")
            m2.name = "curvearraymod"
            m2.object = curve_to_fit

            line_index += 1

        # mesh_name = self._mesh_name
        # mesh_data = D.meshes.new(mesh_name)
        # mesh.to_mesh(mesh_data)
        # mesh.free()
        # mesh_obj = D.objects.new(mesh_data.name, mesh_data)
        # C.collection.objects.link(mesh_obj)


#
# m = mesh_obj.modifiers.new("", "NODES")
# m.node_group = D.node_groups[self._GNSetup]
