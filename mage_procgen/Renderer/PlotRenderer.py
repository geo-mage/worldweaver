from mage_procgen.Renderer.BaseRenderer import BaseRenderer


class FenceRenderer(BaseRenderer):
    _GNSetup = "Fences"
    _GNFile = "Fences.blend"
    _mesh_name = "Fences"


class GardenRenderer(BaseRenderer):
    _GNSetup = "Gardens"
    _GNFile = "Gardens.blend"
    _mesh_name = "Gardens"


class FieldRenderer(BaseRenderer):
    _GNSetup = "Fields"
    _GNFile = "Fields.blend"
    _mesh_name = "Fields"
