import os
import bpy
from bpy import data as D, context as C, ops as O
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm


class BaseRenderer:

    _GNSetup = ""
    _GNFile = ""
    _AssetsFolder = "Assets"
    _mesh_name = ""

    def __init__(self):
        _location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        filepath = os.path.realpath(os.path.join(_location, "..", self._AssetsFolder, self._GNFile))
        try:
            with bpy.data.libraries.load(filepath) as (data_from, data_to):
                data_to.node_groups = [self._GNSetup]
        except Exception as _:
            raise Exception(
                "Unable to load the Geometry Nodes setup with tha name \"" + self._GNSetup + "\"" + \
                "from the file " + filepath
            )

        #TODO: Understand following comment:

        # A Geometry Nodes setup with name <self.gnSetup2d> may alredy exist.
        # That's why following line
        self.gnSetup2d = data_to.node_groups[0].name

    def render(self, polygons, geo_center):

        mesh = bmesh.new()

        for polygon in tqdm(polygons):
            # Kind of hack because Polygon.coords is not implemented
            points_coords = [(x[0], x[1], 0) for x in mapping(polygon)["coordinates"][0]]
            face = mesh.faces.new(mesh.verts.new(x) for x in points_coords)

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
