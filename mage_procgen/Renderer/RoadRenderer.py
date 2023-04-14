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
            line_geometry = line.coords
            points_coords = [[x[0], x[1], 0] for x in line_geometry]

            # Centering the coordinates so that Blender's internal precision is less impactful
            centered_points_coords = [
               [x[0] - geo_center[0], x[1] - geo_center[1], x[2] - geo_center[2]]
               for x in points_coords
            ]

            road_curve_mesh = bmesh.new()

            # Constructing a mesh consisting of a series of edges
            prev_point = None
            is_first = True
            for pt in centered_points_coords:
                current_point = road_curve_mesh.verts.new((pt[0], pt[1], pt[2]))
                if is_first:
                    is_first = False
                else:
                    road_curve_mesh.edges.new((prev_point, current_point))
                prev_point = current_point

            road_curve_mesh_name = "RoadCurve_" + str(line_index)
            road_curve_mesh_data = D.meshes.new(road_curve_mesh_name)
            road_curve_mesh.to_mesh(road_curve_mesh_data)
            road_curve_mesh.free()
            road_curve_mesh_obj = D.objects.new(road_curve_mesh_data.name, road_curve_mesh_data)
            C.collection.objects.link(road_curve_mesh_obj)

            # Transforming the mesh into a curve (requires context override)
            area = [area for area in C.screen.areas if area.type == "VIEW_3D"][0]
            with C.temp_override(area=area):
                road_curve_mesh_obj.select_set(True)
                C.view_layer.objects.active = road_curve_mesh_obj
                O.object.convert(target="CURVE")
                road_curve_mesh_obj.select_set(False)

            curve_to_fit = D.objects[road_curve_mesh_name]

            # Duplicating the road template
            road_object = src_obj.copy()
            road_object.data = src_obj.data.copy()
            road_object.name = src_obj.name + "_copy_" + str(line_index)
            road_collection.objects.link(road_object)

            # Adding the array and curve modifiers
            road_array_mod = road_object.modifiers.new("", "ARRAY")
            road_array_mod.name = "roadarraymod"
            road_array_mod.fit_type = "FIT_CURVE"
            road_array_mod.curve = curve_to_fit

            road_curve_mod = road_object.modifiers.new("", "CURVE")
            road_curve_mod.name = "roadcurvemod"
            road_curve_mod.object = curve_to_fit

            # Applying all the modifiers (requires context override)
            area = [area for area in C.screen.areas if area.type == "VIEW_3D"][0]
            with C.temp_override(area=area):
                for mod in road_object.modifiers:
                    road_object.select_set(True)
                    C.view_layer.objects.active = road_object
                    O.object.modifier_apply(modifier=mod.name)
                    road_object.select_set(False)

            # Removing objects that are no longer needed since modifers have been applied
            O.object.select_all(action='DESELECT')
            road_curve_mesh_obj.select_set(True)
            O.object.delete()
            D.curves.remove(D.curves[road_curve_mesh_name])
            D.meshes.remove(D.meshes[road_curve_mesh_name])

            line_index += 1

