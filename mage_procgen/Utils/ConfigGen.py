"""
    Module to create and edit configuration file for the application
"""

import os
import dataclasses
from mage_procgen.Loader.ConfigLoader import ConfigLoader
from mage_procgen.Utils.Config import Config, GeoWindowConfig
from mage_procgen.Utils.DataFiles import config_folder, default_config_file


def generate_config(new_file_name: str, **kwargs):
    """
    Generate a configuration file from another configuration and saves it as 'new_file_name'

    Parameters:
        new_file_name: The name of the new configuration file
        kwargs: Parameters of the config that will be changed from the base configuration. All are optionnal. Accepted parameters are:

    Other parameters: File parameters:
        from_file (str): The name of the base configuration from which the new configuration will be created. If ommited, it will be the default configuration provided with the software.
        base_folder (str): The name of the base folder of the application, in which all data will be found

    Other parameters: Render window parameters:
        window_type (str): Type of definition used for the window. Can be "COORDS", "TOWN" or "FILE"
        window_x_min (float): Min X of the render window. Only used if window type is "COORDS"
        window_y_min (float): Min Y of the render window. Only used if window type is "COORDS"
        window_x_max (float): Max X of the render window. Only used if window type is "COORDS"
        window_y_max (float): Max Y of the render window. Only used if window type is "COORDS"
        window_from_crs (int): CRS code the xmin, xmax, ymin and ymax are given. Only used if window type is "COORDS"
        town_dpt (int): Number of the departement in which the town is. Only used if window type is "TOWN"
        town_name (str): Name of the town that will determine the render window. Only used if window type is "TOWN"
        window_shapefile (str): File name of the file that will define the render window. Only used if window type is "FILE"

    Other parameters: Render parameters:
        terrain_resolution (float): Spatial resolution of the terrain in the render.
        use_sat_img (bool): If True, will use BDORTHO images as texture for the terrain. If false, will use a base texture.

    Other parameters: Flood parameters:
        flood (bool): If True, will generate a flood on the scene.
        flood_height (float): Only used if flood is True. Height of the flood in meters
        flood_cell_size (float): Only used if flood is True. Spatial resolution of the flood

    Other parameters: Output parameters:
        export_img (bool): If True, will generate png files from the scene. If False, will show all the buildings, cars, trees etc in the whole render scene.
        use_camera_ortho (bool): If True, will use orthographic camera for renders. If False, will use a perspective camera
        out_img_resolution (int): Resolution of the output images
        out_img_pixel_size (float): Size of a pixel, in m.

    Other parameters: Assets for Normal buildings:
        building_render_config_geometry_node_file (str): Name of the asset file for normal buildings
        building_render_config_geometry_node_name (str): Name of the geometry node setup for normal buildings
        building_render_config_tagging_index (int): Index using which normal buildings will be tagged in the semantic map

    Other parameters: Assets for Churches:
        church_render_config_geometry_node_file (str): Name of the asset file for churches
        church_render_config_geometry_node_name (str): Name of the geometry node setup for churches
        church_render_config_tagging_index (int): Index using which churches will be tagged in the semantic map

    Other parameters: Assets for Factories:
        factory_render_config_geometry_node_file (str): Name of the asset file for factories
        factory_render_config_geometry_node_name (str): Name of the geometry node setup for factories
        factory_render_config_tagging_index (int): Index using which factories will be tagged in the semantic map

    Other parameters: Assets for Malls:
        mall_render_config_geometry_node_file (str): Name of the asset file for malls
        mall_render_config_geometry_node_name (str): Name of the geometry node setup for malls
        mall_render_config_tagging_index (int): Index using which malls will be tagged in the semantic map

    Other parameters: Assets for Flood:
        flood_render_config_geometry_node_file (str): Name of the asset file for the flood
        flood_render_config_geometry_node_name (str): Name of the geometry node setup for the flood
        flood_render_config_tagging_index (int): Index using which the flood will be tagged in the semantic map

    Other parameters: Assets for Forests:
        forest_render_config_geometry_node_file (str): Name of the asset file for forests
        forest_render_config_geometry_node_name (str): Name of the geometry node setup for forests
        forest_render_config_tagging_index (int): Index using which forests will be tagged in the semantic map

    Other parameters: Assets for Roads:
        road_render_config_geometry_node_file (str): Name of the asset file for roads
        road_render_config_geometry_node_name (str): Name of the geometry node setup for roads
        road_render_config_tagging_index (int): Index using which roads will be tagged in the semantic map

    Other parameters: Assets for Water:
        water_render_config_geometry_node_file (str): Name of the asset file for water
        water_render_config_geometry_node_name (str): Name of the geometry node setup for water
        water_render_config_tagging_index (int): Index using which water will be tagged in the semantic map

    Other parameters: Assets for Cars:
        car_render_config_geometry_node_file (str): Name of the asset file for cars
        car_render_config_geometry_node_name (str): Name of the geometry node setup for cars
        car_render_config_tagging_index (int): Index using which cars will be tagged in the semantic map
    """
    _location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    default_config_filepath = os.path.realpath(
        os.path.join(_location, "..", config_folder, default_config_file)
    )

    base_config_file = kwargs.get("from_file", default_config_filepath)
    base_config = ConfigLoader.load(base_config_file)
    new_config = dataclasses.replace(base_config)

    new_config.base_folder = kwargs.get("base_folder", base_config.base_folder)

    # Window
    new_config.window_type = kwargs.get("window_type", base_config.window_type)
    new_geo_window = GeoWindowConfig(
        kwargs.get("window_x_min", base_config.geo_window.x_min),
        kwargs.get("window_y_min", base_config.geo_window.y_min),
        kwargs.get("window_x_max", base_config.geo_window.x_max),
        kwargs.get("window_y_max", base_config.geo_window.y_max),
        kwargs.get("window_from_crs", base_config.geo_window.crs_from),
    )
    new_config.geo_window = new_geo_window
    new_config.town_dpt = kwargs.get("town_dpt", base_config.town_dpt)
    new_config.town_name = kwargs.get("town_name", base_config.town_name)
    new_config.window_shapefile = kwargs.get(
        "window_shapefile", base_config.window_shapefile
    )

    # Render params
    new_config.terrain_resolution = kwargs.get(
        "terrain_resolution", base_config.terrain_resolution
    )
    new_config.use_sat_img = kwargs.get("use_sat_img", base_config.use_sat_img)

    # Flood
    new_config.flood = kwargs.get("flood", base_config.flood)
    new_config.flood_height = kwargs.get("flood_height", base_config.flood_height)
    new_config.flood_cell_size = kwargs.get(
        "flood_cell_size", base_config.flood_cell_size
    )

    # Output
    new_config.export_img = kwargs.get("export_img", base_config.export_img)
    new_config.use_camera_ortho = kwargs.get(
        "use_camera_ortho", base_config.use_camera_ortho
    )
    new_config.out_img_resolution = kwargs.get(
        "out_img_resolution", base_config.out_img_resolution
    )
    new_config.out_img_pixel_size = kwargs.get(
        "out_img_pixel_size", base_config.out_img_pixel_size
    )

    ## Assets
    # Buildings
    new_config.building_render_config.geometry_node_file = kwargs.get(
        "building_render_config_geometry_node_file",
        base_config.building_render_config.geometry_node_file,
    )
    new_config.building_render_config.geometry_node_name = kwargs.get(
        "building_render_config_geometry_node_name",
        base_config.building_render_config.geometry_node_name,
    )
    new_config.building_render_config.tagging_index = kwargs.get(
        "building_render_config_tagging_index",
        base_config.building_render_config.tagging_index,
    )

    # Churches
    new_config.church_render_config.geometry_node_file = kwargs.get(
        "church_render_config_geometry_node_file",
        base_config.church_render_config.geometry_node_file,
    )
    new_config.church_render_config.geometry_node_name = kwargs.get(
        "church_render_config_geometry_node_name",
        base_config.church_render_config.geometry_node_name,
    )
    new_config.church_render_config.tagging_index = kwargs.get(
        "church_render_config_tagging_index",
        base_config.church_render_config.tagging_index,
    )

    # Factories
    new_config.factory_render_config.geometry_node_file = kwargs.get(
        "factory_render_config_geometry_node_file",
        base_config.factory_render_config.geometry_node_file,
    )
    new_config.factory_render_config.geometry_node_name = kwargs.get(
        "factory_render_config_geometry_node_name",
        base_config.factory_render_config.geometry_node_name,
    )
    new_config.factory_render_config.tagging_index = kwargs.get(
        "factory_render_config_tagging_index",
        base_config.factory_render_config.tagging_index,
    )

    # Malls
    new_config.mall_render_config.geometry_node_file = kwargs.get(
        "mall_render_config_geometry_node_file",
        base_config.mall_render_config.geometry_node_file,
    )
    new_config.mall_render_config.geometry_node_name = kwargs.get(
        "mall_render_config_geometry_node_name",
        base_config.mall_render_config.geometry_node_name,
    )
    new_config.mall_render_config.tagging_index = kwargs.get(
        "mall_render_config_tagging_index",
        base_config.mall_render_config.tagging_index,
    )

    # Flood
    new_config.flood_render_config.geometry_node_file = kwargs.get(
        "flood_render_config_geometry_node_file",
        base_config.flood_render_config.geometry_node_file,
    )
    new_config.flood_render_config.geometry_node_name = kwargs.get(
        "flood_render_config_geometry_node_name",
        base_config.flood_render_config.geometry_node_name,
    )
    new_config.flood_render_config.tagging_index = kwargs.get(
        "flood_render_config_tagging_index",
        base_config.flood_render_config.tagging_index,
    )

    # Forests
    new_config.forest_render_config.geometry_node_file = kwargs.get(
        "forest_render_config_geometry_node_file",
        base_config.forest_render_config.geometry_node_file,
    )
    new_config.forest_render_config.geometry_node_name = kwargs.get(
        "forest_render_config_geometry_node_name",
        base_config.forest_render_config.geometry_node_name,
    )
    new_config.forest_render_config.tagging_index = kwargs.get(
        "forest_render_config_tagging_index",
        base_config.forest_render_config.tagging_index,
    )

    # Road
    new_config.road_render_config.geometry_node_file = kwargs.get(
        "road_render_config_geometry_node_file",
        base_config.road_render_config.geometry_node_file,
    )
    new_config.road_render_config.geometry_node_name = kwargs.get(
        "road_render_config_geometry_node_name",
        base_config.road_render_config.geometry_node_name,
    )
    new_config.road_render_config.tagging_index = kwargs.get(
        "road_render_config_tagging_index",
        base_config.road_render_config.tagging_index,
    )

    # Water
    new_config.water_render_config.geometry_node_file = kwargs.get(
        "water_render_config_geometry_node_file",
        base_config.water_render_config.geometry_node_file,
    )
    new_config.water_render_config.geometry_node_name = kwargs.get(
        "water_render_config_geometry_node_name",
        base_config.water_render_config.geometry_node_name,
    )
    new_config.water_render_config.tagging_index = kwargs.get(
        "water_render_config_tagging_index",
        base_config.water_render_config.tagging_index,
    )

    # Flood
    new_config.car_render_config.geometry_node_file = kwargs.get(
        "car_render_config_geometry_node_file",
        base_config.car_render_config.geometry_node_file,
    )
    new_config.car_render_config.geometry_node_name = kwargs.get(
        "car_render_config_geometry_node_name",
        base_config.car_render_config.geometry_node_name,
    )
    new_config.car_render_config.tagging_index = kwargs.get(
        "car_render_config_tagging_index",
        base_config.car_render_config.tagging_index,
    )

    ConfigLoader.save(new_config, new_file_name)
    print("New config file generated at ", new_file_name)


