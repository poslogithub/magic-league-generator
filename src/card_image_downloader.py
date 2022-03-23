from mtgsdk import Card, Set
import urllib

class MtgSdk():
    def __init__(self, language='Japanese'):
        self.set_cards = {}
        self.language = language

    def get_set_cards(self, set):
        if set in self.set_cards.keys():
            return self.set_cards[set]
        else:
            try:
                set = Set.find(set).code
                cards = Card.where(language=self.language).where(set=set).all()
                self.set_cards[set] = cards
                return self.set_cards[set]
            except:
                pass
        return None
    
    def get_card(self, set, set_number):
        cards = self.get_set_cards(set)
        for card in cards:
            if card.number == str(set_number):
                return card
        return None

    def get_card_image_url(self, name, set, set_number):
        card = self.get_card(set, set_number)
        if card:
            if card.foreign_names:
                for foreign_name in card.foreign_names:
                    if foreign_name.get('name') == name and foreign_name.get('language') == self.language:
                        image_url = foreign_name.get('imageUrl')
                        if image_url:
                            return image_url
            else:
                #TODO: image_url
                pass
        return None

    def get_card_image(self, name, set, set_number, path=None):
        if path is None:
            path = name+".png"

        image_url = self.get_card_image_url(name, set, set_number)

        rst = None        
        if image_url:
            print(name+"をダウンロード中...")
            try:
                with urllib.request.urlopen(url=image_url) as res:
                    img = res.read()
            except:
                print("except @ urlopen")
            try:
                with open(path, mode='wb') as f:
                    f.write(img)
                rst = path
            except:
                print("except @ write")
            #TODO: png画像ファイルでなければ削除してNoneを返す？
            #TODO: 参考：https://water2litter.net/rum/post/python_pil_image_attributes/#:~:text=height%20256-,%E7%94%BB%E5%83%8F%E3%81%AE%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88%E3%82%92%E8%AA%BF%E3%81%B9%E3%82%8B%E6%96%B9%E6%B3%95,%E3%83%95%E3%82%A9%E3%83%BC%E3%83%9E%E3%83%83%E3%83%88%E3%81%8C%E5%8F%96%E5%BE%97%E3%81%A7%E3%81%8D%E3%81%BE%E3%81%99%E3%80%82&text=%E6%88%BB%E3%82%8A%E5%80%A4%E3%81%AE%E5%9E%8B%E3%81%AFstr%E3%81%A7%E3%81%99%E3%80%82,%E3%81%AFNone%E3%81%8C%E8%BF%94%E3%82%8A%E3%81%BE%E3%81%99%E3%80%82
            return rst
        
        return None

if __name__ == "__main__":
    #param = sys.argv
    mtgsdk = MtgSdk()
    mtgsdk.get_card_image("森", "VOW", 276)
    #CardImageDownloader.get_card_image("森", "VOW", 276)