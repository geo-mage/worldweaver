from mage_procgen.Renderer.BaseRenderer import BaseRenderer
from mage_procgen.Utils.Utils import Point


class BuildingRenderer(BaseRenderer):
    _GNSetup = "Buildings"
    _GNFile = "Buildings.blend"
    _mesh_name = "Buildings"

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
