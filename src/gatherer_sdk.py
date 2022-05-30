# Standard Library
import json
from html.parser import HTMLParser
from threading import Thread
from locale import getdefaultlocale
from time import sleep
from os.path import exists, join
from io import BytesIO
from re import sub

# PyPI
from PIL import Image   # Pillow @ HPND
import requests # requests @ Apache-2.0
import lxml # lxml @ BSD

NBSP = '\xa0'
LANGUAGES = {
    'English': 'en-US',
    'Français': 'fr-FR',
    'Italiano': 'it-IT',
    'Deutsch': 'de-DE',
    '日本語': 'ja-JP',
    'Português': 'pt-BR',
    'русский язык': 'ru-RU',
    '한국어': 'ko-KR',
    '简体中文': 'zh-CN',
    '繁體中文': 'zh-TW'
}

def get_queries(url):
    rst = []
    query_string = url.split('?')[1]
    queries = query_string.split('&')
    for query in queries:
        rst[query[0]] = query[1]
    return rst

class Query():
    MULTIVERSE_ID = 'multiverseid'
    OPTIONS = 'options'
    PART = 'part'

class Tag():
    A = 'a'
    DIV = 'div'
    IMG = 'img'
    SPAN = 'span'
    TABLE = 'table'
    TD = 'td'
    TR = 'tr'

class Attr():
    ALT = 'alt'
    CLASS = 'class'
    HREF = 'href'
    ID = 'id'
    SRC = 'src'

class AttrValue():
    PAGING = 'paging'
    VALUE = 'value'

class Key():
    DETAIL_URL = 'detailUrl'
    IMAGE_URL = 'imageUrl'
    MULTIVERSE_ID = 'multiverseId'
    NAME = 'name'
    COLLECTOR_NUMBER = 'collectorNumber'
    CARD_NUMBER = 'cardNumber'
    TRANSLATED_CARDS = 'translatedCards'

class FaceType():
    NORMAL = 'normal'
    DOUBLE_FACED_FIRST = 'double_faced_first'
    DOUBLE_FACED_SECOND = 'double_faced_second'
    MELD = 'meld'
    MELD_MAIN = 'meld_main'
    MELD_SUB = 'meld_sub'
    SPLIT = 'split'
    FLIP = 'flip'
    ADVENTURER = 'adventurer'


# 検索結果画面をパースして、全検索結果ページへのリンクを取得する
class SearchResultParserForAllPageURLs(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?action=advanced&output=standard&sort=cn+&set=+[%22{}%22]'

    def __init__(self, set):
        super().__init__()
        self.url = self.URL.format(set)

    def feed(self, data):
        self.found_paging_div = False
        self.found_paging_a = False
        self.paging_links = []  # 2次元配列で、2次元目の0番目の値はリンクテキスト、1番目の値はSearchResultPageのURL
        self.link_text = None
        self.link_url = None
        super().feed(data)
        return self.paging_links

    def handle_starttag(self, tag, attrs):
        if tag == Tag.DIV:
            if not self.found_paging_div:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1] == AttrValue.PAGING:
                        self.found_paging_div = True
                        break
        if tag == Tag.A:
            if self.found_paging_div:
                self.found_paging_a = True
                for attr in attrs:
                    if attr[0] == Attr.HREF:
                        self.link_url = attr[1]
                        break

    def handle_endtag(self, tag):
        if tag == Tag.DIV:
            if self.found_paging_div:
                self.found_paging_div = False
        if tag == Tag.A:
            if self.found_paging_a:
                self.found_paging_a = False

    def handle_data(self, data):
        if self.found_paging_a:
            self.link_text = data.replace(NBSP, "")
            self.paging_links.append([self.link_text, self.link_url])