def set_window_coords(
    new_file_name: str,
    window_x_min: float,
    window_y_min: float,
    window_x_max: float,
    window_y_max: float,
    window_from_crs: int,
    from_file: str = None,
):
    """
    Changes the config to use coordinates to define the render window and saves it at 'new_file_name'.
    Base configuration will be the one in 'from_file' if provided, or the base configuration if not.

    Parameters:
        new_file_name: Name of the new configuration file
        window_x_min: Min X of the render window.
        window_y_min: Min Y of the render window.
        window_x_max: Max X of the render window.
        window_y_max: ax Y of the render window.
        window_from_crs: CRS code the xmin, xmax, ymin and ymax are given.
        from_file: Optional. Name of the base configuration.
    """
    if from_file is not None:
        generate_config(
            new_file_name,
            from_file=from_file,
            window_type="COORDS",
            window_x_min=window_x_min,
            window_y_min=window_y_min,
            window_x_max=window_x_max,
            window_y_max=window_y_max,
            window_from_crs=window_from_crs,
        )
    else:
        generate_config(
            new_file_name,
            window_type="COORDS",
            window_x_min=window_x_min,
            window_y_min=window_y_min,
            window_x_max=window_x_max,
            window_y_max=window_y_max,
            window_from_crs=window_from_crs,
        )


