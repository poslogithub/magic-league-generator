import requests
import lxml.html

# WebサイトのURLを指定
url = "https://gatherer.wizards.com/Pages/Search/Default.aspx?action=advanced&output=standard&sort=cn+&set=+[%22NEO%22]"

# Requestsを利用してWebページを取得する
r = requests.get(url, verify=False)

# lxmlを利用してWebページを解析する
html = lxml.html.fromstring(r.content)

# lxmlのfindallを利用して、ヘッドラインのタイトルを取得する
elems = html.findall('.//*[@id="ctl00_ctl00_ctl00_MainContent_SubContent_topPagingControlsContainer"]/')
for elem in elems:
    print(elem.get('href'))
    print(elem.text)
