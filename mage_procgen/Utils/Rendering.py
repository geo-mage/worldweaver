import os
import math
from bpy import context as C, data as D, ops as O
from datetime import datetime


def configure_render(geo_center_deg):
    for a in C.screen.areas:
        if a.type == "VIEW_3D":
            for s in a.spaces:
                if s.type == "VIEW_3D":
                    # Setting clip end distance to avoid the object disappearing when the camera is moved
                    s.clip_end = 100000

                    # Setting the shading type to avoid setting it manually every time
                    s.shading.type = "RENDERED"

    # Sun and lighting
    sun = D.objects["Light"]
    sun.data.type = "SUN"
    sun.data.energy = 10

    sc = C.scene
    sc.sun_pos_properties.sun_object = sun
    sc.sun_pos_properties.latitude = geo_center_deg[1]
    sc.sun_pos_properties.longitude = geo_center_deg[0]
    sc.sun_pos_properties.UTC_zone = 2
    sc.sun_pos_properties.time = 12

    # Camera
    camera = D.objects["Camera"]
    camera.location = (0, 0, 1100)
    camera.rotation_euler = (0, 0, 0)
    camera.data.clip_end = 100000
    camera.data.lens_unit = "FOV"
    camera.data.angle = 10 * math.pi / 180

    # Rendering
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.cycles.samples = 50


# TODO: move out of here when we know better what it should do
def export_rendered_img():
    sc = C.scene

    now = datetime.now()
    now_str = now.strftime("%Y_%m_%d:%H:%M:%S:%f")

    base_path = "/home/verstraa/Work/maps/rendering/77/"

    sc.render.filepath = os.path.join(base_path, now_str + ".png")

    O.render.render("INVOKE_DEFAULT", write_still=True)


def setup_img(resolution, pixel_size, center):

    sc = C.scene
    sc.render.resolution_x = resolution
    sc.render.resolution_y = resolution

    camera = D.objects["Camera"]

    img_size = resolution * pixel_size
    camera_elevation = img_size / (2 * math.tan(camera.data.angle / 2))

    camera.location = (center[0], center[1], camera_elevation)
