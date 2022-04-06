from mtgsdk import Card
from PIL import Image
from os.path import exists
import urllib

class MtgSdk():
    def __init__(self):
        self.set_cards = {}

    def get_set_cards(self, set):
        if set in self.set_cards.keys():
            return self.set_cards[set]
        else:
            try:
                print(set+"セットのカード一覧取得中...", end="", flush=True)
                cards = Card.where(set=set).all()
                self.set_cards[set] = cards
                print("成功")
            except Exception as e:
                print("失敗")
                print(e.args)
                return None
        return self.set_cards[set]
    
    @classmethod
    def normalize(cls, number_string):
        return int(number_string.replace('†', '').replace('A-', ''))
    
    def get_card(self, set, set_number=0, name=None, except_set_numbers=[]):
        cards = self.get_set_cards(set)
        for card in cards:
            if set_number:
                if self.normalize(card.number) == set_number:
                    return card
            elif name:
                if self.normalize(card.number) not in except_set_numbers:
                    if card.name == name:
                        return card
                    elif card.foreign_names:
                        for foreign_name in card.foreign_names:
                            if foreign_name.get('name') == name:
                                return card
        return None

    def get_card_image_url(self, name, set, set_number=0, except_set_numbers=[]):
        if set_number:
            card = self.get_card(set, set_number=set_number)
        else:
            card = self.get_card(set, name=name, except_set_numbers=except_set_numbers)
        if card:
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    if foreign_name.get('name') == name:
                        image_url = foreign_name.get('imageUrl')
                        if image_url:
                            return image_url
            elif card.image_url:
                return card.image_url
        return None
    
    def get_card_image(self, name, set, set_number, path=None):
        if path is None:
            path = name+".png"

        except_set_numbers = []
        image_url = self.get_card_image_url(name, set, set_number)
        print(name+"をダウンロード中...", end="", flush=True)
        while image_url:
            try:
                with urllib.request.urlopen(url=image_url) as res:
                    with Image.open(res) as image:
                        if image.format == 'PNG':
                            try:
                                image.save(path)
                                print("成功")
                                return path
                            except Exception as e:
                                print(e.args)
                                return None
                        else:
                            except_set_numbers.append(set_number)
                            card = self.get_card(set, name=name, except_set_numbers=except_set_numbers)
                            set_number = self.normalize(card.number)
                            image_url = self.get_card_image_url(name, set, set_number)
            except Exception as e:
                print(e.args)
                return None
        
            #TODO: png画像ファイルでなければ削除してNoneを返す？
            #TODO: 参考：https://water2litter.net/rum/post/python_pil_image_attributes/#:~:text=height%20256-,%E7%94%BB%E5%83%8F%E3%81%AE%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88%E3%82%92%E8%AA%BF%E3%81%B9%E3%82%8B%E6%96%B9%E6%B3%95,%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88%E3%81%8C%E5%8F%96%E5%BE%97%E3%81%A7%E3%81%8D%E3%81%BE%E3%81%99%E3%80%82&text=%E6%88%BB%E3%82%8A%E5%80%A4%E3%81%AE%E5%9E%8B%E3%81%AFstr%E3%81%A7%E3%81%99%E3%80%82,%E3%81%AFNone%E3%81%8C%E8%BF%94%E3%82%8A%E3%81%BE%E3%81%99%E3%80%82
        print("失敗")
        return None

#if __name__ == "__main__":
    #param = sys.argv
#    mtgsdk = MtgSdk()
#    mtgsdk.get_card_image("燃え立つ空、軋賜", "NEO", 134)
    #mtgsdk.get_card_image("当世", "NEO", 66)
    #mtgsdk.get_card_image("平地", "MID", 268)
    #CardImageDownloader.get_card_image("森", "VOW", 276)
cards = Card.where(set='MID').all()
for card in cards:
    print(card.number, card.name, card.names, card.image_url)