def set_window_town(
    new_file_name: str, town_dpt: int, town_name: str, from_file: str = None
):
    """
    Changes the config to use town shape to define the render window and saves it at 'new_file_name'.
    Base configuration will be the one in 'from_file' if provided, or the base configuration if not.

    Parameters:
        new_file_name: Name of the new configuration file
        town_dpt: Number of the departement in which the town is. Only used if window type is "TOWN"
        town_name: Name of the town that will determine the render window. Only used if window type is "TOWN"
        from_file: Optional. Name of the base configuration.
    """
    if from_file is not None:
        generate_config(
            new_file_name,
            from_file=from_file,
            window_type="TOWN",
            town_dpt=town_dpt,
            town_name=town_name,
        )
    else:
        generate_config(
            new_file_name,
            window_type="TOWN",
            town_dpt=town_dpt,
            town_name=town_name,
        )


def set_window_file(new_file_name: str, window_shapefile: str, from_file: str = None):
    """
    Changes the config to use town shape to define the render window and saves it at 'new_file_name'.
    Base configuration will be the one in 'from_file' if provided, or the base configuration if not.

    Parameters:
        new_file_name: Name of the new configuration file
        window_shapefile: File name of the file that will define the render window.
        from_file: Optional. Name of the base configuration.
    """
    if from_file is not None:
        generate_config(
            new_file_name,
            from_file=from_file,
            window_type="FILE",
            window_shapefile=window_shapefile,
        )
    else:
        generate_config(
            new_file_name, window_type="FILE", window_shapefile=window_shapefile
        )


