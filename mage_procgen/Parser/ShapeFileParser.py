from mage_procgen.Parser.BaseParser import BaseParser
from pyogrio import read_dataframe, read_info

class ShapeFileParser(BaseParser):
    @staticmethod
    def load(file_path):
        file_data = read_dataframe(file_path)

        return file_data


# Need this because of a bug (?) if we use pyogrio on roads (timestamp issue)
class RoadShapeFileParser(ShapeFileParser):

    _fields = "fields"
    _invalid_columns = ["DATE_SERV", "DATE_CONF", "DATE_APP"]

    @staticmethod
    def load(file_path):

        file_info = read_info(file_path)

        file_fields = file_info[RoadShapeFileParser._fields]

        valid_columns = [i for i in file_fields if i not in RoadShapeFileParser._invalid_columns]

        file_data = read_dataframe(file_path, force_2d=True, columns=valid_columns)

        return file_data

