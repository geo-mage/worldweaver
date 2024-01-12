import os
import bpy
from bpy import data as D
import bmesh
from shapely.geometry import mapping
from tqdm import tqdm
from mage_procgen.Utils.Utils import PolygonList, Point, TerrainData, LineStringList
from mage_procgen.Utils.Geometry import norm2d
from mage_procgen.Utils.Rendering import terrain_collection_name
from random import random

# TODO: find common paths with BaseRenderer
class RoadRenderer:
    _AssetsFolder = "Assets"
    _mesh_name = "Roads"
    _car_mesh_name = "Cars"

    def __init__(
        self, terrain_data: list[TerrainData], object_config, car_object_config
    ):
        self.config = object_config
        self.car_config = car_object_config
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

        # Cars
        filepath_car = os.path.realpath(
            os.path.join(
                _location, "..", self._AssetsFolder, self.car_config.geometry_node_file
            )
        )
        try:
            with bpy.data.libraries.load(filepath_car) as (data_from, data_to):
                data_to.node_groups = [self.car_config.geometry_node_name]
        except Exception as _:
            raise Exception(
                'Unable to load the Geometry Nodes setup with the name "'
                + self.car_config.geometry_node_name
                + '"'
                + "from the file "
                + filepath_car
            )

        self.car_geometry_node_name = data_to.node_groups[0].name

        self._terrain_data = terrain_data

    def render(
        self,
        polygons: PolygonList,
        geo_center: tuple[float, float, float],
        parent_collection_name: str,
        lanes: LineStringList,
        car_collection_name: str,
    ):
        mesh = bmesh.new()

        for polygon in tqdm(polygons):
            # Kind of hack because Polygon.coords is not implemented
            polygon_geometry = mapping(polygon)["coordinates"]
            points_coords = [
                (x[0], x[1], self.interpolate_z(x[0], x[1]))
                for x in polygon_geometry[0]
            ]

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

        m = mesh_obj.modifiers.new("", "NODES")
        m.node_group = D.node_groups[self.geometry_node_name]

        s = D.objects["Roads"].modifiers.new("", "SUBSURF")
        s.subdivision_type = "SIMPLE"
        s.levels = 3
        s.render_levels = 3

        sw = D.objects["Roads"].modifiers.new("", "SHRINKWRAP")
        sw.wrap_mode = "ABOVE_SURFACE"

        sw.target = D.collections[terrain_collection_name].objects[0]
        sw.offset = 0.05

        # Lanes
        car_mesh = bmesh.new()
        next_car_distance = self.next_car_distance()

        for lane in tqdm(lanes):

            previous_point = None

            for point in lane.coords:

                if previous_point is not None:

                    current_lane_vector = (
                        point[0] - previous_point[0],
                        point[1] - previous_point[1],
                    )

                    current_lane_vector_norm = norm2d(current_lane_vector)

                    place_car = current_lane_vector_norm > next_car_distance

                    while place_car:

                        # Place car using a vector along which we will align the car model
                        car_point = (
                            previous_point[0]
                            + next_car_distance
                            * current_lane_vector[0]
                            / current_lane_vector_norm,
                            previous_point[1]
                            + next_car_distance
                            * current_lane_vector[1]
                            / current_lane_vector_norm,
                        )

                        car_point_2 = (
                            previous_point[0]
                            + (next_car_distance + 2)
                            * current_lane_vector[0]
                            / current_lane_vector_norm,
                            previous_point[1]
                            + (next_car_distance + 2)
                            * current_lane_vector[1]
                            / current_lane_vector_norm,
                        )

                        points_coords = [
                            (x[0], x[1], self.interpolate_z(x[0], x[1]))
                            for x in [car_point, car_point_2]
                        ]

                        # Adapting the coordinates for rendering purposes
                        centered_points_coords = self.adapt_coords(
                            points_coords, geo_center
                        )

                        edge = car_mesh.edges.new(
                            car_mesh.verts.new(x) for x in centered_points_coords
                        )

                        # Advancing
                        next_car_distance = self.next_car_distance()
                        previous_point = car_point
                        current_lane_vector = (
                            point[0] - previous_point[0],
                            point[1] - previous_point[1],
                        )
                        current_lane_vector_norm = norm2d(current_lane_vector)
                        place_car = current_lane_vector_norm > next_car_distance

                    next_car_distance = next_car_distance - current_lane_vector_norm

                previous_point = point

        car_mesh_name = self._car_mesh_name
        car_mesh_data = D.meshes.new(car_mesh_name)
        car_mesh.to_mesh(car_mesh_data)
        car_mesh.free()
        car_mesh_obj = D.objects.new(car_mesh_data.name, car_mesh_data)
        car_mesh_obj.pass_index = self.car_config.tagging_index
        D.collections[car_collection_name].objects.link(car_mesh_obj)

        m = car_mesh_obj.modifiers.new("", "NODES")
        m.node_group = D.node_groups[self.car_geometry_node_name]

    def interpolate_z(self, x, y):
        """
        Finds the z coordinate corresponding to the (x,y) point in the input.
        Warning: Currently, it only returns the z coordinate of the point that is the lower left corner of the cell the input point is in.
        Since the terrain data has a 1m resolution, it is acceptable to do this instead of doing a bilinear interpolation.
        :param x: the x coordinate of the point
        :param y: the y coordinate of the point
        :return: the corresponding z coordinate of the point
        """

        current_terrain = None

        for terrain in self._terrain_data:
            is_point_in_terrain = True
            is_point_in_terrain &= x >= terrain.x_min
            is_point_in_terrain &= x < terrain.x_max
            is_point_in_terrain &= y >= terrain.y_min
            is_point_in_terrain &= y < terrain.y_max

            if is_point_in_terrain:
                current_terrain = terrain
                break

        if current_terrain is None:
            return 0
            # raise ValueError(
            #    "Point is outside of terrain: x=" + str(x) + ", y=" + str(y)
            # )

        point_offset_x = x - current_terrain.x_min
        point_offset_y = y - current_terrain.y_min

        # Index of the point in the grid to the lower left of the current point
        ll_index_x = int(point_offset_x / current_terrain.resolution)
        ll_index_y = 999 - int(point_offset_y / current_terrain.resolution)

        in_cell_offset_x = point_offset_x % current_terrain.resolution
        in_cell_offset_y = point_offset_y % current_terrain.resolution

        if ll_index_x == 999:
            # If x index is at max, we cannt use the point to its right for interpolation
            if ll_index_y == 999:
                # If y index is at max, we cannt use the point above for interpolation
                z_ll = current_terrain.data.values[ll_index_y][ll_index_x]

                return z_ll
            else:
                z_ll = current_terrain.data.values[ll_index_y][ll_index_x]
                z_ul = current_terrain.data.values[ll_index_y + 1][ll_index_x]

                return (
                    in_cell_offset_y * z_ul + (1 - in_cell_offset_y) * z_ll
                ) / current_terrain.resolution
        elif ll_index_y == 999:
            # If y index is at max, we cannt use the point above for interpolation
            z_ll = current_terrain.data.values[ll_index_y][ll_index_x]
            z_lr = current_terrain.data.values[ll_index_y][ll_index_x + 1]

            return (
                in_cell_offset_x * z_lr + (1 - in_cell_offset_x) * z_ll
            ) / current_terrain.resolution
        else:
            z_ll = current_terrain.data.values[ll_index_y][ll_index_x]
            z_ul = current_terrain.data.values[ll_index_y + 1][ll_index_x]
            z_ur = current_terrain.data.values[ll_index_y + 1][ll_index_x + 1]
            z_lr = current_terrain.data.values[ll_index_y][ll_index_x + 1]

            z_l = (
                in_cell_offset_x * z_lr + (1 - in_cell_offset_x) * z_ll
            ) / current_terrain.resolution
            z_u = (
                in_cell_offset_x * z_ur + (1 - in_cell_offset_x) * z_ul
            ) / current_terrain.resolution

            return (
                in_cell_offset_y * z_u + (1 - in_cell_offset_y) * z_l
            ) / current_terrain.resolution

    def adapt_coords(
        self, points_coords: list[Point], geo_center: Point
    ) -> list[Point]:

        # Centering the coordinates so that Blender's internal precision is less impactful
        centered_points_coords = [
            (x[0] - geo_center[0], x[1] - geo_center[1], x[2] - geo_center[2])
            for x in points_coords
        ]

        return centered_points_coords

    def next_car_distance(self):
        # TODO: improve this with better distribution
        return 20 + 10 * random()

    def clear_object(self):

        D.objects.remove(D.objects[self._mesh_name], do_unlink=True)
        D.meshes.remove(D.meshes[self._mesh_name], do_unlink=True)

        D.objects.remove(D.objects[self._car_mesh_name], do_unlink=True)
        D.meshes.remove(D.meshes[self._car_mesh_name], do_unlink=True)
