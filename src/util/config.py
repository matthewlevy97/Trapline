from typing import Any
import json

class Config():
    config_file_path = 'etc/config.json'

    @staticmethod
    def set_config_path(path: str) -> None:
        if path:
            Config.config_file_path = path

    @staticmethod
    def get(key: str) -> Any:
        with open(Config.config_file_path, 'r') as f:
            config = json.load(f)
            ret = config.get(key, None)
        return ret