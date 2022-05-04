from urllib.request import urlopen, Request
from html.parser import HTMLParser
from threading import Thread

class Tag():
    A = 'a'
    DIV = 'div'
    IMG = 'img'
    SPAN = 'span'

class Attr():
    ALT = 'alt'
    CLASS = 'class'
    HREF = 'href'
    ID = 'id'

class AttrValue():
    PAGING = 'paging'
    VALUE = 'value'

class RequestHeader():
    ACCEPT_LANGUAGE = 'Accept-Language'

class RequestHeaderValue():
    JA_JP = 'ja-JP'

class Key():
    NAME = 'name'
    LOCAL_NAME = 'localName'
    NUMBER = 'number'

class SearchPageHTMLParser(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?action=advanced&output=compact&set=[{}]'
    NBSP = '\xa0'

    def __init__(self, set):
        super().__init__()
        self.url = self.URL.format(set)

    def feed(self, data):
        self.found_paging_div = False
        self.found_paging_a = False
        self.paging_links = []  # 2次元配列で、2次元目の0番目の値はリンクテキスト、1番目の値はSearchResultPageのURL
        self.link_text = ""
        self.link_url = ""
        super().feed(data)
        return self.paging_links

    def handle_starttag(self, tag, attrs):
        if not self.found_paging_div and tag == Tag.DIV:
            for attr in attrs:
                if attr[0] == Attr.CLASS and attr[1] == AttrValue.PAGING:
                    self.found_paging_div = True
                    break
        elif self.found_paging_div and tag == Tag.A:
            self.found_paging_a = True
            for attr in attrs:
                if attr[0] == Attr.HREF:
                    self.link_url = attr[1]
    
    def handle_endtag(self, tag):
        if self.found_paging_div and tag == Tag.DIV:
            self.found_paging_div = False
        elif self.found_paging_a and tag == Tag.A:
            self.found_paging_a = False

    def handle_data(self, data):
        if self.found_paging_a:
            self.link_text = data.replace(self.NBSP, "")
            self.paging_links.append([self.link_text, self.link_url])

class SearchResultPageHTMLParser(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?page={}&action=advanced&output=compact&set=[%22{}%22]'
    CARD_PRINTINGS_POSTFIX = '_cardPrintings'

    def __init__(self, set, page):
        super().__init__()
        self.set = set
        self.url = self.URL.format(page, set)

    def feed(self, data):
        self.found_printings_div = False
        self.found_printings_a = False
        self.link_url = ""
        self.multiverse_ids = []
        super().feed(data)
        return self.multiverse_ids

    def handle_starttag(self, tag, attrs):
        if not self.found_printings_div and tag == Tag.DIV:
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.CARD_PRINTINGS_POSTFIX):
                    self.found_printings_div = True
                    break
        elif self.found_printings_div and tag == Tag.A:
            self.found_printings_a = True
            for attr in attrs:
                if attr[0] == Attr.HREF:
                    self.link_url = attr[1]
        elif self.found_printings_a and tag == Tag.IMG:
            for attr in attrs:
                if attr[0] == Attr.ALT and attr[1] == self.set:
                    multiverse_id = self.link_url.split('=')[-1]
                    self.multiverse_ids.append(multiverse_id)
    
    def handle_endtag(self, tag):
        if self.found_printings_div and tag == Tag.DIV:
            self.found_printings_div = False
        elif self.found_printings_a and tag == Tag.A:
            self.found_printings_a = False

class DetailPageHTMLParser(HTMLParser):
    URL = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={}'
    SUBTITLE_POSTFIX = '_subtitleDisplay'
    NAME_POSTFIX = '_nameRow'
    CARD_NUMBER_POSTFIX = '_CardNumberValue'

    def __init__(self, multiverse_id):
        super().__init__()
        self.url = self.URL.format(multiverse_id)

    def feed(self, data):
        self.found_subtitle_span = False
        self.found_name_div = False
        self.found_name_value_div = False
        self.found_card_number_div = False
        self.result = {}
        super().feed(data)
        return self.result

    def handle_starttag(self, tag, attrs):
        if not self.found_subtitle_span and tag == Tag.SPAN:
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.SUBTITLE_POSTFIX):
                    self.found_subtitle_span = True
                    break
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
        if not self.found_card_number_div and tag == Tag.DIV:
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.CARD_NUMBER_POSTFIX):
                    self.found_card_number_div = True
                    break
    
    def handle_data(self, data):
        if self.found_subtitle_span:
            self.result[Key.LOCAL_NAME] = data
            self.found_subtitle_span = False
        if self.found_name_div and self.found_name_value_div:
            self.result[Key.NAME] = data.strip()
            self.found_name_div = False
            self.found_name_value_div = False
        if self.found_card_number_div:
            self.result[Key.NUMBER] = int(data.strip(' \\r\\n'))
            self.found_card_number_div = False

class GathererSDK():
    #search_page_url = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?action=advanced&output=compact&set=[{}]'
    #image_url = 'https://gatherer.wizards.com/Handlers/Image.ashx?multiverseid={}&type=card'
    #detail_page_url = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={}'

    @classmethod
    def get_set_json(cls, set="SNC"):
        results = []
        search_page_parser = SearchPageHTMLParser(set)
        request = Request(search_page_parser.url, headers={RequestHeader.ACCEPT_LANGUAGE: RequestHeaderValue.JA_JP})
        try:
            with urlopen(request) as response:
                charset = response.headers.get_content_charset()
                if charset:
                    search_page = response.read().decode(charset)
                else:
                    search_page = str(response.read())
        except Exception as e:
            print(e)
        if not search_page:
            return None

        paging_links = search_page_parser.feed(search_page)
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
        
        for i in range(page_num):
            search_result_page_parser = SearchResultPageHTMLParser(set, i)
            request = Request(search_result_page_parser.url, headers={RequestHeader.ACCEPT_LANGUAGE: RequestHeaderValue.JA_JP})
            try:
                with urlopen(request) as response:
                    charset = response.headers.get_content_charset()
                    if charset:
                        search_result_page = response.read().decode(charset)
                    else:
                        search_result_page = str(response.read())
            except Exception as e:
                print(e)
            if search_result_page:
                multiverse_ids = search_result_page_parser.feed(search_result_page)
                detail_page_threads = []
                for multiverse_id in multiverse_ids:
                    thread = Thread()   #TODO
                    detail_page_parser = DetailPageHTMLParser(multiverse_id)
                    request = Request(detail_page_parser.url, headers={RequestHeader.ACCEPT_LANGUAGE: RequestHeaderValue.JA_JP})
                    try:
                        with urlopen(request) as response:
                            charset = response.headers.get_content_charset()
                            if charset:
                                detail_page = response.read().decode(charset)
                            else:
                                detail_page = str(response.read())
                    except Exception as e:
                        print(e)
                    if detail_page:
                        card_dict = detail_page_parser.feed(detail_page)
                        print(card_dict)


if __name__ == "__main__":
    #param = sys.argv
    GathererSDK.get_set_json()
