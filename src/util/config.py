from typing import Any
import json

class Config():
    @staticmethod
    def get(key: str) -> Any:
        with open('../config.json', 'r') as f:
            config = json.load(f)
            ret = config.get(key, None)
        return ret