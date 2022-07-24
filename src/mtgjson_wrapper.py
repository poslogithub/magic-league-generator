from json import dump, load
from locale import getlocale
from os import makedirs
from os.path import exists, join
from sys import _getframe, version_info
from urllib.request import urlopen, Request

from util import EXT_JSON, GATHERER_CARD_IMAGE_URL, SET_TABLE, UTF_8, handle_exception


class Key():
    DATA = 'data'
    CARDS = 'cards'
    NAME = 'name'
    NUMBER = 'number'
    IDENTIFIERS = 'identifiers'
    MULTIVERSE_ID = 'multiverseId'
    FOREIGN_DATA = 'foreignData'
    LANGUAGE = 'language'
    SET_CODE = 'setCode'
    USER_AGENT = 'User-Agent'

class Value():
    USER_AGENT = 'Python/{}.{}'.format(version_info.major, version_info.minor)

class MtgJsonWrapper():
    JSON_DIR = 'mtgjson_json'
    MTGJSON_URL = 'https://mtgjson.com/api/v5/'

    lang = getlocale()[0].split('_')[0]

    def __init__(self, json_dir=None):
        self.json_dir = json_dir if json_dir else self.JSON_DIR
        self.cards = {}

    def get_set_cards(self, set):
        if set in SET_TABLE:
            set = SET_TABLE[set]
        
        if self.cards.get(set):
            return self.cards.get(set)

        json_path = join(self.json_dir, set+EXT_JSON)
        if exists(json_path):
            try:
                with open(json_path, 'r', encoding=UTF_8) as fp:
                    json = load(fp)
            except Exception:
                handle_exception(self, _getframe().f_code.co_name)
                return None
            if json.get(Key.DATA) and json[Key.DATA].get(Key.CARDS):
                self.cards[set] = json[Key.DATA][Key.CARDS]
                return self.cards[set]

        try:
            makedirs(self.json_dir)
        except Exception:
            handle_exception(self, _getframe().f_code.co_name)
            return None

        print('Downloading {} set data...'.format(set), end='', flush=True)
        url = self.MTGJSON_URL+set+EXT_JSON
        request_headers = {
            Key.USER_AGENT: Value.USER_AGENT
        }
        request = Request(url, headers=request_headers)
        try:
            with urlopen(request, timeout=60) as response:
                json = load(response)
        except Exception:
            handle_exception(self, _getframe().f_code.co_name)
            return None
        try:
            with open(json_path, 'w', encoding='utf-8') as fp:
                dump(json, fp, ensure_ascii=False, indent=4)
        except Exception:
            handle_exception(self, _getframe().f_code.co_name)
            return None
        print('complete.', flush=True)

        if json.get(Key.DATA) and json[Key.DATA].get(Key.CARDS):
            self.cards[set] = json[Key.DATA][Key.CARDS]
            return self.cards[set]

        return None


    def get_card(self, set, number):
        set_cards = self.get_set_cards(set)
        cards = []
        if set_cards:
            for card in set_cards:
                if card.get(Key.SET_CODE) == set and card.get(Key.NUMBER) == str(number):
                    cards.append(card)

        return cards


    def get_card_image_url(self, set, number, back=False):
        cards = self.get_card(set, number)
        if not cards:
            return None
        
        if len(cards) == 1 or not back:
            card = cards[0]
        else:
            card = cards[1]
        
        for foreign_name in card.get(Key.FOREIGN_DATA):
            if foreign_name.get(Key.LANGUAGE) == self.lang:
                if foreign_name.get(Key.MULTIVERSE_ID):
                    return GATHERER_CARD_IMAGE_URL+str(foreign_name.get(Key.MULTIVERSE_ID))
        
        return GATHERER_CARD_IMAGE_URL+card.get(Key.IDENTIFIERS).get(Key.MULTIVERSE_ID)


if __name__ == "__main__":
    set = 'NEO'

    sdk = MtgJsonWrapper()
    print(sdk.get_card_image_url(set, 3))
    print(sdk.get_card_image_url(set, 4))
    print(sdk.get_card_image_url(set, 4, back=True))
