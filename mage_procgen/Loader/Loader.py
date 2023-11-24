import os

import pandas as p

from mage_procgen.Parser.ShapeFileParser import ShapeFileParser, RoadShapeFileParser
from mage_procgen.Parser.ASCParser import ASCParser
from mage_procgen.Parser.JP2Parser import JP2Parser

from mage_procgen.Utils.Utils import GeoWindow, GeoData, CRS_fr, CRS_degrees
import mage_procgen.Utils.DataFiles as df


class Loader:
    @staticmethod
    def load(geo_window: GeoWindow) -> GeoData:

        bbox = geo_window.bounds

        print("Loading shp files")

        arrondissements = ShapeFileParser.load(
            os.path.join(df.base_folder, df.departements, df.regions_file),
            bbox,
            CRS_fr,
        )

        departements_names = arrondissements["CODE_DEPT"].values

        plot_data = None
        building_data = None
        forest_data = None
        road_data = None
        water_data = None
        oceans_data = None
        departements_data = None
        terrain_data = []

        load_oceans = False

        for current_departement in departements_names:

            print("Loading data for departement " + current_departement)

            current_terrain_data = ASCParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.terrain_DB,
                    df.delivery,
                    df.terrain_data_folder,
                ),
                geo_window,
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.terrain_DB,
                    df.additional,
                    df.terrain_data_folder,
                    df.slab_file,
                ),
            )

            terrain_data.extend(current_terrain_data)

            current_plot_data = ShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.parcellaire_DB,
                    df.delivery,
                    df.parcellaire_data_folder,
                    df.plot_file,
                ),
                bbox,
                CRS_fr,
            )
            if plot_data is not None:
                plot_data = p.concat([plot_data, current_plot_data])
            else:
                plot_data = current_plot_data

            current_building_data = ShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.parcellaire_DB,
                    df.delivery,
                    df.parcellaire_data_folder,
                    df.building_file,
                ),
                bbox,
                CRS_fr,
            )
            if building_data is not None:
                building_data = p.concat([building_data, current_building_data])
            else:
                building_data = current_building_data

            current_forest_data = ShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.bdtopo_folder,
                    df.delivery,
                    df.forest_folder,
                    df.forest_file,
                ),
                bbox,
                CRS_fr,
            )
            if forest_data is not None:
                forest_data = p.concat([forest_data, current_forest_data])
            else:
                forest_data = current_forest_data

            current_road_data = RoadShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.bdtopo_folder,
                    df.delivery,
                    df.road_folder,
                    df.road_file,
                ),
                bbox,
                CRS_fr,
            )
            if road_data is not None:
                road_data = p.concat([road_data, current_road_data])
            else:
                road_data = current_road_data

            current_water_data = ShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.bdtopo_folder,
                    df.delivery,
                    df.water_folder,
                    df.water_file,
                ),
                bbox,
                CRS_fr,
                force_2d=True,
            )
            if water_data is not None:
                water_data = p.concat([water_data, current_water_data])
            else:
                water_data = current_water_data

            current_departement_data = ShapeFileParser.load(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.bdtopo_folder,
                    df.delivery,
                    df.dpt_folder,
                    df.dpt_file,
                ),
                bbox,
                CRS_fr,
                force_2d=True,
            )
            if departements_data is not None:
                departements_data = p.concat(
                    [departements_data, current_departement_data]
                )
            else:
                departements_data = current_departement_data

            if os.path.isfile(
                os.path.join(
                    df.base_folder,
                    df.departements,
                    current_departement,
                    df.bdtopo_folder,
                    df.delivery,
                    df.water_folder,
                    df.shore_file,
                )
            ):
                load_oceans = True

        if load_oceans:
            # Ocean file is in degrees so we have to convert the box back to this csr
            ocean_box = geo_window.dataframe.to_crs(CRS_degrees).geometry[0].bounds
            oceans_data = ShapeFileParser.load(
                os.path.join(df.base_folder, df.departements, df.ocean_file),
                ocean_box,
                CRS_fr,
                force_2d=True,
            )

        geo_data = GeoData(
            plot_data,
            building_data,
            forest_data,
            road_data,
            water_data,
            oceans_data,
            departements_data,
            terrain_data,
        )

        return geo_data

    @staticmethod
    def load_town_shape(geo_window: GeoWindow, departement_nbr: int, town_name: str):

        bbox = geo_window.bounds

        towns = ShapeFileParser.load(
            os.path.join(
                df.base_folder,
                df.departements,
                str(departement_nbr),
                df.bdtopo_folder,
                df.delivery,
                df.dpt_folder,
                df.town_file,
            ),
            bbox,
            CRS_fr,
        )

        town = towns.query("NOM == @town_name")

        return town

    @staticmethod
    def load_texture(mesh_box: tuple[float, float, float, float]) -> str:

        arrondissements = ShapeFileParser.load(
            os.path.join(df.base_folder, df.departements, df.regions_file),
            mesh_box,
            CRS_fr,
        )

        departements = list(set(arrondissements["CODE_DEPT"].values))

        if len(departements) > 1:
            raise ValueError("A single slab cannot be over multiple regions")

        current_departement = departements[0]

        current_texture_folder = os.path.join(
            df.base_folder, df.departements, df.texture_folder, current_departement
        )

        if not os.path.isdir(current_texture_folder):
            os.makedirs(current_texture_folder)

        texture_file_name = (
            "Texture_"
            + str(int(mesh_box[0]))
            + "_"
            + str(int(mesh_box[1]))
            + "_"
            + str(int(mesh_box[2]))
            + "_"
            + str(int(mesh_box[3]))
            + "_"
            + ".tif"
        )

        texture_full_path = os.path.join(current_texture_folder, texture_file_name)

        current_texture_image_folder = os.path.join(
            df.base_folder,
            df.departements,
            current_departement,
            df.texture_image_DB,
            df.delivery,
            df.texture_data_folder,
        )
        current_texture_image_slab_file = os.path.join(
            df.base_folder,
            df.departements,
            current_departement,
            df.texture_image_DB,
            df.additional,
            df.texture_data_folder,
            df.slab_file,
        )

        current_terrain_window = GeoWindow.from_square(
            mesh_box[0],
            mesh_box[2],
            mesh_box[1],
            mesh_box[3],
            CRS_fr,
            CRS_fr,
        )

        if not os.path.isfile(texture_full_path):
            JP2Parser.create_texture_img(
                current_texture_image_folder,
                current_terrain_window,
                current_texture_image_slab_file,
                texture_full_path,
            )

        return texture_full_path
