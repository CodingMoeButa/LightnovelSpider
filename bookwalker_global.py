#!/usr/bin/python3
#coding=utf-8
import requests
from pyquery import PyQuery as pq
import threading
import re
import os
import sqlite3
import html2text
import time

proxy = 'http://127.0.0.1:10809'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44 LightnovelSpider/1.0'
cookie = ""
timeout = 30
retry = 5
thread_num = 5

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
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.ProxyError:
            continue
        except requests.exceptions.ChunkedEncodingError:
            continue
        else:
            if r.text == '':
                continue
            return r.text
    return False
def getImage(pid):
    url = 'https://c.bookwalker.jp/' + pid + '/t_700x780.jpg'
    for i in range(retry):
        try:
            r = requests.get(url=url, proxies=proxies, headers=headers, timeout=timeout, cookies=cookies)
        except requests.exceptions.ConnectTimeout:
            continue
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.SSLError:
            continue
        except requests.exceptions.ConnectionError:
            continue
        except requests.exceptions.ProxyError:
            continue
        except requests.exceptions.ChunkedEncodingError:
            continue
        else:
            if os.path.exists('./img/bookwalker_global/'+str(int(int(pid)/10000))) == False:
                try:
                    os.mkdir('./img/bookwalker_global/'+str(int(int(pid)/10000)))
                except FileExistsError:
                    pass
            f = open('./img/bookwalker_global/'+str(int(int(pid)/10000))+'/'+pid+'.jpg', 'wb')
            f.write(r.content)
            f.close()
            return True
    return False
def getTitle(html):
    d = pq(html)
    return d('h1[itemprop=name]').text().replace(d('h1[itemprop=name]').children('span').text(), '').removesuffix(' ')
def getAuthor(html):
    d = pq(html)
    items = d('table.product-detail').find('th').items()
    i = -1
    find_flag = False
    for item in items:
        i = i + 1
        if item.text() == 'Author':
            find_flag = True
            break
    if find_flag == False:
        i = -1
        items = d('table.product-detail').find('th').items()
        for item in items:
            i = i + 1
            if item.text() == 'By (author)':
                find_flag = True
                break
    if find_flag == True:
        return d('table.product-detail').find('td').eq(i).children('a').text()
    else:
        return ''
def getIllustrator(html):
    d = pq(html)
    items = d('table.product-detail').find('th').items()
    i = -1
    find_flag = False
    for item in items:
        i = i + 1
        if item.text() == 'Artist':
            find_flag = True
            break
    if find_flag == False:
        i = -1
        items = d('table.product-detail').find('th').items()
        for item in items:
            i = i + 1
            if item.text() == 'By (artist)':
                find_flag = True
                break
    if find_flag == True:
        return d('table.product-detail').find('td').eq(i).children('a').text()
    else:
        return ''
def getPublisher(html):
    d = pq(html)
    items = d('table.product-detail').find('th').items()
    i = -1
    for item in items:
        i = i + 1
        if item.text() == 'Publisher':
            break
    if i != -1:
        return d('table.product-detail').find('td').eq(i).find('a').text()
    else:
        return ''
def getDate(html):
    d = pq(html)
    items = d('table.product-detail').find('th').items()
    i = -1
    for item in items:
        i = i + 1
        if item.text() == 'Available since':
            break
    if i != -1:
        timeStr = d('table.product-detail').find('td').eq(i).find('span').text().split('(')[0].removesuffix(' ')
        release_date = time.strptime(timeStr, '%B %d, %Y')
        year = str(release_date[0])
        month = str(release_date[1])
        day = str(release_date[2])
        return (year, month, day)
    else:
        return ('', '', '')
def getDescription(html):
    d = pq(html)
    content = d('div[itemprop=description]').text()
    description = content.replace('\n\n', '\n').replace('\n', '\n\n').removesuffix('\n\n')
    return description
def setProductList():
    while True:
        pageListLock.acquire()
        curNum = len(pageList)
        if curNum == 0:
            pageListLock.release()
            break
        else:
            url = pageList.pop()
            pageListLock.release()
        html = get(url)
        if html == False:
            pageListLock.acquire()
            pageList.insert(0, url)
            pageListLock.release()
            continue
        d = pq(html)
        products = d('div.o-tile-book-info').items()
        for product in products:
            pid = product.find('img.lazy').attr('data-srcset').split('/')[3]
            link = product.find('h2.a-tile-ttl').children('a').attr('href')
            productInfo = {
                'pid': pid,
                'link': link
            }
            productListLock.acquire()
            productList.append(productInfo)
            productListLock.release()
        print('[' + str(int((1 - ((curNum + 1) / totalNum)) * 100)) + '%]', url)
def parseProductList():
    conn = sqlite3.connect('spider.db')
    cur = conn.cursor()
    while True:
        productListLock.acquire()
        curNum = len(productList)
        if curNum == 0:
            productListLock.release()
            break
        else:
            productInfo = productList.pop(0)
            productListLock.release()
        pid = productInfo['pid']
        link = productInfo['link']
        databaseLock.acquire()
        result = cur.execute('SELECT pid FROM bookwalker_global WHERE pid=?', (pid,))
        databaseLock.release()
        if len(list(result)) != 0:
            continue
        html = get(link)
        if html == False:
            productListLock.acquire()
            productList.append(productInfo)
            productListLock.release()
            continue
        title = getTitle(html)
        if title == '':
            continue
        if getImage(pid) == False:
            productListLock.acquire()
            productList.append(productInfo)
            productListLock.release()
            continue
        author = getAuthor(html)
        illustrator = getIllustrator(html)
        publisher = getPublisher(html)
        date = getDate(html)
        year = date[0]
        month = date[1]
        day = date[2]
        description = getDescription(html)
        databaseLock.acquire()
        cur.execute("INSERT INTO bookwalker_global (pid, title, author, illustrator, publisher, release_year, release_month, release_day, description) \
            VALUES (?,?,?,?,?,?,?,?,?)", (pid, title, author, illustrator, publisher, year, month, day, description))
        conn.commit()
        print('[' + str(int((1 - ((curNum + 1) / totalNum)) * 100)) + '%]', pid, author, title)
        databaseLock.release()
    conn.close()

html = get('https://global.bookwalker.jp/categories/3/?np=1&order=release')
d = pq(html)
pageall = int(d('div.pager-area').children('ul').children('li').eq(-2).children('a').text())
print(pageall)
for i in range(pageall):
    page = i + 1
    url = 'https://global.bookwalker.jp/categories/3/?np=1&order=release&page=' + str(page)
    pageList.append(url)

totalNum = len(pageList)

for i in range(thread_num):
    thread = threading.Thread(target=setProductList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()

totalNum = len(productList)

for i in range(thread_num):
    thread = threading.Thread(target=parseProductList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()