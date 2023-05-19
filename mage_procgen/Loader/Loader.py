import os

import pandas as p

from mage_procgen.Parser.ShapeFileParser import ShapeFileParser, RoadShapeFileParser
from mage_procgen.Parser.TerrainParser import TerrainParser

from mage_procgen.Utils.Utils import GeoWindow, GeoData, CRS_fr, CRS_degrees


class Loader:
    @staticmethod
    def load(bbox: tuple[float, float, float, float]) -> GeoData:

        base_folder = "/home/verstraa/Work/maps/Departements/"

        regions_file = "ARRONDISSEMENT/ARRONDISSEMENT.shp"

        terrain_folder = "RGEALTI/1_DONNEES_LIVRAISON/MNT"

        parcellaire_folder = "PARCELLAIRE_EXPRESS/1_DONNEES_LIVRAISON"
        plot_file = "PARCELLE.SHP"
        building_file = "BATIMENT.SHP"

        bdtopo_folder = "BDTOPO/1_DONNEES_LIVRAISON"
        forest_file = "OCCUPATION_DU_SOL/ZONE_DE_VEGETATION.shp"
        road_file = "TRANSPORT/TRONCON_DE_ROUTE.shp"
        water_file = "HYDROGRAPHIE/SURFACE_HYDROGRAPHIQUE.shp"

        print("Loading shp files")

        arrondissements = ShapeFileParser.load(
            os.path.join(base_folder, regions_file),
            bbox,
        )

        departements = arrondissements["CODE_DEPT"].values

        plot_data = None
        building_data = None
        forest_data = None
        road_data = None
        water_data = None
        terrain_data = []

        for current_departement in departements:

            print("Loading data for departement " + current_departement)

            current_terrain_data = TerrainParser.load(
                os.path.join(base_folder, current_departement, terrain_folder),
                bbox,
                1,
                1000,
                1000,
            )
            terrain_data.extend(current_terrain_data)
            # print("Terrain loaded: " + str(len(terrain_data)) + " chunks in total")

            current_plot_data = ShapeFileParser.load(
                os.path.join(
                    base_folder, current_departement, parcellaire_folder, plot_file
                ),
                bbox,
            )
            if plot_data is not None:
                plot_data = p.concat([plot_data, current_plot_data])
            else:
                plot_data = current_plot_data

            current_building_data = ShapeFileParser.load(
                os.path.join(
                    base_folder, current_departement, parcellaire_folder, building_file
                ),
                bbox,
            )
            if building_data is not None:
                building_data = p.concat([building_data, current_building_data])
            else:
                building_data = current_building_data

            current_forest_data = ShapeFileParser.load(
                os.path.join(
                    base_folder, current_departement, bdtopo_folder, forest_file
                ),
                bbox,
            )
            if forest_data is not None:
                forest_data = p.concat([forest_data, current_forest_data])
            else:
                forest_data = current_forest_data

            current_road_data = RoadShapeFileParser.load(
                os.path.join(
                    base_folder, current_departement, bdtopo_folder, road_file
                ),
                bbox,
            )
            if road_data is not None:
                road_data = p.concat([road_data, current_road_data])
            else:
                road_data = current_road_data

            current_water_data = ShapeFileParser.load(
                os.path.join(
                    base_folder, current_departement, bdtopo_folder, water_file
                ),
                bbox,
                force_2d=True,
            )
            if water_data is not None:
                water_data = p.concat([water_data, current_water_data])
            else:
                water_data = current_water_data

        geo_data = GeoData(
            plot_data, building_data, forest_data, road_data, water_data, terrain_data
        )

        return geo_data
