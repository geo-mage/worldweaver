from dataclasses import dataclass

@dataclass
class Config:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    crs_from: int
    crs_to: int
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

@dataclass
class GeoWindowConfig:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    crs_from: int
    crs_to: int


@dataclass
class RenderObjectConfig:
    GNSetup: str
    GNFile: str
    mesh_name: str