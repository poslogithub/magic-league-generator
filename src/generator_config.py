from config import ConfigFile
from generator import Mode

class ConfigKey():
    USER_ID = "userId"
    SET = "set"
    MODE = "mode"

class GeneratorConfigFile(ConfigFile):
    def __init__(self, path=None):
        super().__init__(path)
        self.config = {
            ConfigKey.USER_ID: "username#00000",
            ConfigKey.SET: None,
            ConfigKey.MODE: Mode.RANDOM
        }
