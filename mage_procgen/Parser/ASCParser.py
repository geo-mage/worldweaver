import os

import re
import pandas as p
from mage_procgen.Utils.Utils import TerrainData
from mage_procgen.Utils.Utils import GeoWindow, CRS_fr
from mage_procgen.Utils.DataFiles import file_coords_regex
from mage_procgen.Parser.ShapeFileParser import ShapeFileParser


class ASCParser:
    @staticmethod
    def load(
        file_folder: str,
        geo_window: GeoWindow,
        slab_file: str,
    ):

        bbox = geo_window.bounds
        slabs = ShapeFileParser.load(slab_file, bbox, CRS_fr)
        slab_parts = slabs.overlay(
            geo_window.dataframe, how="intersection", keep_geom_type=True
        )

        # TODO: could extract the region we really want and not the whole slab. Only issue would be with the rendering
        # resolution because it's much better if it divides the points number. Maybe it needs to be passed here, and
        # we get the smallest sub-slab that fits "pts_number is a multiple of render resolution"

        loaded_files = []

        for index, row in slab_parts.iterrows():
            file_name = os.path.basename(row["NOM_DALLE"]) + ".asc"

            file_full_path = os.path.join(file_folder, file_name)

            # Sometimes the name of the file in the dalles.shp file does not correspond to the actual name of the file
            if not os.path.isfile(file_full_path):
                # The corner of the file seems always be present in format _DDDD_DDDD_
                # We can use that to find the file we want
                file_coords = file_coords_regex.findall(file_name)[0]

                file_name = next(x for x in os.listdir(file_folder) if file_coords in x)
                file_full_path = os.path.join(file_folder, file_name)

            file_data = p.read_csv(file_full_path)

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

            print("Loaded slab : " + file_name)

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

        # Coherence check: find out if we are missing a slab
        global_x_min = min([x.x_min for x in loaded_files])
        global_x_max = max([x.x_max for x in loaded_files])
        global_y_min = min([x.y_min for x in loaded_files])
        global_y_max = max([x.y_max for x in loaded_files])

        resolution = loaded_files[0].resolution
        nbcols = loaded_files[0].nbcol
        nbrows = loaded_files[0].nbrow
        no_data = loaded_files[0].no_data

        terrain_data = p.DataFrame([[0 for x in range(nbcols)] for y in range(nbrows)])

        current_x = global_x_min
        current_y = global_y_min
        current_terrain = None

        while current_x < global_x_max and current_y < global_y_max:

            for terrain in loaded_files:
                if current_x == terrain.x_min and current_y == terrain.y_min:
                    current_terrain = terrain
                    break

            # If the terrain that is supposed to be there is not, add it
            if current_terrain is None:
                loaded_files.append(
                    TerrainData(
                        current_x,
                        current_y,
                        current_x + resolution * nbcols,
                        current_y + resolution * nbrows,
                        resolution,
                        nbcols,
                        nbrows,
                        no_data,
                        terrain_data,
                    )
                )

            # If we're at the end of a line
            if current_x >= global_x_max:
                current_y = current_y + resolution * nbrows
                current_x = global_x_min
            else:
                current_x = current_x + resolution * nbcols

        return loaded_files
