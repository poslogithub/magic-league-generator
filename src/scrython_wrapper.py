from json import dump, load
from locale import getlocale
from os import makedirs
from os.path import exists, join
from sys import _getframe
from time import sleep
from traceback import print_exc

import scrython
from util import ENGLISH, EXT_JSON, GATHERER_CARD_IMAGE_URL, SET_TABLE, UTF_8

class Key():
    HAS_MORE = 'has_more'
    DATA = 'data'
    COLLECTOR_NUMBER = 'collector_number'
    MULTIVERSE_IDS = 'multiverse_ids'


class ScrythonWrapper():
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
        except:
            print_exc()
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
            except:
                print_exc()
                return None

        print('Downloading {} {} set data...'.format(self.lang, set), end='', flush=True)
        q = 'set:{} order:set lang:{}'.format(set, self.lang)
        data = self.search(q)
        if not data:
            return None
        self.cards[set][self.lang] = data
        print('complete.', flush=True)

        if self.lang != ENGLISH:
            print('Downloading {} {} set data...'.format(ENGLISH, set), end='', flush=True)
            q = 'set:{} order:set lang:{}'.format(set, ENGLISH)
            data = self.search(q)
            if not data:
                return None
            self.cards[set][ENGLISH] = data
            print('complete.', flush=True)

        try:
            if not exists(self.json_dir):
                makedirs(self.json_dir, exist_ok=True)
            with open(json_path, 'w', encoding=UTF_8) as fp:
                dump(self.cards[set], fp, ensure_ascii=False, indent=4)
        except:
            print_exc()
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

    sdk = ScrythonWrapper()
    print(sdk.get_card_image_url(set, 3))
    print(sdk.get_card_image_url(set, 4))
    print(sdk.get_card_image_url(set, 4, back=True))
