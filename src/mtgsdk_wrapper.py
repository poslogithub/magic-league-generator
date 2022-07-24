from json import dump, load
from locale import getlocale
from os import makedirs
from os.path import exists, join
from sys import _getframe
from time import sleep

from mtgsdk import Card
from util import EXT_JSON, SET_TABLE, UTF_8


class Key():
    NAME = 'name'
    NUMBER = 'number'
    IMAGE_URL = 'imageUrl'
    FOREIGN_NAMES = 'foreignNames'
    LANGUAGE = 'language'

class MtgSdkWrapper():
    JSON_DIR = 'mtgsdk_json'

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
                    self.cards[set] = load(fp)
                return self.cards[set]
            except Exception as e:
                print('An exception occured @ {}.{} load {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
                print(e.args)
                return None

        try:
            print('Downloading {} set data...'.format(set), end='', flush=True)
            cards = Card.where(set=set).all()
            sleep(0.1)
            print('complete.', flush=True)
        except Exception as e:
            print('An exception occured @ {}.{} Card.where({}).all().'.format(self.__class__, _getframe().f_code.co_name, set))
            print(e.args, flush=True)
            return None

        self.cards[set] = []
        for card in cards:
            entry = {}
            entry[Key.NAME] = card.name
            entry[Key.NUMBER] = card.number
            entry[Key.IMAGE_URL] = card.image_url
            entry[Key.FOREIGN_NAMES] = []
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    entry[Key.FOREIGN_NAMES].append(
                        {
                            Key.NAME: foreign_name.get(Key.NAME),
                            Key.LANGUAGE: foreign_name.get(Key.LANGUAGE),
                            Key.IMAGE_URL: foreign_name.get(Key.IMAGE_URL),
                        }
                    )
            self.cards[set].append(entry)
        
        try:
            if not exists(self.json_dir):
                makedirs(self.json_dir, exist_ok=True)
            with open(json_path, 'w', encoding=UTF_8) as fp:
                dump(self.cards[set], fp, ensure_ascii=False, indent=4)
        except Exception as e:
            print('An exception occured @ {}.{} dump {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
            print(e.args, flush=True)
            return None

        return self.cards[set]


    def get_card(self, set, number):
        set_cards = self.get_set_cards(set)
        cards = []
        if set_cards:
            for card in set_cards:
                if card.get('number') == str(number):
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
        
        for foreign_name in card.get(Key.FOREIGN_NAMES):
            if foreign_name.get(Key.LANGUAGE) == self.lang:
                if foreign_name.get(Key.IMAGE_URL):
                    return foreign_name.get(Key.IMAGE_URL)
        
        return card.get(Key.IMAGE_URL)


if __name__ == "__main__":
    set = 'NEO'

    sdk = MtgSdkWrapper()
    print(sdk.get_card_image_url(set, 3))
    print(sdk.get_card_image_url(set, 4))
    print(sdk.get_card_image_url(set, 4, back=True))
