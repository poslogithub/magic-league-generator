from mtgsdk import Card
import urllib
from hashlib import md5
from urllib.request import urlopen

class CardImageDownloader():
    CARD_BACK_IMAGE_MD5 = 'db0c48db407a907c16ade38de048a441'

    def __init__(self, dir='.', language='Japanese'):
        self.dir = dir
        self.language = language
    
    @classmethod
    def check_md5(cls, image_data):
        hash_value = md5(image_data).hexdigest()
        if hash_value != cls.CARD_BACK_IMAGE_MD5:
            return True
        else:
            return False
    
    def get_card_image_data_from_cards(self, cards, name=None):
        for card in cards:
            image_url = None
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    if foreign_name.get('language') == self.language:
                        if not name or foreign_name.get('name') == name:
                            image_url = foreign_name.get('imageUrl')
                            break
            elif card.image_url:
                image_url = card.image_url
            if image_url:
                with urllib.request.urlopen(url=image_url) as res:
                    image_data = res.read()
                if self.check_md5(image_data):
                    return image_data
        return None

    def get_image_data(self, name, set, number):
        image_data = self.get_card_image_data_from_cards(Card.where(set=set).where(number=number).all())
        if not image_data:
            image_data = self.get_card_image_data_from_cards(Card.where(set=set).where(language=self.language).where(name=name).all(), name)
        if not image_data:
            image_data = self.get_card_image_data_from_cards(Card.where(language=self.language).where(name=name).all(), name)
        return image_data
    
    def get_card_image_data(cls, name, set, number, language='Japanese'):
        cards = Card.where(set='MID').where(number=268).all()

        image_url = None
        for card in cards:
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    if foreign_name['language'] == 'Japanese':
                        image_url = foreign_name['imageUrl']
                        if image_url:
                            with urlopen(url=image_url) as response:
                                image_data = response.read()
                                if md5(image_data).hexdigest() != cls.CARD_BACK_IMAGE_MD5:
                                    name = foreign_name['name']
                                else:
                                    image_url = None
                        break
            if image_url is None:
                name = card.name
                image_url = card.image_url
            if image_url:
                break


if __name__ == "__main__":
    downloader = CardImageDownloader()
#    image_data = downloader.get_image_data("貪る混沌、碑出告", "NEO", 99)
#    image_data = downloader.get_image_data("A-ゼロ除算", "STX", 41)
    image_data = downloader.get_image_data("沼", "MID", 272)
    if image_data:
        with open('test.png', 'wb') as f:
            f.write(image_data)
    
    #param = sys.argv
#    mtgsdk = MtgSdk()
#    mtgsdk.get_card_image("燃え立つ空、軋賜", "NEO", 134)
    #mtgsdk.get_card_image("当世", "NEO", 66)
    #mtgsdk.get_card_image("平地", "MID", 268)
    #CardImageDownloader.get_card_image("森", "VOW", 276)
