from mtgsdk import Card
from hashlib import md5
from urllib.request import urlopen

class CardImageDownloader():
    CARD_BACK_IMAGE_MD5 = 'db0c48db407a907c16ade38de048a441'

    @classmethod
    def get_image_data(cls, set, number, language='Japanese'):
        cards = Card.where(set=set).where(number=number).all()

        image_data = None
        for card in cards:
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    if foreign_name['language'] == language:
                        image_url = foreign_name['imageUrl']
                        if image_url:
                            with urlopen(url=image_url) as response:
                                image_data = response.read()
                                if md5(image_data).hexdigest() == cls.CARD_BACK_IMAGE_MD5:
                                    image_data = None
                        break
            if image_data is None:
                if card.image_url:
                    with urlopen(url=card.image_url) as response:
                        image_data = response.read()
            if image_data:
                return image_data


if __name__ == "__main__":
#    image_data = downloader.get_image_data("貪る混沌、碑出告", "NEO", 99)
#    image_data = downloader.get_image_data("A-ゼロ除算", "STX", 41)
    image_data = CardImageDownloader.get_image_data("MID", 268)
    if image_data:
        with open('test.png', 'wb') as f:
            f.write(image_data)
    
    #param = sys.argv
#    mtgsdk = MtgSdk()
#    mtgsdk.get_card_image("燃え立つ空、軋賜", "NEO", 134)
    #mtgsdk.get_card_image("当世", "NEO", 66)
    #mtgsdk.get_card_image("平地", "MID", 268)
    #CardImageDownloader.get_card_image("森", "VOW", 276)
