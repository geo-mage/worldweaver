bl_info = {
    "name": "MAGE Procgen",
    "blender": (3, 5, 0),
    "category": "Object",
}

import bpy


class ObjectMageProcgen(bpy.types.Operator):
    """Object Mage Procgen"""

    bl_idname = "object.mage_procgen"
    bl_label = "Mage Procgen"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from mage_procgen import main as mpm

        mpm.main()

        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(ObjectMageProcgen.bl_idname)


# store keymaps here to access after registration
addon_keymaps = []


def register():
    bpy.utils.register_class(ObjectMageProcgen)
    bpy.types.VIEW3D_MT_object.append(menu_func)

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


def unregister():
    # Note: when unregistering, it's usually good practice to do it in reverse order you registered.
    # Can avoid strange issues like keymap still referring to operators already unregistered...
    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(ObjectMageProcgen)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    register()