# 検索結果画面をパースして、各カードのmultiverseidを取得する
class SearchResultParserForMultiverseIds(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?page={}&action=advanced&output=standard&sort=cn+&set=+[%22{}%22]'
    CARD_IMAGE_LINK_POSTFIX = '_cardImageLink'

    def __init__(self, set, page):
        super().__init__()
        self.set = set
        self.url = self.URL.format(page, set)

    def feed(self, data):
        self.multiverse_ids = []
        super().feed(data)
        return self.multiverse_ids

    def handle_starttag(self, tag, attrs):
        if tag == Tag.A:
            found_card_image_link_a = False
            link_url = None
            for attr in attrs:
                if attr[0] == Attr.ID:
                    if attr[1].endswith(self.CARD_IMAGE_LINK_POSTFIX):
                        found_card_image_link_a = True
                elif attr[0] == Attr.HREF:
                    link_url = attr[1]
            if found_card_image_link_a and link_url:
                queries = get_queries(link_url)
                multiverse_id = int(queries.get(Query.MULTIVERSE_ID))
                self.multiverse_ids.append(multiverse_id)

# カード詳細ページをパースして、各バリエーションのmultiverseidを取得する
class DetailParserForVariations(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={}'
    VARIATION_LINKS_POSTFIX = '_variationLinks'
    COMMUNITY_RATINGS_CLASS = 'CommunityRatings'

    def __init__(self, multiverse_id):
        super().__init__()
        self.url = self.URL.format(multiverse_id)

    def feed(self, data):
        self.found_variation_links_div = False
        self.multiverse_ids = []
        super().feed(data)
        return self.multiverse_ids

    def handle_starttag(self, tag, attrs):
        if tag == Tag.DIV:
            if not self.found_variation_links_div:
                for attr in attrs:
                    if attr[0] == Attr.ID and attr[1].endswith(self.VARIATION_LINKS_POSTFIX):
                        self.found_variation_links_div = True
                        break
            elif self.found_variation_links_div:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1] == self.COMMUNITY_RATINGS_CLASS:
                        self.found_variation_links_div = False
                        break
        if tag == Tag.A:
            if self.found_variation_links_div:
                link_url = None
                for attr in attrs:
                    if attr[0] == Attr.HREF:
                        link_url = attr[1]
                        queries = get_queries(link_url)
                        multiverse_id = int(queries.get(Query.MULTIVERSE_ID))
                        self.multiverse_ids.append(multiverse_id)
                        break

# 言語画面をパースして、全言語ページへのリンクを取得する
class SearchResultParserForAllPageURLs(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Card/Languages.aspx?multiverseid={}'

    def __init__(self, multiverse_id):
        super().__init__()
        self.url = self.URL.format(multiverse_id)

    def feed(self, data):
        self.found_paging_div = False
        self.found_paging_a = False
        self.paging_links = []  # 2次元配列で、2次元目の0番目の値はリンクテキスト、1番目の値はSearchResultPageのURL
        self.link_url = None
        super().feed(data)
        return self.paging_links

    def handle_starttag(self, tag, attrs):
        if tag == Tag.DIV:
            if not self.found_paging_div:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1] == AttrValue.PAGING:
                        self.found_paging_div = True
                        break
        if tag == Tag.A:
            if self.found_paging_div:
                self.found_paging_a = True
                for attr in attrs:
                    if attr[0] == Attr.HREF:
                        self.link_url = attr[1]
                        break

    def handle_endtag(self, tag):
        if tag == Tag.DIV:
            if self.found_paging_div:
                self.found_paging_div = False
        if tag == Tag.A:
            if self.found_paging_a:
                self.found_paging_a = False

    def handle_data(self, data):
        if self.found_paging_a:
            link_text = data.replace(NBSP, "")
            if link_text.isdecimal():
                self.paging_links.append([link_text, self.link_url])
            
# 言語ページをパースして、各カードのmultiverseidを取得する
class LanguageParserForLanguagesAndMultiverseIds(HTMLParser):
    CARD_ITEM_PREFIX = 'cardItem '

    def __init__(self, url):
        super().__init__()
        self.url = url

    def feed(self, data):
        self.found_card_item_tr = False
        self.found_language_td = False
        self.card_item_td_count = 0
        self.languages = []
        self.multiverse_ids = []
        super().feed(data)
        return self.languages, self.multiverse_ids

    def handle_starttag(self, tag, attrs):
        if tag == Tag.TR:
            if not self.found_card_item_tr:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1].startswith(self.CARD_ITEM_PREFIX):
                        self.found_card_item_tr = True
                        self.card_item_td_count = 0
                        break
        if tag == Tag.A:
            if self.found_card_item_tr:
                for attr in attrs:
                    if attr[0] == Attr.HREF:
                        link_url = attr[1]
                        queries = get_queries(link_url)
                        multiverse_id = int(queries.get(Query.MULTIVERSE_ID))
                        self.multiverse_ids.append(multiverse_id)
                        break
        if tag == Tag.TD:
            if self.found_card_item_tr:
                if self.card_item_td_count == 2:
                    self.found_language_td = True
                else:
                    self.card_item_td_count += 1
    
    def handle_endtag(self, tag, attrs):
        if tag == Tag.TR:
            if self.found_card_item_tr:
                self.found_card_item_tr = False
                self.card_item_td_count = 0
        if tag == Tag.TD:
            if self.found_language_td:
                self.found_language_td = False
            
    def handle_data(self, data):
        if self.found_language_td:
            self.language = data.replace(NBSP, "")
            self.languages.append(LANGUAGES[self.language])

