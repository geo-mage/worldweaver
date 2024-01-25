bl_info = {
    "name": "MAGE Procgen",
    "blender": (3, 5, 0),
    "category": "Object",
}

import os
import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import Operator, AddonPreferences
from bpy_extras.io_utils import ImportHelper

# store keymaps here to access after registration
addon_keymaps = []


class MageProcgenAddonPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    filepath: StringProperty(
        name="Configuration File Path",
        subtype="FILE_PATH",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="MAGE Procgen Preferences:")
        layout.prop(self, "filepath")


class ObjectMageProcgenConfigSelect(bpy.types.Operator, ImportHelper):
    """Object Mage Procgen Config Select"""

    bl_idname = "object.mage_procgen_config_select"
    bl_label = "Mage Procgen Config Select"
    bl_options = {"REGISTER", "UNDO"}
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        """Custom invoke to be able to set the base filepath"""
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        self.filepath = addon_prefs.filepath

        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Change the configuration file for MAGE Procgen"""
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        addon_prefs.filepath = self.filepath

        bpy.ops.wm.save_userpref()
        print("Configuration file changed to: ", addon_prefs.filepath)

        return {"FINISHED"}


def menu_func_config_select(self, context):
    self.layout.operator(ObjectMageProcgenConfigSelect.bl_idname)


class ObjectMageProcgen(bpy.types.Operator):
    """Object Mage Procgen"""

    bl_idname = "object.mage_procgen"
    bl_label = "Mage Procgen"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from mage_procgen import main as mpm

        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        print("Using config file: ", addon_prefs.filepath)
        mpm.main(addon_prefs.filepath)

        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(ObjectMageProcgen.bl_idname)


def register():
    bpy.utils.register_class(MageProcgenAddonPreferences)

    bpy.utils.register_class(ObjectMageProcgen)
    bpy.types.VIEW3D_MT_object.append(menu_func)

    bpy.utils.register_class(ObjectMageProcgenConfigSelect)
    bpy.types.VIEW3D_MT_object.append(menu_func_config_select)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name="Object Mode", space_type="EMPTY")
        kmi = km.keymap_items.new(
            ObjectMageProcgen.bl_idname, "M", "PRESS", ctrl=True, shift=True
        )
        addon_keymaps.append((km, kmi))

        km2 = wm.keyconfigs.addon.keymaps.new(name="Object Mode", space_type="EMPTY")
        kmi2 = km2.keymap_items.new(
            ObjectMageProcgenConfigSelect.bl_idname, "L", "PRESS", ctrl=True, shift=True
        )
        addon_keymaps.append((km2, kmi2))


def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(ObjectMageProcgenConfigSelect)
    bpy.types.VIEW3D_MT_object.remove(menu_func_config_select)

    bpy.utils.unregister_class(ObjectMageProcgen)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

    bpy.utils.unregister_class(MageProcgenAddonPreferences)


if __name__ == "__main__":
    register()
