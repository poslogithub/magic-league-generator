from mtgsdk import Card
from os.path import exists, join
import json
from urllib.request import urlopen
from hashlib import md5
from re import sub
from PIL import Image
from io import BytesIO

class CardImageDownloader():
    FORMATS = {
        'BMP': '.bmp',
        'DIB': '.dib',
        'GIF': '.gif',
        'TIFF': '.tiff',
        'JPEG': '.jpg',
        'PPM': '.ppm',
        'PNG': '.png'
    }

    def __init__(self, language='Japanese', json_dir='.'):
        self.__language = language
        self.__json_dir = json_dir

    def get_card_name_and_image_data(self, set, number, language=None):
        card = self.__get_card(set, number)
        return self.__get_card_name_and_image_data(card, language if language else self.__language)
    
    def get_card_image_data(self, set, number, language=None):
        name, image_data = self.get_card_name_and_image_data(set, number, language if language else self.__language)
        return image_data

    def save_set_all_image(self, set, dir='.', language=None):
        cards = self.__get_set_cards(set)
        for card in cards:
            name = self.__get_card_name(card, language if language else self.__language)
            is_exist = False
            for ext in self.FORMATS.values():
                path = join(dir, sub(r'["*/:<>?\\\|]', '-', name+ext))
                if exists(path):
                    is_exist = True
                    break
            if not is_exist:
                name, image_data = self.__get_card_name_and_image_data(card, language if language else self.__language)
                if name and image_data:
                    with Image.open(BytesIO(image_data)) as image:
                        format = image.format
                        ext = self.FORMATS.get(format)
                        if ext:
                            path = join(dir, sub(r'["*/:<>?\\\|]', '-', name+self.FORMATS[format]))
                            if not exists(path):
                                image.save(path)

    __CARD_BACK_IMAGE_MD5 = 'db0c48db407a907c16ade38de048a441'
    
    def __get_card(self, set, number):
        cards = self.__get_set_cards(set)
        for card in cards:
            if card['number'] == str(number):
                return card
        return None

    def __get_set_cards(self, set):
        json_path = join(self.__json_dir, set+'.json')
        if exists(json_path):
            with open(json_path) as f:
                set_cards = json.load(f)
        else:
            set_cards = {}
        if set in set_cards.keys():
            return set_cards[set]
        else:
            print(set+"セットのカード一覧取得中...", end="", flush=True)
            set_cards[set] = []
            try:
                cards = Card.where(set=set).all()
                for card in cards:
                    entry = {}
                    entry['foreignNames'] = card.foreign_names
                    entry['imageUrl'] = card.image_url
                    entry['name'] = card.name
                    entry['number'] = card.number
                    set_cards[set].append(entry)
                with open(json_path, 'w') as f:
                    f.write(json.dumps(set_cards))
                print("成功")
                return set_cards[set]
            except Exception as e:
                print("失敗")
                print(e.args)
                return None
    
    @classmethod
    def __get_card_name(cls, card, language):
        name = None
        if card:
            if card['foreignNames']:
                for foreign_name in card['foreignNames']:
                    if foreign_name['language'] == language:
                        name = foreign_name['name']
                        break
            if name is None:
                name = card['name']
        return name

    @classmethod
    def __get_card_name_and_image_data(cls, card, language):
        name = None
        image_data = None
        if card:
            if card['foreignNames']:
                for foreign_name in card['foreignNames']:
                    if foreign_name['language'] == language:
                        name = foreign_name['name']
                        image_url = foreign_name['imageUrl']
                        if image_url:
                            image_data = cls.__download_image_data_from_url(image_url, name)
                        break
            if image_data is None:
                name = card['name']
                image_url = card['imageUrl']
                if image_url:
                    image_data = cls.__download_image_data_from_url(image_url, name)
        return name, image_data

    @classmethod
    def __download_image_data_from_url(cls, image_url, name=None):
        if name:
            print(name+"をダウンロード中...", end="", flush=True)
        with urlopen(url=image_url) as response:
            image_data = response.read()
            if md5(image_data).hexdigest() == cls.__CARD_BACK_IMAGE_MD5:
                image_data = None
        if name:
            if image_data:
                print("成功")
            else:
                print("失敗")
        return image_data

if __name__ == "__main__":
    #param = sys.argv
    downloader = CardImageDownloader()
    #name, image_data = downloader.get_card_name_and_image_data('NEO', 226) # 漆月魁渡
    #name, image_data = downloader.get_card_name_and_image_data('ELD', 329)  # フェイに呪われた王、コルヴォルド
    #name, image_data = downloader.get_card_name_and_image_data('NEO', 4)    # 蛾との親睦
    #name, image_data = downloader.get_card_name_and_image_data('MID', 268)    # MID平地
    #name, image_data = downloader.get_card_name_and_image_data('AFR', 1)    # メイス＋２
    #name, image_data = downloader.get_card_name_and_image_data('STX', 'A-41')    # A-ゼロ除算
    #name, image_data = downloader.get_card_name_and_image_data('NEO', '219')    # 闇叫び
#    if name and image_data:
#        with open(sub(r'["*/:<>?\\\|]', '-', name)+'.png', 'wb') as f:
#            f.write(image_data)

    downloader.save_set_all_image('VOW', 'card_image')
