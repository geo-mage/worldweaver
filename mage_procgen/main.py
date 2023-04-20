import sys

sys.path.append("/usr/lib/python3/dist-packages/")

from mage_procgen.Renderer import (
    BuildingRenderer,
    ForestRenderer,
    PlotRenderer,
    RoadRenderer,
    WaterRenderer,
    BackgroundRenderer,
)
from mage_procgen.Utils.Utils import GeoWindow, GeoData, CRS_fr, CRS_degrees
from mage_procgen.Preprocessor.Preprocessor import Preprocessor
from mage_procgen.Parser.ShapeFileParser import ShapeFileParser, RoadShapeFileParser


def main():
    parser = ShapeFileParser

    # geo_window = GeoWindow(2.93, 2.945, 48.9350, 48.94, CRS_degrees, CRS_fr)
    geo_window = GeoWindow(2.9, 2.955, 48.93, 48.945, CRS_degrees, CRS_fr)

    geo_center = geo_window.center

    bbox = geo_window.bounds

    print("Loading shp files")

    plot_data = parser.load(
        "/home/verstraa/Work/maps/PARCELLAIRE_EXPRESS/PARCELLAIRE_EXPRESS/1_DONNEES_LIVRAISON_2022-11-00045/PEPCI_1-1_SHP_LAMB93_D077/PARCELLE.SHP",
        bbox,
    )
    building_data = parser.load(
        "/home/verstraa/Work/maps/PARCELLAIRE_EXPRESS/PARCELLAIRE_EXPRESS/1_DONNEES_LIVRAISON_2022-11-00045/PEPCI_1-1_SHP_LAMB93_D077/BATIMENT.SHP",
        bbox,
    )
    forest_data = parser.load(
        "/home/verstraa/Work/maps/BDTOPO/BDTOPO/1_DONNEES_LIVRAISON_2022-12-00159/BDT_3-3_SHP_LAMB93_D077-ED2022-12-15/OCCUPATION_DU_SOL/ZONE_DE_VEGETATION.shp",
        bbox,
    )

    road_data = RoadShapeFileParser.load(
        "/home/verstraa/Work/maps/BDTOPO/BDTOPO/1_DONNEES_LIVRAISON_2022-12-00159/BDT_3-3_SHP_LAMB93_D077-ED2022-12-15/TRANSPORT/TRONCON_DE_ROUTE.shp",
        bbox,
    )

    water_data = parser.load(
        "/home/verstraa/Work/maps/BDTOPO/BDTOPO/1_DONNEES_LIVRAISON_2022-12-00159/BDT_3-3_SHP_LAMB93_D077-ED2022-12-15/HYDROGRAPHIE/SURFACE_HYDROGRAPHIQUE.shp",
        bbox,
        force_2d=True,
    )

    geo_data = GeoData(plot_data, building_data, forest_data, road_data, water_data)

    print("shp files loaded")

    print("Starting preprocessing")
    processor = Preprocessor(geo_data, geo_window, CRS_fr)
    rendering_data = processor.process()
    print("Preprocessing done")

    print("Starting rendering")

    fields_renderer = PlotRenderer.FieldRenderer()
    fields_renderer.render(rendering_data.fields, geo_center)
    print("Fields rendered")

    gardens_renderer = PlotRenderer.GardenRenderer()
    gardens_renderer.render(rendering_data.gardens, geo_center)
    print("Gardens rendered")

    fences_renderer = PlotRenderer.FenceRenderer()
    fences_renderer.render(rendering_data.fences, geo_center)
    print("Fences rendered")

    forest_renderer = ForestRenderer.ForestRenderer()
    forest_renderer.render(rendering_data.forests, geo_center)
    print("Forests rendered")

    building_renderer = BuildingRenderer.BuildingRenderer()
    building_renderer.render(rendering_data.buildings, geo_center)
    print("Buildings rendered")

    road_renderer = RoadRenderer.RoadRenderer()
    road_renderer.render(rendering_data.roads, geo_center)
    print("Roads rendered")

    water_renderer = WaterRenderer.WaterRenderer()
    water_renderer.render(rendering_data.water, geo_center)
    print("Water rendered")

    background_renderer = BackgroundRenderer.BackgroundRenderer()
    background_renderer.render(rendering_data.background, geo_center)
    print("Background rendered")


if __name__ == "__main__":
    main()
