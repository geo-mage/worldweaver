from mage_procgen.Renderer.BaseRenderer import BaseRenderer


class GardenRenderer(BaseRenderer):

    _GNSetup = "Fences"
    _GNFile = "Fences.blend"
    _mesh_name = "Gardens"


class FieldsRenderer(BaseRenderer):

    _GNSetup = "Fields"
    _GNFile = "Fields.blend"
    _mesh_name = "Fields"

