from operator import itemgetter

class Key():
    DETAIL_URL = 'detailUrl'
    IMAGE_URL = 'imageUrl'
    MULTIVERSE_ID = 'multiverseId'
    NAME = 'name'
    COLLECTOR_NUMBER = 'collectorNumber'
    CARD_NUMBER = 'cardNumber'
    TRANSLATED_CARDS = 'translatedCards'


cards = []
for _ in range(3):
    cards.append(
        {
            Key.NAME: None,
            Key.COLLECTOR_NUMBER: None,
            Key.CARD_NUMBER: None,
            Key.MULTIVERSE_ID: None,
            Key.IMAGE_URL: None,
            Key.TRANSLATED_CARDS: []
        }
    )

cards[0][Key.MULTIVERSE_ID] = 3
cards[0][Key.CARD_NUMBER] = "5a"
cards[1][Key.MULTIVERSE_ID] = 4
cards[1][Key.CARD_NUMBER] = "5a"
cards[2][Key.MULTIVERSE_ID] = 3
cards[2][Key.CARD_NUMBER] = "4"

cards.sort(key=itemgetter(Key.MULTIVERSE_ID, Key.CARD_NUMBER))

print(cards)
