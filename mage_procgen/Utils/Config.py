from dataclasses import dataclass

window_type_coords = "COORDS"
window_type_town = "TOWN"
window_type_file = "FILE"


@dataclass
class RenderObjectConfig:
    geometry_node_file: str
    geometry_node_name: str
    tagging_index: int


@dataclass
class GeoWindowConfig:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    crs_from: int


@dataclass
class Config:
    base_folder: str
    window_type: str
    geo_window: GeoWindowConfig
    town_dpt: int
    town_name: str
    window_shapefile: str
    terrain_resolution: float
    use_sat_img: bool
    flood: bool
    flood_height: float
    flood_cell_size: float
    export_img: bool
    use_camera_ortho: bool
    out_img_resolution: int
    out_img_pixel_size: float
    building_render_config: RenderObjectConfig
    church_render_config: RenderObjectConfig
    factory_render_config: RenderObjectConfig
    mall_render_config: RenderObjectConfig
    flood_render_config: RenderObjectConfig
    forest_render_config: RenderObjectConfig
    road_render_config: RenderObjectConfig
    water_render_config: RenderObjectConfig
    car_render_config: RenderObjectConfig
