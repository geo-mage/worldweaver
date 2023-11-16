from bpy import data as D

from mage_procgen.Renderer.BaseRenderer import BaseRenderer
from mage_procgen.Utils.Utils import TerrainData


class ForestRenderer(BaseRenderer):
    _mesh_name = "Forest"

    def __init__(self, terrain_data: list[TerrainData], object_config):
        super().__init__(terrain_data, object_config)

        # Need to bind the forest geometry node to the terrain collection so that trees are neither floating nor underground
        # D.node_groups[self.geometry_node_name].nodes["Collection Info"].inputs[
        #    0
        # ].default_value = D.collections["Terrain"]
