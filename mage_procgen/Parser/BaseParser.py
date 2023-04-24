import geopandas as g


class BaseParser:
    @staticmethod
    def load(file_path: str, bbox: tuple[float, float, float, float]) -> g.GeoDataFrame:
        raise NotImplementedError
