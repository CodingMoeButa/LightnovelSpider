#!/usr/bin/python3
import requests
from pyquery import PyQuery as pq
import threading
import re
import os
import sqlite3

proxy = 'http://127.0.0.1:10809'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44 LightnovelSpider/1.0'
timeout = 30
retry = 5
thread_num = 10

proxies = {
    'http': proxy,
    'https': proxy
}
headers = {
    'User-Agent': user_agent
}
productList = []
threads = []
productListLock = threading.Lock()
databaseLock = threading.Lock()

def get(url):
    for i in range(retry):
        try:
            r = requests.get(url=url, proxies=proxies, headers=headers, timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        else:
            if r.text == '':
                continue
            return r.text
def getPid(url):
    return re.findall('product-([0-9]*)\.html', url)[0]
def getTitle(html):
    d = pq(html)
    return re.findall('《(.*)》', d('h1.goodsname').text())[0]
def getAuthor(html):
    text = re.search('(?<=(作者：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if text == None:
        return ''
    text = text.group()
    text = text.replace('（', '')
    text = text.replace('）', '')
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace('日', '')
    text = text.removeprefix(' ')
    text = text.removeprefix(' ')
    text = text.removesuffix(' ')
    return text
def getIllustrator(html):
    text = re.search('(?<=(插画：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if text == None:
        return ''
    text = text.group()
    text = text.replace('（', '')
    text = text.replace('）', '')
    text = text.replace('(', '')
    text = text.replace(')', '')
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace('日', '')
    text = text.removeprefix(' ')
    text = text.removeprefix(' ')
    text = text.removesuffix(' ')
    return text
def getPublisher(html):
    text = re.search('(?<=(出版社：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if text == None:
        return ''
    text = text.group()
    text = text.removeprefix(' ')
    text = text.removesuffix(' ')
    return text
def getYear(html):
    pretext = re.search('(?<=(出版时间：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if pretext == None:
        return ''
    pretext = pretext.group()
    text = re.search('(?<=( ))[.\s\S]*?(?=(-))', pretext, re.S|re.M)
    if text == None:
        pass
    else:
        text = text.group()
        return text
    text = re.search('(?<=( ))[.\s\S]*?(?=(年))', pretext, re.S|re.M)
    if text == None:
        pass
    else:
        text = text.group()
        return text
    return ''
def getMonth(html):
    pretext = re.search('(?<=(出版时间：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if pretext == None:
        return ''
    pretext = pretext.group()
    text = re.search('(?<=(-))[.\s\S]*?(?=( ))', pretext, re.S|re.M)
    if text == None:
        pass
    else:
        text = text.group()
        text = text.removeprefix('0')
        return text
    text = re.search('(?<=(年))[.\s\S]*?(?=(月))', pretext, re.S|re.M)
    if text == None:
        pass
    else:
        text = text.group()
        text = text.removeprefix('0')
        return text
    return ''
def getISBN(html):
    text = re.search('(?<=(ISBN：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if text == None:
        return ''
    text = text.group()
    text = text.replace('-', '')
    text = text.replace(' ', '')
    return text
def getDescription(html):
    d = pq(html)
    paragraphs = d('div.body.indent.uarea-output')
    d = pq(paragraphs)
    paragraphs = d('p,font').items()
    index = 0
    flag1 = 0
    flag2 = -1
    for paragraph in paragraphs:
        result = re.search('内容简介', paragraph.html(), re.S|re.M)
        if result == None:
            pass
        else:
            flag1 = index
        result = re.search('作者简介', paragraph.html(), re.S|re.M)
        if result == None:
            index+=1
            continue
        else:
            flag2 = index
    html = ''
    if flag2 == -1:
        for i in range(flag1+1, index):
            html = html + d('p,font').eq(i).text() + '\n'
    else:
        for i in range(flag1+1, flag2-1):
            html = html + d('p,font').eq(i).text() + '\n'
    textList = html.splitlines(True)
    formatList = list(set(textList))
    formatList.sort(key=textList.index)
    if formatList.count('\n') == 1:
        formatList.remove('\n')
    for i in range(0,len(formatList)-1):
        if len(formatList[i]) <= 5:
            formatList[i-1] = formatList[i-1].replace('\n', '')
    text = ''
    for t in formatList:
        text = text + t
    text = text.removesuffix('\n')
    return text.replace('\n', '\n\n')
def getImage(pid, html):
    d = pq(html)
    url = d('div.goods-detail-pic').attr('bigpicsrc')
    for i in range(retry):
        try:
            r = requests.get(url=url, proxies=proxies, headers=headers, timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        else:
            if os.path.exists('./img/kadokawa_cn/'+str(int(int(pid)/10000))) == False:
                os.mkdir('./img/kadokawa_cn/'+str(int(int(pid)/10000)))
            f = open('./img/kadokawa_cn/'+str(int(int(pid)/10000))+'/'+pid+'.jpg', 'wb')
            f.write(r.content)
            f.close()
            break
def run():
    conn = sqlite3.connect('spider.db')
    cur = conn.cursor()
    while True:
        productListLock.acquire()
        if len(productList) == 0:
            productListLock.release()
            break
        else:
            url = productList.pop()
            productListLock.release()
        pid = getPid(url)
        # databaseLock.acquire()
        result = cur.execute('SELECT pid FROM kadokawa_cn WHERE pid=?', (pid,))
        # databaseLock.release()
        if len(list(result)) != 0:
            continue
        html = get(url)
        title = getTitle(html)
        author = getAuthor(html)
        illustrator = getIllustrator(html)
        publisher = getPublisher(html)
        release_year = getYear(html)
        release_month = getMonth(html)
        isbn = getISBN(html)
        description = getDescription(html)
        getImage(pid, html)
        databaseLock.acquire()
        cur.execute("INSERT INTO kadokawa_cn (pid, title, author, illustrator, publisher, release_year, release_month, isbn, description) \
            VALUES (?,?,?,?,?,?,?,?,?)", (pid, title, author, illustrator, publisher, release_year, release_month, isbn, description))
        conn.commit()
        print(pid, author, title)
        databaseLock.release()
    conn.close()

html = get('http://www.gztwkadokawa.com/?gallery-2-grid.html')
d = pq(html)
pageall = int(d('span.pageall').text())
print(pageall)

for i in range(pageall):
    page = i+1
    html = get('http://www.gztwkadokawa.com/?gallery-2--0--'+str(page)+'--grid.html')
    d = pq(html)
    products = d('a.entry-title').items()
    for product in products:
        productList.append('http://www.gztwkadokawa.com/' + product.attr('href'))
    print(page)

for i in range(thread_num):
    thread = threading.Thread(target=run)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()