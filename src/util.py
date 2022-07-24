from traceback import print_exc

EXT_JSON = '.json'
SET_TABLE = {   # セット名変換表
    "DAR": "DOM"    # ドミナリア
}
UTF_8 = 'utf-8'
ENGLISH = 'English'
GATHERER_CARD_IMAGE_URL = 'https://gatherer.wizards.com/Handlers/Image.ashx?type=card&multiverseid='

def handle_exception(instance, co_name):
    print('An exception occured @ {}.{}.'.format(instance.__class__.__name__, co_name))
    print_exc()
