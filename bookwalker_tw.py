#!/usr/bin/python3
#coding=utf-8
import requests
from pyquery import PyQuery as pq
import threading
import re
import os
import sqlite3

proxy = 'http://127.0.0.1:10809'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44 LightnovelSpider/1.0'
cookie = ""
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
cookies = {i.split("=")[0]:i.split("=")[-1] for i in cookie.split("; ")}
pageList = []
productList = []
threads = []
pageListLock = threading.Lock()
productListLock = threading.Lock()
databaseLock = threading.Lock()

def get(url):
    for i in range(retry):
        try:
            r = requests.get(url=url, proxies=proxies, headers=headers, timeout=timeout, cookies=cookies)
        except requests.exceptions.ConnectTimeout:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.SSLError:
            continue
        else:
            if r.text == '':
                continue
            return r.text
def getImage(pid, html):
    d = pq(html)
    url = d('a.imgw200').attr('href')
    for i in range(retry):
        try:
            r = requests.get(url=url, proxies=proxies, headers=headers, timeout=timeout, cookies=cookies)
        except requests.exceptions.ConnectTimeout:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.SSLError:
            continue
        else:
            if os.path.exists('./img/bookwalker_tw/'+str(int(int(pid)/10000))) == False:
                os.mkdir('./img/bookwalker_tw/'+str(int(int(pid)/10000)))
            f = open('./img/bookwalker_tw/'+str(int(int(pid)/10000))+'/'+pid+'.jpg', 'wb')
            f.write(r.content)
            f.close()
            break
def getPid(url):
    return re.findall('product/([0-9]*)', url)[0]
def getTitle(html):
    d = pq(html)
    title = d('div.bwname').children('h2').text()
    title = title + d('div.booktitle.clearfix').children('h3').text()
    return title
def getAuthor(html):
    d = pq(html)
    if d('dl.writer_data.clearfix').children('dt').eq(0).text() == '作者：':
        return d('dl.writer_data.clearfix').find('a').eq(0).text()
    else:
        return ''
def getIllustrator(html):
    d = pq(html)
    if d('dl.writer_data.clearfix').children('dt').eq(1).text() == '插畫：':
        return d('dl.writer_data.clearfix').find('a').eq(1).text()
    else:
        return ''
def getTranslator(html):
    d = pq(html)
    if d('dl.writer_data.clearfix').children('dt').eq(2).text() == '譯者：':
        return d('dl.writer_data.clearfix').find('a').eq(2).text()
    else:
        return ''
def getPublisher(html):
    d = pq(html)
    for i in range(0,2):
        if d('div.bookinfo_more.clearfix').find('li').eq(i).children('span.title').text() == '出版社：':
            return d('div.bookinfo_more.clearfix').find('li').eq(i).children('a').text()
    return ''
def getYear(html):
    d = pq(html)
    for i in range(1,3):
        if d('div.bookinfo_more.clearfix').find('li').eq(i).children('span.title').text() == '發售日：':
            date = d('div.bookinfo_more.clearfix').find('li').eq(i).text()
            year = re.search('(?<=( ))[.\s\S]*?(?=(年))', date, re.S|re.M).group()
            return year
    return ''
def getMonth(html):
    d = pq(html)
    for i in range(1,3):
        if d('div.bookinfo_more.clearfix').find('li').eq(i).children('span.title').text() == '發售日：':
            date = d('div.bookinfo_more.clearfix').find('li').eq(i).text()
            month = re.search('(?<=(年 ))[.\s\S]*?(?=(月))', date, re.S|re.M).group()
            return month.removeprefix('0')
    return ''
def getDay(html):
    d = pq(html)
    for i in range(1,3):
        if d('div.bookinfo_more.clearfix').find('li').eq(i).children('span.title').text() == '發售日：':
            date = d('div.bookinfo_more.clearfix').find('li').eq(i).text()
            day = re.search('(?<=(月 ))[.\s\S]*?(?=(日))', date, re.S|re.M).group()
            return day.removeprefix('0')
    return ''
def getISBN(html):
    text = re.search('(?<=(ISBN：</span>))[.\s\S]*?(?=(</li>))', html, re.S|re.M)
    if text == None:
        return ''
    text = text.group()
    text = text.replace('\n', '')
    text = text.replace(' ', '')
    return text
def getDescription(html):
    d = pq(html)
    text = d('div.product-introduction-container').text()
    text = text.replace('\n\n', '\n')
    text = text.replace('\n', '\n\n')
    return text
def setProductList():
    while True:
        pageListLock.acquire()
        if len(pageList) == 0:
            pageListLock.release()
            break
        else:
            url = pageList.pop()
            pageListLock.release()
        html = get(url)
        d = pq(html)
        products = d('div.bookitem').items()
        for product in products:
            productListLock.acquire()
            productList.append(product.children('a').attr('href'))
            productListLock.release()
        print(url)
def parseProduct():
    conn = sqlite3.connect('spider.db')
    cur = conn.cursor()
    while True:
        productListLock.acquire()
        if len(productList) == 0:
            productListLock.release()
            break
        else:
            url = productList.pop(0)
            productListLock.release()
        pid = getPid(url)
        # databaseLock.acquire()
        result = cur.execute('SELECT pid FROM bookwalker_tw WHERE pid=?', (pid,))
        # databaseLock.release()
        if len(list(result)) != 0:
            continue
        html = get(url)
        d = pq(html)
        if d('title').text() == '404 您所瀏覽的網頁(檔案)不存在 - BOOK☆WALKER TAIWAN 台灣漫讀':
            continue
        title = getTitle(html)
        author = getAuthor(html)
        illustrator = getIllustrator(html)
        translator = getTranslator(html)
        publisher = getPublisher(html)
        release_year = getYear(html)
        release_month = getMonth(html)
        release_day = getDay(html)
        isbn = getISBN(html)
        description = getDescription(html)
        getImage(pid, html)
        databaseLock.acquire()
        cur.execute("INSERT INTO bookwalker_tw (pid, title, author, illustrator, translator, publisher, release_year, release_month, release_day, isbn, description) \
            VALUES (?,?,?,?,?,?,?,?,?,?,?)", (pid, title, author, illustrator, translator, publisher, release_year, release_month, release_day, isbn, description))
        conn.commit()
        print(pid, author, title)
        databaseLock.release()
    conn.close()

html = get('https://www.bookwalker.com.tw/search?m=3&order=sell_desc&page=1')
d = pq(html)
pageall = int(d('ul.bw_pagination.text-center').children('li.hidden-xs').children('a').eq(0).text())
print(pageall)
for i in range(pageall):
    page = i+1
    pageList.append('https://www.bookwalker.com.tw/search?m=3&order=sell_desc&page='+str(page))

for i in range(thread_num):
    thread = threading.Thread(target=setProductList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()

for i in range(thread_num):
    thread = threading.Thread(target=parseProduct)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()