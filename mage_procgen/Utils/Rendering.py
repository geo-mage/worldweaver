from bpy import context as C


def configure_render():
    for a in C.screen.areas:
        if a.type == "VIEW_3D":
            for s in a.spaces:
                if s.type == "VIEW_3D":
                    s.clip_end = 100000
                    s.shading.type = "MATERIAL"
