from dataclasses import dataclass


@dataclass
class RenderObjectConfig:
    geometry_node_file: str
    geometry_node_name: str


@dataclass
class GeoWindowConfig:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    crs_from: int
    crs_to: int


@dataclass
class Config:
    geo_window: GeoWindowConfig
    render_objects: bool
    remove_landlocked_plots: bool
    render_terrain: bool
    terrain_resolution: float
    use_sat_img: bool
    flood: bool
    flood_height: float
    flood_cell_size: float
    export_img: bool
    out_img_resolution: int
    out_img_pixel_size: float
    background_render_config: RenderObjectConfig
    building_render_config: RenderObjectConfig
    flood_render_config: RenderObjectConfig
    forest_render_config: RenderObjectConfig
    field_render_config: RenderObjectConfig
    garden_render_config: RenderObjectConfig
    fence_render_config: RenderObjectConfig
    road_render_config: RenderObjectConfig
    water_render_config: RenderObjectConfig
    tag_result_order: list
    tagging_config: dict
