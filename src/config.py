from os import makedirs
from os.path import dirname, exists
import json


class ConfigFile():
    def __init__(self, path=None):
        self.path = path if path else "config.json"
        if not exists(dirname(self.path)):
            makedirs(dirname(self.path), exist_ok=True)
        self.config = {}

    def load(self):
        if exists(self.path):
            with open(self.path, 'r', encoding="utf_8_sig") as rf:
                config = json.load(rf)
                for key in config:
                    self.config[key] = config.get(key)
        return self.config
    
    def save(self, config):
        with open(self.path, 'w', encoding="utf_8_sig") as wf:
            json.dump(config, wf, ensure_ascii=False, indent=4)
