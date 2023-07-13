from mage_procgen.Renderer.BaseRenderer import BaseRenderer
from mage_procgen.Utils.Config import RenderObjectConfig
from mage_procgen.Utils.Rendering import hex_color_to_tuple
from bpy import data as D


class TaggingRenderer(BaseRenderer):
    def __init__(self, terrain_data, color_code):
        object_config = RenderObjectConfig(
            geometry_node_file="Tagging.blend", geometry_node_name="Tagging"
        )
        super().__init__(terrain_data, object_config)
        color_tuple = hex_color_to_tuple(color_code)

        tagging_material = (
            D.node_groups[self.geometry_node_name]
            .nodes["Set Material"]
            .inputs[2]
            .default_value
        )
        tagging_material.node_tree.nodes["Principled BSDF"].inputs[
            0
        ].default_value = color_tuple


class TaggingBackgroundRenderer(TaggingRenderer):
    _mesh_name = "TaggingBackground"


class TaggingBuildingRenderer(TaggingRenderer):
    _mesh_name = "TaggingBuilding"


class TaggingRoadsRenderer(TaggingRenderer):
    _mesh_name = "TaggingRoads"


class TaggingWaterRenderer(TaggingRenderer):
    _mesh_name = "TaggingWater"