def set_geometry_node(
    new_file_name: str,
    object_type: str,
    geometry_node_file: str,
    geometry_node_name: str,
    from_file: str = None,
):
    """
    Changes the geometry node asset file or geometry nodes setup name of an object type in a config file and saves it at 'new_file_name'.
    Base configuration will be the one in 'from_file' if provided, or the base configuration if not.

    Parameters:
        new_file_name: Name of the new configuration file
        object_type: Type of object affected by the change. Can only be one of:
            "BUILDING",
            "CHURCH",
            "FACTORY",
            "MALL",
            "FLOOD",
            "FOREST",
            "ROAD",
            "WATER",
            "CAR"
        geometry_node_file: Name of the blender asset file in which the geometrynodes setup is
        geometry_node_name: Name of the geometrynodes setup
        from_file: Optional. Name of the base configuration.
    """

    match object_type:
        case "BUILDING":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    building_render_config_geometry_node_file=geometry_node_file,
                    building_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    building_render_config_geometry_node_file=geometry_node_file,
                    building_render_config_geometry_node_name=geometry_node_name,
                )
        case "CHURCH":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    church_render_config_geometry_node_file=geometry_node_file,
                    church_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    church_render_config_geometry_node_file=geometry_node_file,
                    church_render_config_geometry_node_name=geometry_node_name,
                )
        case "FACTORY":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    factory_render_config_geometry_node_file=geometry_node_file,
                    factory_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    factory_render_config_geometry_node_file=geometry_node_file,
                    factory_render_config_geometry_node_name=geometry_node_name,
                )
        case "MALL":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    mall_render_config_geometry_node_file=geometry_node_file,
                    mall_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    mall_render_config_geometry_node_file=geometry_node_file,
                    mall_render_config_geometry_node_name=geometry_node_name,
                )
        case "FLOOD":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    flood_render_config_geometry_node_file=geometry_node_file,
                    flood_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    flood_config_geometry_node_file=geometry_node_file,
                    flood_config_geometry_node_name=geometry_node_name,
                )
        case "FOREST":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    forest_render_config_geometry_node_file=geometry_node_file,
                    forest_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    forest_render_config_geometry_node_file=geometry_node_file,
                    forest_render_config_geometry_node_name=geometry_node_name,
                )
        case "ROAD":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    road_render_config_geometry_node_file=geometry_node_file,
                    road_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    road_render_config_geometry_node_file=geometry_node_file,
                    road_render_config_geometry_node_name=geometry_node_name,
                )
        case "WATER":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    water_render_config_geometry_node_file=geometry_node_file,
                    water_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    water_render_config_geometry_node_file=geometry_node_file,
                    water_render_config_geometry_node_name=geometry_node_name,
                )
        case "CAR":
            if from_file is not None:
                generate_config(
                    new_file_name,
                    from_file=from_file,
                    car_render_config_geometry_node_file=geometry_node_file,
                    car_render_config_geometry_node_name=geometry_node_name,
                )
            else:
                generate_config(
                    new_file_name,
                    car_render_config_geometry_node_file=geometry_node_file,
                    car_render_config_geometry_node_name=geometry_node_name,
                )