#TODO
# カード詳細ページをパースしてカード情報を取得する
class DetailParserForCardData(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={}'
    IMAGE_URL = 'https://gatherer.wizards.com/Handlers/Image.ashx?{}'
    SUBTITLE_POSTFIX = '_SubContentHeader_subtitleDisplay'
    CARD_IMAGE_POSTFIX = '_cardImage'
    NAME_POSTFIX = '_nameRow'
    CARD_NUMBER_POSTFIX = '_numberRow'
    CARD_COMPONENT = '_cardComponent'

    def __init__(self, multiverse_id):
        super().__init__()
        self.url = self.URL.format(multiverse_id)
        self.image_url = self.IMAGE_URL.format(multiverse_id)

    def feed(self, data):
        self.found_subtitle_span = False
        self.found_name_div = False
        self.found_name_value_div = False
        self.found_card_number_div = False
        self.found_card_number_value_div = False
        self.found_card_details_table = False
        self.card_component_count = 0
        self.face_type = None
        self.cards = []
        for _ in range(2):
            self.cards.append(
                {
                    Key.NAME: None,
                    Key.COLLECTOR_NUMBER: None,
                    Key.CARD_NUMBER: None,
                    Key.MULTIVERSE_ID: None,
                    Key.IMAGE_URL: None,
                    Key.TRANSLATED_CARDS: []
                }
            )
        super().feed(data)
        return self.results

    def handle_starttag(self, tag, attrs):
        # 表題のカード名
        if tag == Tag.SPAN:
            if not self.found_subtitle_span:
                for attr in attrs:
                    if attr[0] == Attr.ID and attr[1].endswith(self.SUBTITLE_POSTFIX):
                        self.found_subtitle_span = True
                        break
        # カードコンポーネント開始
        if tag == Tag.TD:
            for attr in attrs:
                if attr[0] == Attr.CLASS and self.CARD_COMPONENT in attr[1]:
                    self.card_component_count += 1
                    break
        # カード画像
        if tag == Tag.IMG:
            is_card_image = False
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.CARD_IMAGE_POSTFIX):
                    is_card_image = True
                elif attr[0] == Attr.ALT:
                    alt = attr[1]
                elif attr[0] == Attr.SRC:
                    src = attr[1]
            if is_card_image:
                self.cards[self.card_component_count][Key.NAME] = alt
                queries = get_queries(src)
                multiverse_id = int(queries.get(Query.MULTIVERSE_ID))
                self.cards[self.card_component_count][Key.MULTIVERSE_ID] = multiverse_id
                self.cards[self.card_component_count][Key.IMAGE_URL] = self.IMAGE_URL.format(multiverse_id)
            elif not self.found_card_details_table: # TODO found_card_details_tableの条件をもっと何とかできないか。というかいらんくね？
                for attr in attrs:
                    if attr[0] == Attr.ALT and attr[1] == self.result.get(Key.NAME):
                        self.found_card_details_table = True
                        break
        if self.found_card_details_table:
            # 英語版カード名
            if not self.found_name_div and tag == Tag.DIV:
                for attr in attrs:
                    if attr[0] == Attr.ID and attr[1].endswith(self.NAME_POSTFIX):
                        self.found_name_div = True
                        break
            if self.found_name_div and not self.found_name_value_div and tag == Tag.DIV:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1] == AttrValue.VALUE:
                        self.found_name_value_div = True
                        break
            # カード番号
            if not self.found_card_number_div and tag == Tag.DIV:
                for attr in attrs:
                    if attr[0] == Attr.ID and attr[1].endswith(self.CARD_NUMBER_POSTFIX):
                        self.found_card_number_div = True
                        break
            if self.found_card_number_div and not self.found_card_number_value_div and tag == Tag.DIV:
                for attr in attrs:
                    if attr[0] == Attr.CLASS and attr[1] == AttrValue.VALUE:
                        self.found_card_number_value_div = True
                        break
    
    def handle_endtag(self, tag):
        if self.found_card_details_table and tag == Tag.TABLE:
            self.found_card_details_table = False
    
    def handle_data(self, data):
        # カード名
        if self.found_subtitle_span:
            if ' // ' in data:
                self.face_type = FaceType.SPLIT
            self.cards[self.card_component_count][Key.NAME] = data
            self.found_subtitle_span = False
        # カード詳細テーブル
        if self.found_card_details_table:
            # 英語版カード名
            if self.found_name_div and self.found_name_value_div:
                self.result[Key.ROW_NAME] = data.strip()
                self.found_name_div = False
                self.found_name_value_div = False
            # カード番号
            if self.found_card_number_div and self.found_card_number_value_div:
                self.result[Key.ROW_NUMBER] = sub("\s", "", data)
                self.result[Key.NUMBER] = int(sub("\D", "", self.result[Key.ROW_NUMBER]))
                self.found_card_number_div = False
                self.found_card_number_value_div = False

