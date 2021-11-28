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
thread_num = 100

proxies = {
    'http': proxy,
    'https': proxy
}
headers = {
    'User-Agent': user_agent
}
cookies = {i.split("=")[0]:i.split("=")[-1] for i in cookie.split("; ")}
bidList = []
chapterList = []
threads = []
bidListLock = threading.Lock()
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
        except requests.exceptions.ChunkedEncodingError:
            continue
        else:
            if r.text == '':
                continue
            return r.text
    return False
def getTitle(html):
    d = pq(html)
    return d('.book-meta').children('h1').text()
def getAuthor(html):
    d = pq(html)
    return d('.book-meta').children('p').children('span').children('a').text()
def getVolume(html):
    try:
        html = re.search('(?<=(</a> > ))[.\s\S]*?(?=(</div>))', html, re.I|re.S).group()
        html = html + '</div>'
        html = re.search('(?<=(</a> > ))[.\s\S]*?(?=(</div>))', html, re.I|re.S).group()
        html = html + '</div>'
        html = re.search('(?<=(</a> > ))[.\s\S]*?(?=(</div>))', html, re.I|re.S).group()
        return html
    except:
        return ''
def getChapter(html):
    d = pq(html)
    return d('#mlfy_main_text').children('h1').text()
def setChapterList():
    while True:
        bidListLock.acquire()
        if len(bidList) == 0:
            bidListLock.release()
            break
        else:
            bid = bidList.pop(0)
            bidListLock.release()
        html = get('https://www.linovelib.com/novel/' + str(bid) + '/catalog')
        if html == False:
            bidListLock.acquire()
            bidList.append(bid)
            bidListLock.release()
            continue
        d = pq(html)
        if d('title').text() == '出现错误！哔哩轻小说':
            continue
        title = getTitle(html)
        author = getAuthor(html)
        chapters = d('.chapter-list').children('li').items()
        cid_before = 0
        for c in chapters:
            if c.children('a').attr('href') == 'javascript:cid(0)':
                cid = cid_before + 1
            else:
                cid = int((c.children('a').attr('href')).split('/')[3].split('.')[0])
                cid_before = cid
            chapter = {
                'bid': bid,
                'title': title,
                'author': author,
                'cid': cid
            }
            chapterListLock.acquire()
            chapterList.append(chapter)
            chapterListLock.release()
        print(bid, author, title)
def parseChapterList():
    conn = sqlite3.connect('spider.db')
    cur = conn.cursor()
    while True:
        chapterListLock.acquire()
        curNum = len(chapterList)
        if curNum == 0:
            chapterListLock.release()
            break
        else:
            chapter = chapterList.pop(0)
            chapterListLock.release()
        bid = chapter['bid']
        title = chapter['title']
        author = chapter['author']
        cid = chapter['cid']
        databaseLock.acquire()
        result = cur.execute('SELECT cid FROM libi WHERE cid=?', (str(cid),))
        databaseLock.release()
        if len(list(result)) != 0:
            continue
        html = get('https://www.linovelib.com/novel/' + str(bid) + '/' + str(cid) + '.html')
        # print('https://www.linovelib.com/novel/' + str(bid) + '/' + str(cid) + '.html')
        if html == False:
            chapterListLock.acquire()
            chapterList.append(chapter)
            chapterListLock.release()
            continue
        volume = getVolume(html)
        chapterName = getChapter(html)
        content = ''
        d = pq(html)
        if d('#TextContent').html() == None:
            continue
        page_flag = False
        success_flag = False
        page = 1
        if d('.mlfy_page').children().eq(4).text() == '下一页':
            page_flag = True
        else:
            success_flag = True
        result = re.search('对不起，本章节内容不提供阅读！', html, re.I)
        if result:
            pass
        else:
            h = html2text.HTML2Text()
            content = d('#TextContent').html()
            content = h.handle(content)
            content = content.removesuffix('\n\n')
        while page_flag:
            page = page + 1
            html = get('https://www.linovelib.com/novel/' + str(bid) + '/' + str(cid) + '_' + str(page) + '.html')
            # print('https://www.linovelib.com/novel/' + str(bid) + '/' + str(cid) + '_' + str(page) + '.html')
            if html == False:
                chapterListLock.acquire()
                chapterList.append(chapter)
                chapterListLock.release()
                break
            d = pq(html)
            if d('.mlfy_page').children().eq(4).text() == '下一页':
                page_flag = True
            else:
                page_flag = False
                success_flag = True
            result = re.search('对不起，本章节内容不提供阅读！', html, re.I)
            if result:
                pass
            else:
                h = html2text.HTML2Text()
                if d('#TextContent').html() == None:
                    pass
                else:
                    content = content + '\n\n' + h.handle(d('#TextContent').html()).removesuffix('\n\n')
        if success_flag:
            databaseLock.acquire()
            cur.execute("INSERT OR IGNORE INTO libi (bid, title, author, volume, cid, chapter, content) \
                VALUES (?,?,?,?,?,?,?)", (bid, title, author, volume, cid, chapterName, content))
            conn.commit()
            print('[' + str(int((1 - ((curNum + 1) / totalNum)) * 100)) + '%]', bid, cid, author, title, volume, chapterName)
            databaseLock.release()
    conn.close()

html = get('https://www.linovelib.com/top/postdate/1.html')
d = pq(html)
bidMax = int((d('.rank_d_b_name').children('a').attr('href')).split('/')[2].split('.')[0])
print(bidMax)
for i in range(bidMax):
    bid = i+1
    bidList.append(bid)

for i in range(thread_num):
    thread = threading.Thread(target=setChapterList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()

totalNum = len(chapterList)

for i in range(thread_num):
    thread = threading.Thread(target=parseChapterList)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()
threads.clear()