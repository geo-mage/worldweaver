import os
import math
from bpy import context as C, data as D, ops as O
from datetime import datetime

import random

import mage_procgen.Utils.DataFiles as df


rendering_collection_name = "Rendering"
terrain_collection_name = "Terrain"
cars_collection_name = "Cars"
buildings_collection_name = "Buildings"
base_collection_name = "Collection"


def configure_render(geo_center_deg):
    for a in C.screen.areas:
        if a.type == "VIEW_3D":
            for s in a.spaces:
                if s.type == "VIEW_3D":
                    # Setting clip end distance because our scene is very large
                    s.clip_end = 100000

                    # Setting the shading type
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

    # Ortho Camera
    camera_data = D.cameras.new(name="Camera_Ortho")
    camera_object = D.objects.new("Camera_Ortho", camera_data)
    D.collections[base_collection_name].objects.link(camera_object)
    camera_data.type = "ORTHO"
    camera_data.clip_end = 100000
    camera_object.location = (0, 0, 1100)
    camera_object.rotation_euler = (0, 0, 0)
    camera_data.ortho_scale = 200

    # Rendering
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.cycles.samples = 50

    # Preparing collections
    rendering_collection = D.collections.new(rendering_collection_name)
    D.collections[base_collection_name].children.link(rendering_collection)

    terrain_collection = D.collections.new(terrain_collection_name)
    D.collections[rendering_collection_name].children.link(terrain_collection)

    cars_collection = D.collections.new(cars_collection_name)
    D.collections[rendering_collection_name].children.link(cars_collection)

    buildings_collection = D.collections.new(buildings_collection_name)
    D.collections[rendering_collection_name].children.link(buildings_collection)


def setup_export_folder(base_folder, departement):
    now = datetime.now()
    now_str = now.strftime("%Y_%m_%d:%H:%M")

    base_path = os.path.join(base_folder, df.rendering, departement, now_str)
    os.makedirs(base_path, exist_ok=True)
    return base_path


# TODO: move out of here when we know better what it should do
def export_rendered_img(base_path, base_name):
    sc = C.scene

    sc.render.filepath = os.path.join(base_path, base_name + ".png")

    O.render.render(write_still=True)


def setup_img_persp(resolution, pixel_size, center):

    sc = C.scene
    sc.render.resolution_x = resolution
    sc.render.resolution_y = resolution

    camera = D.objects["Camera"]
    sc.camera = camera
    img_size = resolution * pixel_size
    camera_elevation = img_size / (2 * math.tan(camera.data.angle / 2))

    max_z = -math.inf

    # Calculating the maximum height of the scene, using terrain and buildings
    # TODO: check if there are edge cases where this does not hold
    terrain_collection = D.collections["Terrain"].objects
    for terrain in terrain_collection:
        terrain_box = terrain.bound_box
        z_coords = [v[2] for v in terrain_box]
        cur_z_max = max(z_coords)
        if cur_z_max > max_z:
            max_z = cur_z_max

    camera.location = (center[0], center[1], max_z + camera_elevation)


def setup_img_ortho(size_x, size_y, pixel_size, center):
    sc = C.scene
    sc.render.resolution_x = size_x // pixel_size
    sc.render.resolution_y = size_y // pixel_size

    size = max(size_x, size_y)

    camera = D.objects["Camera_Ortho"]
    sc.camera = camera
    camera.data.ortho_scale = size

    max_z = -math.inf

    # Calculating the maximum height of the scene, using terrain and buildings
    # TODO: check if there are edge cases where this does not hold
    terrain_collection = D.collections["Terrain"].objects
    for terrain in terrain_collection:
        terrain_box = terrain.bound_box
        z_coords = [v[2] for v in terrain_box]
        cur_z_max = max(z_coords)
        if cur_z_max > max_z:
            max_z = cur_z_max

    camera_z = max_z + 50

    camera.location = (center[0], center[1], max_z + 50)

    return camera_z


