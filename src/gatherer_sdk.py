# Standard Library
import json
from html.parser import HTMLParser
from threading import Thread
from locale import getdefaultlocale
from time import sleep
from os import makedirs
from os.path import exists, join
from io import BytesIO
from re import sub
from logging import StreamHandler, getLogger, DEBUG
from operator import itemgetter

# PyPI
from PIL import Image   # Pillow @ HPND
import requests # requests @ Apache-2.0

from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
disable_warnings(InsecureRequestWarning)

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

logger = getLogger(__name__)
logger.setLevel(DEBUG)
stream_handler = StreamHandler()
stream_handler.setLevel(DEBUG)
logger.addHandler(stream_handler)

def get_queries(url):
    rst = {}
    query_string = url.split('?')[1]
    queries = query_string.split('&')
    for query in queries:
        key, value = query.split('=')
        rst[key] = value
    return rst

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

class QueryKey():
    ACTION = 'action'
    OUTPUT = 'output'
    SORT = 'sort'
    SET = 'set'
    PAGE = 'page'
    MULTIVERSE_ID = 'multiverseid'
    TYPE = 'type'
    OPTIONS = 'options'

class QueryValue():
    ADVANCED = 'advanced'
    STANDARD = 'standard'
    CARD_NUMBER = 'cn+'
    CARD = 'card'
    ROTATE180 = 'rotate180'

class Query():
    ADVANCED_SEARCH = QueryKey.ACTION+'='+QueryValue.ADVANCED
    STANDARD_OUTPUT = QueryKey.OUTPUT+'='+QueryValue.STANDARD
    SORT_BY_CARD_NUMBER = QueryKey.SORT+'='+QueryValue.CARD_NUMBER
    SEARCH_BY_SET =  QueryKey.SET+'=+["{}"]'
    PAGE = QueryKey.PAGE+'={}'
    MULTIVERSE_ID = QueryKey.MULTIVERSE_ID+'={}'
    CARD = QueryKey.TYPE+'='+QueryValue.CARD
    ROTATE180 = QueryKey.OPTIONS+'='+QueryValue.ROTATE180

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

class GathererURL():
    SEARCH_RESULTS = 'https://gatherer.wizards.com/Pages/Search/Default.aspx'
    CARD_DETAIL = 'https://gatherer.wizards.com/Pages/Card/Details.aspx'
    CARD_LANGUAGES = 'https://gatherer.wizards.com/Pages/Card/Languages.aspx'
    CARD_IMAGE = 'https://gatherer.wizards.com/Handlers/Image.ashx'


# 検索結果画面をパースして、全検索結果ページ数を取得する
class SearchResultParserForPageNum(HTMLParser):
    URL = GathererURL.SEARCH_RESULTS+'?'+ \
        Query.ADVANCED_SEARCH+'&'+ \
        Query.STANDARD_OUTPUT+'&'+ \
        Query.SEARCH_BY_SET

    def __init__(self, set_code):
        super().__init__()
        self.url = self.URL.format(set_code)

    def feed(self, data):
        self.found_paging_div = False
        self.found_paging_a = False
        self.paging_links = []  # 2次元配列で、2次元目の0番目の値はリンクテキスト、1番目の値はSearchResultPageのURL
        self.link_text = None
        self.link_url = None
        super().feed(data)
        # 検索結果HTMLをパースして全検索結果ページのURLを取得
        if self.paging_links:
            if self.paging_links[-1][0] == '>':
                page_num = int(self.paging_links[-2][0])
            elif self.paging_links[-1][0] == '>>':
                queries = get_queries(self.paging_links[-1][1])
                page_num = int(queries[QueryKey.PAGE])
            else:
                page_num = 1
        return page_num

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
    URL = GathererURL.SEARCH_RESULTS+'?'+ \
        Query.PAGE+'&'+ \
        Query.ADVANCED_SEARCH+'&'+ \
        Query.STANDARD_OUTPUT+'&'+ \
        Query.SORT_BY_CARD_NUMBER+'&'+ \
        Query.SEARCH_BY_SET
    CARD_IMAGE_LINK_POSTFIX = '_cardImageLink'

    def __init__(self, set_code, page):
        super().__init__()
        self.url = self.URL.format(page, set_code)

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
                multiverse_id = int(queries.get(QueryKey.MULTIVERSE_ID))
                self.multiverse_ids.append(multiverse_id)

