from mage_procgen.Parser.BaseParser import BaseParser
from pyogrio import read_dataframe


class ShapeFileParser(BaseParser):
    @staticmethod
    def load(file_path):
        file_data = read_dataframe(file_path)

        return file_data
