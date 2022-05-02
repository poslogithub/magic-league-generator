from urllib.request import urlopen
from urllib.parse import quote
from html.parser import HTMLParser
from enum import Enum

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

    def __init__(self, set):
        super().__init__()
        self.set = set
        self.url = self.URL.format('{}', set)

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
    CARD_NUMBER_POSTFIX = '_CardNumberValue'

    def __init__(self, multiverse_id):
        super().__init__()
        self.url = self.URL.format(multiverse_id)

    def feed(self, data):
        self.found_subtitle_span = False
        self.found_card_number_div = False
        self.name = ""
        self.number = 0
        super().feed(data)
        return self.name, self.number

    def handle_starttag(self, tag, attrs):
        if not self.found_subtitle_span and tag == Tag.SPAN:
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.SUBTITLE_POSTFIX):
                    self.found_subtitle_span = True
                    break
        elif not self.found_card_number_div and tag == Tag.DIV:
            for attr in attrs:
                if attr[0] == Attr.ID and attr[1].endswith(self.CARD_NUMBER_POSTFIX):
                    self.found_card_number_div = True
                    break
    
    def handle_endtag(self, tag):
        if self.found_subtitle_span and tag == Tag.SPAN:
            self.found_subtitle_span = False
        elif self.found_card_number_div and tag == Tag.DIV:
            self.found_card_number_div = False

    def handle_data(self, data):
        if self.found_subtitle_span:
            self.name = data.strip()
        elif self.found_card_number_div:
            self.number = int(data.strip(' \\r\\n'))

class GathererSDK():
    #search_page_url = 'https://gatherer.wizards.com/Pages/Search/Default.aspx?action=advanced&output=compact&set=[{}]'
    #image_url = 'https://gatherer.wizards.com/Handlers/Image.ashx?multiverseid={}&type=card'
    #detail_page_url = 'https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={}'

    @classmethod
    def get_set_json(cls, set="SNC"):
        search_page_parser = SearchPageHTMLParser(set)

        try:
            with urlopen(url=search_page_parser.url) as response:
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
        
        search_result_page_parser = SearchResultPageHTMLParser(set)
        search_result_page_urls = []
        for i in range(page_num):
            url = search_result_page_parser.url.format(str(i))
            search_result_page_urls.append(url)
        for url in search_result_page_urls:
            try:
                with urlopen(url=url) as response:
                    search_result_page = str(response.read())
            except Exception as e:
                print(e)
            if search_result_page:
                multiverse_ids = search_result_page_parser.feed(search_result_page)
                for multiverse_id in multiverse_ids:
                    detail_page_parser = DetailPageHTMLParser(multiverse_id)
                    try:
                        with urlopen(url=detail_page_parser.url) as response:
                            detail_page = str(response.read())
                    except Exception as e:
                        print(e)
                    if detail_page:
                        name, number = detail_page_parser.feed(detail_page)
                        print(name, number)


if __name__ == "__main__":
    #param = sys.argv
    GathererSDK.get_set_json()
