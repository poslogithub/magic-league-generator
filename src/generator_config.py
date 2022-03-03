from config import ConfigFile
from generator import Mode

class ConfigKey():
    USER_ID = "userId"
    SET = "set"
    MODE = "mode"
    INDEX_TIME = "indexTime"
    PACK_MODE = "packMode"
    PACK_NUM = "packNum"

class GeneratorConfigFile(ConfigFile):
    def __init__(self, path=None):
        super().__init__(path)
        self.config = {
            ConfigKey.USER_ID: "username#00000",
            ConfigKey.SET: None,
            ConfigKey.MODE: Mode.DAILY,
            ConfigKey.INDEX_TIME: "",
            ConfigKey.PACK_MODE: 0, # 0:自動, 1:手動
            ConfigKey.PACK_NUM: 6
        }