# カード詳細ページをパースして、各バリエーションのmultiverseidを取得する
class DetailParserForVariations(HTMLParser):
    URL = GathererURL.CARD_DETAIL+'?'+ \
        Query.MULTIVERSE_ID
    VARIATION_LINKS_POSTFIX = '_variationLinks'
    COMMUNITY_RATINGS_CLASS = 'CommunityRatings'

    def __init__(self, multiverse_id):
        super().__init__()
        self.multiverse_id = multiverse_id
        self.url = self.URL.format(multiverse_id)

    def feed(self, data):
        self.found_variation_links_div = False
        self.multiverse_ids = []
        super().feed(data)
        if len(self.multiverse_ids) == 0:
            self.multiverse_ids.append(self.multiverse_id)
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
                        multiverse_id = int(queries.get(QueryKey.MULTIVERSE_ID))
                        self.multiverse_ids.append(multiverse_id)
                        break

#TODO ページ数を返すようにする
# 言語画面をパースして、全言語ページへのリンクを取得する
class LanguageParserForPageNum(HTMLParser):
    URL = GathererURL.CARD_LANGUAGES+'?'+ \
        Query.MULTIVERSE_ID

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
    URL = GathererURL.CARD_LANGUAGES+'?'+ \
        Query.PAGE+'&'+ \
        Query.MULTIVERSE_ID
    CARD_ITEM_PREFIX = 'cardItem '

    def __init__(self, page, multiverse_id):
        super().__init__()
        self.multiverse_id = multiverse_id
        self.url = self.URL.format(page, multiverse_id)

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
                        multiverse_id = int(queries.get(QueryKey.MULTIVERSE_ID))
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

# カード詳細ページをパースしてカード情報を取得する
class DetailParserForCardData(HTMLParser):
    URL = GathererURL.CARD_DETAIL+'?'+ \
        Query.MULTIVERSE_ID
    IMAGE_URL = GathererURL.CARD_IMAGE+'?'+ \
        Query.MULTIVERSE_ID+'&'+ \
        Query.CARD
    SUBTITLE_POSTFIX = '_SubContentHeader_subtitleDisplay'
    CARD_IMAGE_POSTFIX = '_cardImage'
    NAME_POSTFIX = '_nameRow'
    CARD_NUMBER_POSTFIX = '_numberRow'
    CARD_COMPONENT = '_cardComponent'

    def __init__(self, multiverse_id):
        super().__init__()
        self.multiverse_id = multiverse_id
        self.url = self.URL.format(multiverse_id)
        self.image_url = self.IMAGE_URL.format(multiverse_id)

    def feed(self, data):
        self.found_subtitle_span = False
        self.found_card_number_div = False
        self.found_card_number_value_div = False
        self.found_card_details_table = False
        self.card_component_count = 0
        self.face_type = None
        self.cards = []
        for _ in range(3):
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
        self.cards[0][Key.MULTIVERSE_ID] = self.multiverse_id
        self.cards[0][Key.IMAGE_URL] = self.image_url
        super().feed(data)

        # カード判別
        if ' // ' in self.cards[0][Key.NAME]:
            self.face_type = FaceType.SPLIT
        elif self.multiverse_id != self.cards[1][Key.MULTIVERSE_ID]:
            self.face_type = FaceType.DOUBLE_FACED_SECOND
        elif self.cards[2][Key.NAME]:
            if self.multiverse_id != self.cards[2][Key.MULTIVERSE_ID]:
                self.face_type = FaceType.DOUBLE_FACED_FIRST
            elif Query.ROTATE180 in self.cards[2][Key.IMAGE_URL]:
                self.face_type = FaceType.FLIP
            elif int(sub("\D", "", self.cards[2][Key.CARD_NUMBER])) != self.cards[2][Key.COLLECTOR_NUMBER]:
                self.face_type = FaceType.MELD_SUB
            else:
                self.face_type = FaceType.ADVENTURER
        else:
            self.face_type = FaceType.NORMAL

        results = []
        match self.face_type:
            case FaceType.NORMAL | FaceType.DOUBLE_FACED_FIRST | FaceType.MELD_MAIN | FaceType.MELD_SUB:
                results.append(self.cards[1])
            case FaceType.DOUBLE_FACED_SECOND | FaceType.MELD:
                results.append(self.cards[2])
            case FaceType.SPLIT:
                self.cards[0][Key.IMAGE_URL] = self.cards[0][Key.IMAGE_URL]
                self.cards[0][Key.COLLECTOR_NUMBER] = self.cards[1][Key.COLLECTOR_NUMBER]
                self.cards[0][Key.CARD_NUMBER] = str(self.cards[0][Key.CARD_NUMBER])
                results.append(self.cards[0])
                results.append(self.cards[1])
                results.append(self.cards[2])
            case FaceType.ADVENTURER:
                results.append(self.cards[1])
                results.append(self.cards[2])
            case FaceType.FLIP:
                results.append(self.cards[1])
                results.append(self.cards[2])
            case _:
                results.append(self.cards[1])
        return results

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
                if attr[0] == Attr.ID and self.CARD_COMPONENT in attr[1]:
                    self.card_component_count += 1
                    break
        # カード画像
        if self.card_component_count > 0:
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
                    multiverse_id = int(queries.get(QueryKey.MULTIVERSE_ID))
                    self.cards[self.card_component_count][Key.MULTIVERSE_ID] = multiverse_id
                    self.cards[self.card_component_count][Key.IMAGE_URL] = self.IMAGE_URL.format(multiverse_id)
                    if queries.get(QueryKey.OPTIONS) == QueryValue.ROTATE180:
                        self.cards[self.card_component_count][Key.IMAGE_URL] += '&'+Query.ROTATE180
            if tag == Tag.DIV:
                # カード番号
                if not self.found_card_number_div:
                    for attr in attrs:
                        if attr[0] == Attr.ID and attr[1].endswith(self.CARD_NUMBER_POSTFIX):
                            self.found_card_number_div = True
                            break
                elif self.found_card_number_div and not self.found_card_number_value_div:
                    for attr in attrs:
                        if attr[0] == Attr.CLASS and attr[1] == AttrValue.VALUE:
                            self.found_card_number_value_div = True
                            break
    
    def handle_data(self, data):
        # 表題のカード名
        if self.found_subtitle_span:
            self.cards[0][Key.NAME] = data
            self.found_subtitle_span = False
        # カードコンポーネント
        if self.card_component_count > 0:
            # コレクター番号とカード番号
            if self.found_card_number_div and self.found_card_number_value_div:
                card_number = sub("\s", "", data)
                collector_number = int(sub("\D", "", card_number))
                self.cards[self.card_component_count][Key.CARD_NUMBER] = card_number
                self.cards[self.card_component_count][Key.COLLECTOR_NUMBER] = collector_number
                self.found_card_number_div = False
                self.found_card_number_value_div = False

