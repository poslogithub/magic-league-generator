from mtgsdk import Card
from hashlib import md5
from urllib.request import urlopen
from os.path import join
from PIL import Image
from io import BytesIO

class CardImageDownloader():
    CARD_BACK_IMAGE_MD5 = 'db0c48db407a907c16ade38de048a441'
    ALCHEMY_PREFIX = 'A-'
    FORMATS = {
        'BMP': '.bmp',
        'DIB': '.dib',
        'GIF': '.gif',
        'TIFF': '.tiff',
        'JPEG': '.jpg',
        'PPM': '.ppm',
        'PNG': '.png',
    }

    @classmethod
    def download_image_data_from_url(cls, image_url):
        with urlopen(url=image_url) as response:
            image_data = response.read()
            if md5(image_data).hexdigest() != cls.CARD_BACK_IMAGE_MD5:
                return image_data
            else:
                return None

    @classmethod
    def get_image_data(cls, name, set, number, language='Japanese'):
        if name.startsWith(cls.ALCHEMY_PREFIX):
            number = cls.ALCHEMY_PREFIX + str(number)

        cards = Card.where(set=set).where(number=number).all()

        image_data = None
        for card in cards:
            _, image_data = cls.get_card_name_and_image_data(card, language)
            if image_data:
                break

        return image_data
                
    @classmethod
    def get_card_name_and_image_data(cls, card, language='Japanese'):
        name = None
        image_data = None
        if card.foreign_names:
            for foreign_name in card.foreign_names:
                if foreign_name['language'] == language:
                    name = foreign_name['name']
                    image_url = foreign_name['imageUrl']
                    if image_url:
                        image_data = cls.download_image_data_from_url(image_url)
                    break
        if name is None:
            name = card.name
        if image_data is None:
            image_url = card.image_url
            if image_url:
                image_data = cls.download_image_data_from_url(image_url)

        return name, image_data

    @classmethod
    def save_all_image_data_from_set(cls, set, language='Japanese', dir='.'):
        cards = Card.where(set=set).all()

        image_data = None
        for card in cards:
            name, image_data = cls.get_card_name_and_image_data(card, language)
            if image_data:
                image = Image.open(IOBytes(image_data))
                format = image.format
                with open(join(dir, name))



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