def setup_img_ortho_res(resolution, pixel_size, center):
    sc = C.scene
    sc.render.resolution_x = resolution
    sc.render.resolution_y = resolution

    size = resolution * pixel_size

    camera = D.objects["Camera_Ortho"]
    sc.camera = camera
    camera.data.ortho_scale = size

    max_z = -math.inf

    # Calculating the maximum height of the scene, using terrain and buildings
    # TODO: check if there are edge cases where this does not hold
    terrain_collection = D.collections["Terrain"].objects
    for terrain in terrain_collection:
        terrain_box = terrain.bound_box
        z_coords = [v[2] for v in terrain_box]
        cur_z_max = max(z_coords)
        if cur_z_max > max_z:
            max_z = cur_z_max

    camera_z = max_z + 50

    camera.location = (center[0], center[1], max_z + 50)

    return camera_z


def setup_compositing_height_map(base_folder: str):

    # Enabling compositing nodes
    D.scenes["Scene"].use_nodes = True

    # Enabling Z pass to be able to get the heightmap
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_z = True

    # Disabling object index pass (will need to be reactivated if we want to take objects other than terrain into account)
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_object_index = False

    # Adding the nodes to the node tree to get the setup we want
    scene = C.scene
    nodes = scene.node_tree.nodes
    nodes.clear()
    r_layers = nodes.new("CompositorNodeRLayers")

    # Depth map as an EXR file
    output_file = nodes.new("CompositorNodeOutputFile")
    output_file.format.file_format = "OPEN_EXR"
    output_file.base_path = os.path.join(base_folder, df.rendering, df.temp_folder)
    output_file.file_slots.remove(output_file.inputs[0])
    output_file.file_slots.new("depth_map")

    # Linking it
    links = scene.node_tree.links
    link = links.new(nodes["Render Layers"].outputs[2], output_file.inputs[0])


def setup_compositing_semantic_map(base_folder: str):
    # Enabling compositing nodes
    D.scenes["Scene"].use_nodes = True

    # Disabling Z pass
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_z = False

    # Enabling object index pass to get the semantic map
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_object_index = True

    # Adding the nodes to the node tree to get the setup we want
    scene = C.scene
    nodes = scene.node_tree.nodes
    nodes.clear()
    r_layers = nodes.new("CompositorNodeRLayers")

    # Semantic map as a greyscale PNG
    output_file = nodes.new("CompositorNodeOutputFile")
    output_file.format.file_format = "PNG"
    output_file.format.color_mode = "BW"
    output_file.format.color_depth = "8"
    output_file.base_path = os.path.join(base_folder, df.rendering, df.temp_folder)
    output_file.file_slots.remove(output_file.inputs[0])
    output_file.file_slots.new("semantic_map")

    # Linking it
    norm = nodes.new("CompositorNodeNormalize")
    links = scene.node_tree.links
    link = links.new(nodes["Render Layers"].outputs[2], norm.inputs[0])
    link2 = links.new(norm.outputs[0], output_file.inputs[0])


def setup_compositing_render(folder):

    # Enabling compositing nodes
    D.scenes["Scene"].use_nodes = use_nodes = True

    # Disabling Z pass
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_z = False

    # Enabling object index pass to get the semantic map
    D.scenes["Scene"].view_layers["ViewLayer"].use_pass_object_index = True

    # Adding the nodes to the node tree to get the setup we want
    scene = C.scene
    nodes = scene.node_tree.nodes
    nodes.clear()
    r_layers = nodes.new("CompositorNodeRLayers")

    # Semantic map as a greyscale PNG
    output_file = nodes.new("CompositorNodeOutputFile")
    output_file.format.file_format = "PNG"
    output_file.format.color_mode = "BW"
    output_file.format.color_depth = "8"
    output_file.base_path = folder

    # Linking it
    norm = nodes.new("CompositorNodeNormalize")
    links = scene.node_tree.links
    link = links.new(nodes["Render Layers"].outputs[2], norm.inputs[0])
    link2 = links.new(norm.outputs[0], output_file.inputs[0])


def set_compositing_render_image_name(image_name):

    # The file name is tied to the input name of the node.
    # So we have to delete the previous input, add another one, and relink it to the correct node
    output_file = D.scenes["Scene"].node_tree.nodes["File Output"]
    output_file.file_slots.remove(output_file.inputs[0])
    output_file.file_slots.new(image_name)
    norm = D.scenes["Scene"].node_tree.nodes["Normalize"]
    links = D.scenes["Scene"].node_tree.links
    link2 = links.new(norm.outputs[0], output_file.inputs[0])
