import jsonpickle


class ConfigLoader:
    @staticmethod
    def save(config, filepath):
        json_dump = jsonpickle.encode(config, indent=1)
        with open(filepath, "w") as f:
            f.write(json_dump)

    @staticmethod
    def load(filepath):
        with open(filepath, "r") as f:
            json_dump = f.read()

        config = jsonpickle.decode(json_dump)
        return config