class GathererSDK():
    LOCALE = getdefaultlocale()[0].replace("_", "-")
    THREAD_INTERVAL_SEC = 0.01
    THREAD_TIMEOUT_SEC = 60
    SET_TABLE = {   # セット名変換表
        "DAR": "DOM"    # ドミナリア
    }
    IMAGE_FORMATS = {
        'PNG': '.png',
        'JPEG': '.jpg',
        'GIF': '.gif',
        'BMP': '.bmp',
        'DIB': '.dib',
        'TIFF': '.tiff',
        'PPM': '.ppm'
    }
    
    error = False

    def __init__(self, json_dir=".", image_dir="."):
        self.json_dir = json_dir
        self.image_dir = image_dir

    def get_set_cards(self, set):
        # セット名をセット名変換表で変換
        if set in self.SET_TABLE.keys():
            set = self.SET_TABLE[set]
        
        # セットjsonファイルが既存ならばそれを返す
        json_path = join(self.json_dir, set+'.json')
        if exists(json_path):
            with open(json_path, encoding='utf-8') as f:
                return json.load(f)
        
        # セットjsonファイルが無ければGathererからセット情報をダウンロードして保存してから返す
        # 検索結果HTMLを取得
        parser = SearchResultParserForAllPages(set)
        search_page = None
        print(parser.url+"を取得中...", flush=True)
        response = requests.get(parser.url)
        if response.status_code == 200:
            search_page = response.text
        if not search_page:
            self.error = True
            return None
        # 検索結果HTMLをパースして全検索結果ページのURLを取得
        paging_links = parser.feed(search_page)
        if paging_links:
            if paging_links[-1][0] == '>':
                page_num = int(paging_links[-2][0])
            elif paging_links[-1][0] == '>>':
                query_string = paging_links[-1][1].split('?')[1]
                queries = query_string.split('&')
                for query in queries:
                    key, value = query.split('=')
                    if key == 'page':
                        page_num = int(value)
                        break
            else:
                page_num = 1
        
        # 全検索結果ページから各カードのmultiverse_idを取得
        # この時点では「英語版のみ」「イラスト違いが含まれない＝セット番号が網羅されていない」「分割カード等でmultiverse_idに重複がある」
        threads = []
        self.search_result_multiverse_ids = []
        for i in range(page_num):
            thread = Thread(target=self.__get_multiverse_id_from_search_result, args=(set, i))
            #thread = Thread(target=self.__get_cards_detail_from_search_result, args=(set, i))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                self.error = True
                break
        if self.error:
            print("An error occured @ __get_multiverse_id_from_search_result")
            return None
        # multiverse_idの重複を削除
        self.search_result_multiverse_ids = list(set(self.search_result_multiverse_ids))

        # 各カードの詳細ページから全variationのmultiverse_idを取得
        threads = []
        self.variation_multiverse_ids = []
        for multiverse_id in self.search_result_multiverse_ids:
            thread = Thread(target=self.__get_variation_multiverse_id_from_detail, args=(multiverse_id))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                self.error = True
                break
        if self.error:
            print("An error occured @ __get_variation_multiverse_id_from_detail")
            return None
        # multiverse_idの重複を削除
        self.variation_multiverse_ids = list(set(self.variation_multiverse_ids))

        #TODO
        # 全variationのmultiverse_idから詳細ページをダウンロードし、カード名、コレクター番号、カード番号を取得する
        threads = []
        self.cards = []
        for multiverse_id in self.variation_multiverse_ids:
            thread = Thread(target=self.__get_cards_detail_from_search_result, args=(multiverse_id))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                self.error = True
                break
        if self.error:
            print("An error occured @ __get_cards_detail_from_search_result")
            return None

        self.search_result_multiverse_ids.sort(key=lambda x: (x.get(Key.MULTIVERSE_ID)))
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.search_result_multiverse_ids, f, indent=4, ensure_ascii=False)
        return self.search_result_multiverse_ids

        # 言語ページをパースした後、カード番号が異なるものは排除する必要がある点に注意
    
    def get_card(self, set, number):
        cards = self.get_set_cards(set)
        for card in cards:
            if card.get(Key.NUMBER) == number:
                return card
        return None

    def get_card_image(self, set, number):
        card = self.get_card(set, number)
        if card:
            # カード画像ファイルが既存ならばそれを返す
            for ext in self.IMAGE_FORMATS.values():
                image_path = join(self.image_dir, card.get(Key.NAME) + ext)
                if exists(image_path):
                    with open(image_path, 'rb') as f:
                        return f.read()
            # カード画像ファイルが無ければダウンロードして保存してから返す
            print(card.get(Key.NAME)+"のカード画像をダウンロード中...")
            response = requests.get(card.get(Key.IMAGE_URL))
            if response.status_code == 200:
                image_data = response.content
                with Image.open(BytesIO(image_data)) as card_image:
                    image_path = join(self.image_dir, card.get(Key.NAME) + self.IMAGE_FORMATS[card_image.format])
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                return image_data
            return None
        return None

    def __get_multiverse_id_from_search_result(self, set, page):
        parser = SearchResultParserForMultiverseIds(set, page)
        print(str(page)+": "+parser.url+"を取得中...", flush=True)
        search_result_page = None
        response = requests.get(parser.url)
        if response.status_code == 200:
            search_result_page = response.text
        if not search_result_page:
            self.error = True
            return None
        multiverse_ids = parser.feed(search_result_page)
        self.search_result_multiverse_ids.extend(multiverse_ids)
    
    def __get_variation_multiverse_id_from_detail(self, multiverse_id):
        parser = DetailParserForVariations(set, multiverse_id)
        print(parser.url+"を取得中...", flush=True)
        detail_page = None
        response = requests.get(parser.url)
        if response.status_code == 200:
            detail_page = response.text
        if not detail_page:
            self.error = True
            return None
        multiverse_ids = parser.feed(detail_page)
        self.variation_multiverse_ids.extend(multiverse_ids)

    def __get_cards_detail_from_search_result(self, set, page):
        parser = SearchResultParserForMultiverseIds(set, page)
        print(str(page)+": "+parser.url+"を取得中...", flush=True)
        search_result_page = None
        response = requests.get(parser.url)
        if response.status_code == 200:
            search_result_page = response.text
        if not search_result_page:
            self.error = True
            return None

        multiverse_ids = parser.feed(search_result_page)
        detail_page_threads = []
        for multiverse_id in multiverse_ids:
            thread = Thread(target=self.__get_card_detail, args=(multiverse_id, page))
            thread.daemon = True
            thread.start()
            detail_page_threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in detail_page_threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive() or self.error:
                self.error = True
                break

    def __get_card_detail(self, multiverse_id, page):
        parser = DetailParserForCardData(multiverse_id)
        print(str(page)+": "+parser.url+"を取得中...", flush=True)
        detail_page = None
        response = requests.get(parser.url)
        if response.status_code == 200:
            detail_page = response.text
        if detail_page:
            card = parser.feed(detail_page)
            card[Key.MULTIVERSE_ID] = multiverse_id
            card[Key.DETAIL_URL] = parser.url
            card[Key.IMAGE_URL] = parser.image_url
            self.search_result_multiverse_ids.append(card)
        else:
            self.error = None

if __name__ == "__main__":
    #param = sys.argv
    set = "NEO"
    gatherer_sdk = GathererSDK()
    cards = gatherer_sdk.get_set_cards(set)
    with open(set+".json", 'w', encoding='utf-8') as f:
        json.dump(cards, f, indent=4, ensure_ascii=False)

