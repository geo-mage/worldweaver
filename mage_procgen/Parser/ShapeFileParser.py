from mage_procgen.Parser.BaseParser import BaseParser
from pyogrio import read_dataframe, read_info
import geopandas as g
import shapely


class ShapeFileParser:
    @staticmethod
    def load(
        file_path: str,
        bbox: tuple[float, float, float, float],
        to_crs: int,
        force_2d=False,
    ) -> g.GeoDataFrame:
        file_data = read_dataframe(file_path, bbox=bbox, force_2d=force_2d).to_crs(
            to_crs
        )

        file_data.set_geometry(
            shapely.set_precision(file_data.geometry, 1e-2), inplace=True
        )

        return file_data


# Need this because of a bug (?) if we use pyogrio on roads (timestamp issue)
class RoadShapeFileParser:
    _fields = "fields"
    _invalid_columns = ["DATE_SERV", "DATE_CONF", "DATE_APP"]

    @staticmethod
    def load(
        file_path: str, bbox: tuple[float, float, float, float], to_crs: int
    ) -> g.GeoDataFrame:
        file_info = read_info(file_path)

        file_fields = file_info[RoadShapeFileParser._fields]

        valid_columns = [
            i for i in file_fields if i not in RoadShapeFileParser._invalid_columns
        ]

        file_data = read_dataframe(
            file_path, force_2d=True, columns=valid_columns, bbox=bbox
        ).to_crs(to_crs)

        file_data.set_geometry(
            shapely.set_precision(file_data.geometry, 1e-2), inplace=True
        )

        return file_data
