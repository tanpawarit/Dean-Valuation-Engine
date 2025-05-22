import os 
from yaml import safe_load, YAMLError
from .logger import logger 

CONFIG_PATH = os.path.join(os.getcwd(), "config.yaml")


class Config:
    def __init__(self, path: str = CONFIG_PATH):
        self.path = path
        self._configs = dict()
        self._read_config()

    def _read_config(self):
        # read config file
        with open(self.path, "r") as stream:
            try:
                self._configs = safe_load(stream)
            except YAMLError as e:
                logger.error(e)

    def get_config(self, keys: str | list = None) -> dict:  # type: ignore
        if not keys:
            return self._configs
        elif isinstance(keys, str):
            config = self._configs.get(keys, dict())
        elif isinstance(keys, list):
            config = self._configs
            try:
                for key in keys:
                    config = config[key]
            except KeyError:
                return dict()

        return config
 