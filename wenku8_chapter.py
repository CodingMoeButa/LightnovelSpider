#!/usr/bin/python3
#coding=utf-8
import requests
from pyquery import PyQuery as pq
import threading
import re
import os
import sqlite3
import html2text

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
aidList = []
chapterList = []
threads = []
pageListLock = threading.Lock()
aidListLock = threading.Lock()
chapterListLock = threading.Lock()
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
        else:
            if r.text == '':
                continue
            r.encoding = 'gbk'
            return r.text
    return False
def getTitle(html):
    d = pq(html)
    return d('div#title').text()
def getAuthor(html):
    d = pq(html)
    return d('div#info').text().replace('作者：', '')
def getSubtitle(html):
    d = pq(html)
    return d('div#title').text()
def setAidList():
    while True:
        pageListLock.acquire()
        if len(pageList) == 0:
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
        aids = d('a[style="font-size:13px;"]').items()
        for a in aids:
            aidListLock.acquire()
            aidList.append(re.search('(?<=(book/))[.\s\S]*?(?=(.htm))', a.attr('href')).group())
            aidListLock.release()
        print(url)
def setChapterList():
    while True:
        aidListLock.acquire()
        if len(aidList) == 0:
            aidListLock.release()
            break
        else:
            aid = aidList.pop(0)
            aidListLock.release()
        html = get('https://www.wenku8.net/modules/article/reader.php?aid=' + aid)
        if html == False:
            aidListLock.acquire()
            aidList.append(aid)
            aidListLock.release()
            continue
        d = pq(html)
        title = getTitle(html)
        author = getAuthor(html)
        chapters = d('td.ccss').children('a').items()
        for c in chapters:
            chapterLink = c.attr('href')
            cid = chapterLink.split('cid=')[1]
            chapter = {
                'aid': aid,
                'title': title,
                'author': author,
                'cid': cid
            }
            chapterListLock.acquire()
            chapterList.append(chapter)
            chapterListLock.release()
        print(aid, author, title)
def parseChapter():
    conn = sqlite3.connect('spider.db')
    cur = conn.cursor()
    while True:
        chapterListLock.acquire()
        if len(chapterList) == 0:
            chapterListLock.release()
            break
        else:
            chapter = chapterList.pop(0)
            chapterListLock.release()
        aid = chapter['aid']
        title = chapter['title']
        author = chapter['author']
        cid = chapter['cid']
        # databaseLock.acquire()
        result = cur.execute('SELECT cid FROM wenku8 WHERE cid=?', (cid,))
        # databaseLock.release()
        if len(list(result)) != 0:
            continue
        html = get('https://www.wenku8.net/modules/article/reader.php?aid=' + aid + '&cid=' + cid)
        if html == False:
            chapterListLock.acquire()
            chapterList.append(chapter)
            chapterListLock.release()
            continue
        subtitle = getSubtitle(html)
        result = re.search('因版权问题，文库不再提供该小说的阅读！', html, re.I)
        if result:
            content = ''
        else:
            result = re.search('(?<=(</ul>))[.\s\S]*?(?=(<ul id="contentdp">))', html, re.I|re.S)
            content = result.group()
            content = content.replace('&nbsp;&nbsp;&nbsp;&nbsp;', '')
            h = html2text.HTML2Text()
            content = h.handle(content)
            content = content.removesuffix('\n\n')
        databaseLock.acquire()
        cur.execute("INSERT INTO wenku8 (aid, title, author, cid, subtitle, content) \
            VALUES (?,?,?,?,?,?)", (aid, title, author, cid, subtitle, content))
        conn.commit()
        print(aid, cid, author, title, subtitle)
        databaseLock.release()
    conn.close()

html = get('https://www.wenku8.net/modules/article/articlelist.php')
d = pq(html)
pageall = int(d('a.last').text())
print(pageall)
for i in range(pageall):
    page = i+1
    pageList.append('https://www.wenku8.net/modules/article/articlelist.php?page=' + str(page))

for i in range(thread_num):
    thread = threading.Thread(target=setAidList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()

for i in range(thread_num):
    thread = threading.Thread(target=setChapterList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()

for i in range(thread_num):
    thread = threading.Thread(target=parseChapter)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()