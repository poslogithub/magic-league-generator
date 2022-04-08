from config import ConfigFile
from generator import Mode

class ConfigKey():
    USER_ID = "userId"
    SETS = "sets"
    MODE = "mode"
    INDEX_TIME = "indexTime"
    PACK_MODE = "packMode"
    PACK_NUMS = "packNums"
    CARD_IMAGE_CACHE_DIR = "cardImageCacheDir"
    DECKLIST_IMAGE_OUTPUT_DIR = "decklistImageOutputDir"

class GeneratorConfigFile(ConfigFile):
    def __init__(self, path=None):
        super().__init__(path)
        self.config = {
            ConfigKey.USER_ID: "username#00000",
            ConfigKey.SETS: [ None, None, None ],
            ConfigKey.MODE: Mode.DAILY,
            ConfigKey.INDEX_TIME: "",
            ConfigKey.PACK_MODE: 0, # 0:自動, 1:手動
            ConfigKey.PACK_NUMS: [ 6, 0, 0 ],
            ConfigKey.CARD_IMAGE_CACHE_DIR: "card_image",
            ConfigKey.DECKLIST_IMAGE_OUTPUT_DIR: "."
        }
