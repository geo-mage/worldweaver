import os

import pandas as p
from mage_procgen.Utils.Utils import TerrainData


class TerrainParser:
    @staticmethod
    def load(
        file_folder: str,
        bbox: tuple[float, float, float, float],
        terrain_resolution,
        file_points_number_x,
        file_points_number_y,
    ):
        # TODO: resolution, pts number etc could be read from the first file instead of being passed as argument.
        # Assuming ofc that it's constant in a region.

        loaded_files = []

        for file in os.listdir(file_folder):
            file_name_parts = file.split("_")
            # File name contains xmin and ymax, but in km. we just need to convert it
            file_x_min = float(file_name_parts[2]) * 1000
            file_y_max = float(file_name_parts[3]) * 1000

            file_x_range = terrain_resolution * file_points_number_x
            file_y_range = terrain_resolution * file_points_number_y

            # If one of the corners of the file is in the bbox, load the file
            x_min_in = (file_x_min >= bbox[0]) and (file_x_min <= bbox[2])
            x_max_in = ((file_x_min + file_x_range) >= bbox[0]) and (
                (file_x_min + file_x_range) <= bbox[2]
            )
            y_max_in = (file_y_max >= bbox[1]) and (file_y_max <= bbox[3])
            y_min_in = ((file_y_max - file_y_range) >= bbox[1]) and (
                (file_y_max - file_y_range) <= bbox[3]
            )

            add_file = False
            add_file |= x_min_in and (y_min_in or y_max_in)
            add_file |= x_max_in and (y_min_in or y_max_in)
            # Also, if xmin is below and xmax is above (and similiarly for y)
            add_file |= (file_x_min <= bbox[0]) and (
                (file_x_min + file_x_range) >= bbox[2]
            )
            add_file |= ((file_y_max - file_y_range) <= bbox[1]) and (
                file_y_max >= bbox[3]
            )

            if not add_file:
                continue

            file_data = p.read_csv(os.path.join(file_folder, file))

            # Number of columns must be read in dataframe.columns, the rest is in the rows ...
            nbcols = int(file_data.columns[0].split(" ")[-1])
            nbrows = int(file_data.values[0][0].split(" ")[-1])
            x_min = float(file_data.values[1][0].split(" ")[-1])
            y_min = float(file_data.values[2][0].split(" ")[-1])
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
