import os

import pandas as p
from mage_procgen.Utils.Utils import TerrainData
from mage_procgen.Utils.Utils import GeoWindow
from mage_procgen.Parser.ShapeFileParser import ShapeFileParser


class ASCParser:
    @staticmethod
    def load(
        file_folder: str,
        geo_window: GeoWindow,
        slab_file: str,
    ):

        bbox = geo_window.bounds
        slabs = ShapeFileParser.load(slab_file, bbox)
        slab_parts = slabs.overlay(
            geo_window.dataframe, how="intersection", keep_geom_type=True
        )

        # TODO: could extract the region we really want and not the whole slab. Only issue would be with the rendering
        # resolution because it's much better if it divides the points number. Maybe it needs to be passed here, and
        # we get the smallest sub-slab that fits "pts_number is a multiple of render resolution"

        loaded_files = []

        for index, row in slab_parts.iterrows():
            file_name = os.path.basename(row["NOM_DALLE"]) + ".asc"

            file_data = p.read_csv(os.path.join(file_folder, file_name))

            # Number of columns must be read in dataframe.columns, the rest is in the rows ...
            nbcols = int(file_data.columns[0].split(" ")[-1])
            nbrows = int(file_data.values[0][0].split(" ")[-1])

            # The x_min and y_min indicated are those of the enveloppe of the raster,
            # while we're concerned abt the center pixel which is (0.5,0.5) away.
            x_min = float(file_data.values[1][0].split(" ")[-1]) + 0.5
            y_min = float(file_data.values[2][0].split(" ")[-1]) + 0.5

            resolution = float(file_data.values[3][0].split(" ")[-1])
            no_data = float(file_data.values[4][0].split(" ")[-1])
            x_max = x_min + resolution * nbcols
            y_max = y_min + resolution * nbrows

            # Cleaning the data
            file_data = file_data.drop([0, 1, 2, 3, 4])

            terrain_pts_list = []

            for line in file_data.values:
                point_list = [float(x) for x in line[0].split(" ")[1:]]
                terrain_pts_list.append(point_list)

            terrain_data = p.DataFrame(terrain_pts_list)

            loaded_files.append(
                TerrainData(
                    x_min,
                    y_min,
                    x_max,
                    y_max,
                    resolution,
                    nbcols,
                    nbrows,
                    no_data,
                    terrain_data,
                )
            )

        return loaded_files