class GathererSDK():
    LOCALE = getdefaultlocale()[0].replace("_", "-")
    THREAD_INTERVAL_SEC = 0.02
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

    def __init__(self, json_dir="set_json", image_dir="set_image", html_dir="html_cache"):
        self.json_dir = json_dir
        self.image_dir = image_dir
        self.html_dir = html_dir

        # フォルダが存在しなければ作成する
        if not exists(self.json_dir):
            makedirs(self.json_dir)
        if not exists(self.image_dir):
            makedirs(self.image_dir)
        if not exists(self.html_dir):
            makedirs(self.html_dir)
    
    def __get_html(self, path, url):
        html = None
        if exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
        else:
            logger.info(url+"を取得中...")
            try:
                response = requests.get(url, verify=False)
                if response.status_code == 200:
                    html = response.text
            except Exception as e:
                logger.error("An exception occured @ requests.get("+url+")")
                logger.error(e.args)
                return None
            if not html:
                logger.error("No search result page @ requests.get("+url+")")
                return None
            if len(html) > 0:
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    f.write(html)
        return html

    def get_set_cards(self, set_code):
        # セット名をセット名変換表で変換
        if set_code in self.SET_TABLE.keys():
            set_code = self.SET_TABLE[set_code]
        
        # セットjsonファイルが既存ならばそれを返す
        json_path = join(self.json_dir, set_code+'.json')
        if exists(json_path):
            with open(json_path, encoding='utf-8') as f:
                return json.load(f)
        
        # セットjsonファイルが無ければGathererからセット情報をダウンロードして保存してから返す
        # 検索結果HTMLを取得
        parser = SearchResultParserForPageNum(set_code)
        html_path = join(self.html_dir, set_code+'.html')
        html = self.__get_html(html_path, parser.url)
        if not html:
            self.error = True
            return None
        # 検索結果HTMLをパースしてページ数を取得
        page_num = parser.feed(html)
        
        # 全検索結果ページから各カードのmultiverse_idを取得
        # この時点では「英語版のみ」「イラスト違いが含まれない＝セット番号が網羅されていない」「分割カード等でmultiverse_idに重複がある」
        threads = []
        self.search_result_multiverse_ids = []
        for i in range(page_num):
            thread = Thread(target=self.__get_multiverse_id_from_search_result, args=(set_code, i))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                logger.error("Timeout @ __get_multiverse_id_from_search_result")
                self.error = True
                break
        if self.error:
            logger.error("An error occured @ __get_multiverse_id_from_search_result")
            return None
        # multiverse_idの重複を削除
        self.search_result_multiverse_ids = list(set(self.search_result_multiverse_ids))

        # 各カードの詳細ページから全variationのmultiverse_idを取得
        threads = []
        self.variation_multiverse_ids = []
        for multiverse_id in self.search_result_multiverse_ids:
            thread = Thread(target=self.__get_variation_multiverse_ids_from_detail, args=(multiverse_id,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                logger.error("Timeout @ __get_variation_multiverse_id_from_detail")
                self.error = True
                break
        if self.error:
            logger.error("An error occured @ __get_variation_multiverse_id_from_detail")
            return None
        # multiverse_idの重複を削除
        self.variation_multiverse_ids = list(set(self.variation_multiverse_ids))

        # 全variationのmultiverse_idから詳細ページをダウンロードし、カード名、コレクター番号、カード番号を取得する
        threads = []
        self.cards = []
        for multiverse_id in self.variation_multiverse_ids:
            thread = Thread(target=self.__get_cards_detail_from_multiverse_id, args=(multiverse_id, ))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                logger.error("Timeout @ __get_cards_detail_from_multiverse_id")
                self.error = True
                break
        if self.error:
            logger.error("An error occured @ __get_cards_detail_from_multiverse_id")
            return None

        #TODO 言語毎のカード情報
        # 言語ページをパースした後、カード番号が異なるものは排除する必要がある点に注意
        threads = []
        for multiverse_id in self.search_result_multiverse_ids: #言語ページにはバリエーションが含まれるのでsearch_result_multiverse_idsでよい
            thread = Thread(target=self.__get_cards_detail_from_multiverse_id, args=(multiverse_id, ))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            sleep(self.THREAD_INTERVAL_SEC)
        for thread in threads:
            thread.join(self.THREAD_TIMEOUT_SEC)
            if thread.is_alive():
                logger.error("Timeout @ __get_cards_detail_from_multiverse_id")
                self.error = True
                break
        if self.error:
            logger.error("An error occured @ __get_cards_detail_from_multiverse_id")
            return None


        self.cards.sort(key=itemgetter(Key.MULTIVERSE_ID, Key.CARD_NUMBER))
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.cards, f, indent=4, ensure_ascii=False)
        return self.cards

    
    def get_card(self, set_code, number):
        cards = self.get_set_cards(set_code)
        for card in cards:
            if card.get(Key.NUMBER) == number:
                return card
        return None

    def get_card_image(self, set_code, number):
        card = self.get_card(set_code, number)
        if card:
            # カード画像ファイルが既存ならばそれを返す
            for ext in self.IMAGE_FORMATS.values():
                image_path = join(self.image_dir, card.get(Key.NAME) + ext)
                if exists(image_path):
                    with open(image_path, 'rb') as f:
                        return f.read()
            # カード画像ファイルが無ければダウンロードして保存してから返す
            logger.info(card.get(Key.NAME)+"のカード画像をダウンロード中...")
            try:
                response = requests.get(card.get(Key.IMAGE_URL), verify=False)
                if response.status_code == 200:
                    image_data = response.content
            except Exception as e:
                logger.error("An error occured @ get "+card.get(Key.IMAGE_URL))
                logger.error(e)
                return None
            if response.status_code == 200:
                with Image.open(BytesIO(image_data)) as card_image:
                    image_path = join(self.image_dir, card.get(Key.NAME) + self.IMAGE_FORMATS[card_image.format])
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                return image_data
            return None
        return None

    def __get_multiverse_id_from_search_result(self, set_code, page):
        parser = SearchResultParserForMultiverseIds(set_code, page)
        html_path = join(self.html_dir, set_code+'_'+str(page)+'.html')
        html = self.__get_html(html_path, parser.url)
        if not html:
            self.error = True
            return None
        multiverse_ids = parser.feed(html)
        self.search_result_multiverse_ids.extend(multiverse_ids)
    
    def __get_variation_multiverse_ids_from_detail(self, multiverse_id):
        parser = DetailParserForVariations(multiverse_id)
        html_path = join(self.html_dir, str(multiverse_id)+'.html')
        html = self.__get_html(html_path, parser.url)
        if not html:
            self.error = True
            return None
        multiverse_ids = parser.feed(html)
        self.variation_multiverse_ids.extend(multiverse_ids)

    def __get_cards_detail_from_multiverse_id(self, multiverse_id):
        parser = DetailParserForCardData(multiverse_id)
        html_path = join(self.html_dir, str(multiverse_id)+'.html')
        html = self.__get_html(html_path, parser.url)
        if not html:
            self.error = True
            return None

        cards = parser.feed(html)
        self.cards.extend(cards)

if __name__ == "__main__":
    #param = sys.argv
    set_code = "NEO"
    gatherer_sdk = GathererSDK()
    cards = gatherer_sdk.get_set_cards(set_code)
    #print(cards)