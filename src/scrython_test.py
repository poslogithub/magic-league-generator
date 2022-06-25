from json import dump, load
from locale import getlocale
from os import mkdir
from os.path import exists, join
from sys import _getframe
from time import sleep

import scrython

lang = getlocale()[0].split('_')[0]
JSON_DIR = 'scrython_json'
IMAGE_DIR = 'scrython_image'
EXT_JSON = '.json'
UTF_8 = 'utf-8'

class Key():
    DATA = 'data'
    HAS_MORE = 'has_more'

class Scrython():
    def __init__(self, json_dir=JSON_DIR, image_dir=IMAGE_DIR):
        self.json_dir = json_dir
        self.image_dir = image_dir
        self.set_cards = {}

    def get_set_cards(self, set):
        if self.set_cards.get(set):
            return self.set_cards.get(set)

        json_path = join(self.json_dir, set+EXT_JSON)
        if exists(json_path):
            try:
                with open(json_path, 'r', encoding=UTF_8) as fp:
                    self.set_cards[set] = load(fp)
                    return self.set_cards[set]
            except Exception as e:
                print('Exception has occured @ {}.{} load {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
                print(e.args)
                return None

        page = 1
        q = 'set:{} lang:{} order:set'.format(set, lang)
        try:
            sleep(0.1)
            results = scrython.cards.Search(q=q, page=page)
            data = results.scryfallJson[Key.DATA]
            while results.scryfallJson[Key.HAS_MORE]:
                page += 1
                sleep(0.1)
                results = scrython.cards.Search(q=q, page=page)
                data.extend(results.scryfallJson[Key.DATA])
        except Exception as e:
            print('Exception has occured @ {}.{} {}.'.format(self.__class__, _getframe().f_code.co_name, 'scrython.cards.Search(q={}, page={})'.format(q, page)))
            print(e.args)
            return None
        
        self.set_cards[set] = data

        try:
            if not exists(JSON_DIR):
                mkdir(JSON_DIR)
            with open(json_path, 'w', encoding=UTF_8) as fp:
                dump(data, fp, ensure_ascii=False, indent=4)
        except Exception as e:
            print('Exception has occured @ {}.{} dump {}.'.format(self.__class__, _getframe().f_code.co_name, json_path))
            print(e.args)
            return None
        
        return self.set_cards[set]

if __name__ == '__main__':
    set = 'SNC'
    sdk = Scrython()
    print(sdk.get_set_cards(set))
