#!/usr/bin/python3
#coding=utf-8
import sqlite3
import markdown
from pyquery import PyQuery as pq
import requests
import threading
import os

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
chapterList = []
imageList = []
threads = []
imageListLock = threading.Lock()

def getImage(imageInfo):
    cid = imageInfo['cid']
    imageName = imageInfo['imageName']
    imageLink = imageInfo['imageLink']
    for i in range(retry):
        try:
            r = requests.get(url=imageLink, proxies=proxies, headers=headers, timeout=timeout)
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
            if os.path.exists('./img/wenku8/' + str(int(int(cid)/10000))) == False:
                try:
                    os.mkdir('./img/wenku8/' + str(int(int(cid)/10000)))
                except FileExistsError:
                    pass
            if os.path.exists('./img/wenku8/' + str(int(int(cid)/10000)) + '/' + cid) == False:
                try:
                    os.mkdir('./img/wenku8/' + str(int(int(cid)/10000)) + '/' + cid)
                except FileExistsError:
                    pass
            f = open('./img/wenku8/' + str(int(int(cid)/10000)) + '/' + cid + '/' + imageName, 'wb')
            f.write(r.content)
            f.close()
            return True
    return False
def operateTask():
    while True:
        imageListLock.acquire()
        if len(imageList) == 0:
            imageListLock.release()
            return
        else:
            imageInfo = imageList.pop(0)
            imageListLock.release()
        cid = imageInfo['cid']
        imageName = imageInfo['imageName']
        if os.path.exists('./img/wenku8/' + str(int(int(cid)/10000)) + '/' + cid + '/' + imageName) == True:
            continue
        if getImage(imageInfo) == False:
            imageListLock.acquire()
            imageList.append(imageInfo)
            imageListLock.release()
        else:
            print('./img/wenku8/' + str(int(int(cid)/10000)) + '/' + cid + '/' + imageName)

conn = sqlite3.connect('spider.db')
cur = conn.cursor()
result = cur.execute("SELECT cid,content FROM wenku8 WHERE subtitle LIKE '%插图%'")
for row in result:
    cid = row[0]
    content = row[1]
    chapter = {
        'cid': str(cid),
        'content': content
    }
    if content != '':
        chapterList.append(chapter)
        print(cid)
conn.close()

for chapter in chapterList:
    cid = chapter['cid']
    content = chapter['content']
    html = markdown.markdown(content)
    d = pq(html)
    images = d('img').items()
    for image in images:
        imageLink = image.attr('src')
        imageName = imageLink.split('/')[-1]
        imageInfo = {
            'cid': cid,
            'imageName': imageName,
            'imageLink': imageLink
        }
        imageList.append(imageInfo)
        print(imageInfo)

for i in range(thread_num):
    thread = threading.Thread(target=operateTask)
    threads.append(thread)
for i in range(thread_num):
    threads[i].start()
for i in range(thread_num):
    threads[i].join()