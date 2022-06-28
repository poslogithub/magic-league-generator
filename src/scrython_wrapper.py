from json import dump, load
from locale import getlocale
from os import makedirs
from os.path import exists, join
from sys import _getframe
from time import sleep

import scrython
from util import EXT_JSON, SET_TABLE, UTF_8

ENGLISH = 'English'
GATHERER_CARD_IMAGE_URL = 'https://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid='

class Key():
    HAS_MORE = 'has_more'
    DATA = 'data'
    COLLECTOR_NUMBER = 'collector_number'
    MULTIVERSE_IDS = 'multiverse_ids'


class Scrython():
    JSON_DIR = 'scrython_json'

    lang = getlocale()[0].split('_')[0]

    def __init__(self, json_dir=None):
        self.json_dir = json_dir if json_dir else self.JSON_DIR
        self.cards = {}

    def search(self, q):
        data = []
        try:
            page = 1
            sleep(0.1)
            results = scrython.cards.Search(q=q, page=page)
            data.extend(results.scryfallJson[Key.DATA])
            while results.scryfallJson[Key.HAS_MORE]:
                page += 1
                sleep(0.1)
                results = scrython.cards.Search(q=q, page=page)
                data.extend(results.scryfallJson[Key.DATA])
        except Exception as e:
            print('Exception has occured @ {}.{} {}.'.format(self.__class__, _getframe().f_code.co_name, 'scrython.cards.Search(q={}, page={})'.format(q, page)))
            print(e.args)
            return None
        
        return data


    def get_set_cards(self, set):
        if set in SET_TABLE:
            set = SET_TABLE[set]

        if self.cards.get(set):
            return self.cards.get(set)
        self.cards[set] = {}

        json_path = join(self.json_dir, set+EXT_JSON)
        if exists(json_path):
            try:
                with open(json_path, 'r', encoding=UTF_8) as fp:
                    self.cards[set] = load(fp)
                return self.cards[set]
            except Exception as e:
                print('Exception has occured @ {}.{} load {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
                print(e.args)
                return None

        print('Downloading {} {} set data...'.format(self.lang, set), end='', flush=True)
        q = 'set:{} order:set lang:{}'.format(set, self.lang)
        data = self.search(q)
        if not data:
            return None
        self.cards[set][self.lang] = data
        print('Complete.')

        if self.lang != ENGLISH:
            print('Downloading {} {} set data...'.format(ENGLISH, set), end='', flush=True)
            q = 'set:{} order:set lang:{}'.format(set, ENGLISH)
            data = self.search(q)
            if not data:
                return None
            self.cards[set][ENGLISH] = data
            print('Complete.')

        try:
            if not exists(self.json_dir):
                makedirs(self.json_dir)
            with open(json_path, 'w', encoding=UTF_8) as fp:
                dump(self.cards[set], fp, ensure_ascii=False, indent=4)
        except Exception as e:
            print('Exception has occured @ {}.{} dump {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
            print(e.args)
            return None
        
        return self.cards[set]


    def get_card(self, set, collector_number):
        set_cards = self.get_set_cards(set)
        if not set_cards:
            return None

        for card in set_cards.get(self.lang):
            if (Key.COLLECTOR_NUMBER, str(collector_number)) in card.items():
                return card

        if self.lang != ENGLISH:
            for card in set_cards.get(ENGLISH):
                if (Key.COLLECTOR_NUMBER, str(collector_number)) in card.items():
                    return card

        return None
    
    
    def get_card_image_url(self, set, collector_number, back=False):
        card = self.get_card(set, collector_number)
        if not card:
            return None

        multiverse_ids = card.get(Key.MULTIVERSE_IDS)
        if not multiverse_ids:
            return None

        if len(multiverse_ids) == 1 or not back:
            multiverse_id = multiverse_ids[0]
        else:
            multiverse_id = multiverse_ids[1]
        
        return GATHERER_CARD_IMAGE_URL + str(multiverse_id)


if __name__ == '__main__':
    set = 'NEO'

    sdk = Scrython()
    print(sdk.get_card_image_url(set, 3))
    print(sdk.get_card_image_url(set, 4))
    print(sdk.get_card_image_url(set, 4, back=True))
