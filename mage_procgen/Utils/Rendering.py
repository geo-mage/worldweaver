from bpy import context as C


def configure_render():
    for a in C.screen.areas:
        if a.type == "VIEW_3D":
            for s in a.spaces:
                if s.type == "VIEW_3D":
                    # Setting clip end distance to avoid the object disappearing when the camera is moved
                    s.clip_end = 100000

                    # Setting the shading type to avoid setting it manually every time
                    s.shading.type = "MATERIAL"
