from mtgsdk import Card
import urllib

class CardImageDownloader():

    @classmethod
    def get_card_image(cls, name, set, set_number, path=None, language='Japanese'):
        if path is None:
            path = name+".png"

        image_url = None
        cards = Card.where(language=language).where(set=set).where(number=set_number).all()
        for card in cards:
            if card.foreign_names is None:
                break
            for foreign_name in card.foreign_names:
                if foreign_name.get('name') == name and foreign_name.get('language') == language:
                    image_url = foreign_name.get('imageUrl')
                    if image_url:
                        break
            if image_url:
                break
        
        if image_url:
            print(name+"をダウンロード中...")
            try:
                with urllib.request.urlopen(url=image_url) as res:
                    img = res.read()
            except:
                print("except @ urlopen")
                return None
            try:
                with open(path, mode='wb') as f:
                    f.write(img)
            except:
                print("except @ write")
                return None
            return path
        
        return None

if __name__ == "__main__":
    #param = sys.argv
    CardImageDownloader.get_card_image("悪魔の契約", "AKR", 99)