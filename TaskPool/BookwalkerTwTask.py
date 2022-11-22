#!/usr/bin/python3
#coding=utf-8
'''任务：台湾漫读'''
import os
import json
import html2text
from pyquery import PyQuery
from AddressPool import Req,ReqQueue
from Downloader import Res
from DataPool import MySQL
from logger import LogLevel

def init(reqQueue:ReqQueue):
    reqQueue.push(Req('https://www.bookwalker.com.tw/search?m=3&order=sell_desc&page=1', 'init'))

def parse(res:Res, mysql:MySQL, reqQueue:ReqQueue, flag:bool, log) -> bool:
    if not res.response.ok:
        log(res.req.url+' '+str(res.response.status_code)+' '+res.response.reason, LogLevel.WARN)
        reqQueue.push(res.req)
        return flag
    res.response.encoding = 'utf-8'
    d = PyQuery(res.response.text)

    def formatDate(dateStr:str) -> tuple:
        year=month=day = None
        if dateStr.find('年') > -1:
            year = int(dateStr.split('年')[0].strip(' '))
            if dateStr.find('月') > -1:
                month = int(dateStr.split('年')[1].split('月')[0].strip(' '))
                if dateStr.find('日') > -1:
                    day = int(dateStr.split('年')[1].split('月')[1].split('日')[0].strip(' '))
        return (year,month,day)
    def formatNum(numS:str) -> int:
        s = ''
        for c in numS:
            if c.isdigit():
                s = s + c
        return int(s)
    def formatTag(tagStr:str) -> tuple:
        t = ''
        s = 2
        tags = tagStr.strip(' ').split(' / ')
        for tag in tags:
            if tag == '限制級':
                s = 1
                tags.remove(tag)
        for tag in tags:
            if tag == 'EP同步':
                tags.remove(tag)
        for tag in tags:
            if tag == '先行發售':
                tags.remove(tag)
        for tag in tags:
            if tag == '贈品':
                tags.remove(tag)
        for tag in tags:
            if tag == '特別內容':
                tags.remove(tag)
        for tag in tags:
            if tag == '租書':
                tags.remove(tag)
        for tag in tags:
            if tag == '動畫化':
                tags.remove(tag)
        for tag in tags:
            if tag == '已完結':
                tags.remove(tag)
        for tag in tags:
            if tag == '得獎作':
                tags.remove(tag)
        for tag in tags:
            if tag == '漫畫改編':
                tags.remove(tag)
        for tag in tags:
            if tag == '這本輕小說最厲害！':
                tags.remove(tag)
        for tag in tags:
            if tag == '外傳類型':
                tags.remove(tag)
        for tag in tags:
            if tag == '外傳':
                tags.remove(tag)
        for tag in tags:
            if tag == '電子限定':
                tags.remove(tag)
        for tag in tags:
            if tag == '改編作':
                tags.remove(tag)
        for tag in tags:
            if tag == '動畫改編':
                tags.remove(tag)
        for tag in tags:
            if tag == '漫畫化':
                tags.remove(tag)
        if len(tags) > 0:
            t = ','.join(tags).replace('戀愛喜劇', '戀愛,喜劇').replace('幽默搞笑', '幽默,搞笑').replace('靈異神怪', '靈異,神怪')
        return (t,s)

    if res.req.tag == 'init':
        maxPage = int(d('ul.bw_pagination.text-center').children('li.hidden-xs').children('a').eq(0).text())
        for i in range(maxPage):
            page = i+1
            reqQueue.push(Req('https://www.bookwalker.com.tw/search?m=3&order=sell_desc&page='+str(page), 'page'))
        return True
    elif res.req.tag == 'page':
        for div in d('div.bookitem').items():
            url = div.children('a').attr('href')
            pid = int(url.split('/')[-1])
            if mysql.selectOne('SELECT pid FROM bookwalker_tw_products WHERE pid=%s', (pid,)) != None:
                continue
            reqQueue.push(Req(url, 'pid'))
        return False
    elif res.req.tag == 'pid':
        pid = int(res.req.url.split('/')[-1])
        title = d('div.bwname').children('h2').text()
        if title == '' or title == None:
            reqQueue.push(res.req)
            log(res.req.url+' 内容解析失败，将会重载该页。网页内容如下：\n'+res.response.text, LogLevel.WARN)
            return flag
        subtitle = d('div.booktitle.clearfix').children('h3').text()
        if subtitle != '' and subtitle != None:
            title = title + ' ' + subtitle
        author=illustrator=translator=publisher=tag=description=sname = ''
        release_year=release_month=release_day=ean=page_count=price=sid = None
        currency = 'TWD'
        lang = 'zh-Hant'
        status = 2
        n = 0
        for dt in d('dl.writer_data.clearfix').children('dt').items():
            if d('dl.writer_data.clearfix').children('dt').eq(n).text() == '作者：':
                author = d('dl.writer_data.clearfix').find('a').eq(n).text()
            elif d('dl.writer_data.clearfix').children('dt').eq(n).text() == '插畫：':
                illustrator = d('dl.writer_data.clearfix').find('a').eq(n).text()
            elif d('dl.writer_data.clearfix').children('dt').eq(n).text() == '譯者：':
                translator = d('dl.writer_data.clearfix').find('a').eq(n).text()
            n += 1
        n = 0
        for li in d('div.bookinfo_more.clearfix').find('li').items():
            if d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == '出版社：':
                publisher = d('div.bookinfo_more.clearfix').find('li').eq(n).children('a').text()
            elif d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == '發售日：':
                date = formatDate(d('div.bookinfo_more.clearfix').find('li').eq(n).text().split('：')[1])
                release_year = date[0]
                release_month = date[1]
                release_day = date[2]
            elif d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == 'ISBN：':
                ean = formatNum(d('div.bookinfo_more.clearfix').find('li').eq(n).text().split('：')[1])
            elif d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == 'EISBN：':
                if ean != None:
                    n += 1
                    continue
                ean = formatNum(d('div.bookinfo_more.clearfix').find('li').eq(n).text().split('：')[1])
            elif d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == '頁數：':
                page_count = formatNum(d('div.bookinfo_more.clearfix').find('li').eq(n).text().split('：')[1])
            elif d('div.bookinfo_more.clearfix').find('li').eq(n).children('span.title').text() == '類型標籤：':
                tag,status = formatTag(d('div.bookinfo_more.clearfix').find('li').eq(n).text().split('：')[1])
            n += 1
        description = html2text.HTML2Text().handle(d('div.topic_content').html()).strip('\n')
        for a in d('div#breadcrumb_list').find('a').items():
            if a.text().find('系列') > 0:
                sid = int(a.attr('href').split('series=')[1])
                sname = a.text().removesuffix('系列')
        if sid != None:
            mysql.commitOne('INSERT IGNORE INTO bookwalker_tw_series(sid,name) VALUES (%s,%s)', (sid,sname))
        mysql.commitOne('''INSERT INTO bookwalker_tw_products(pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,ean,page_count,tag,description,price,currency,lang,status,sid)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
        (pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,ean,page_count,tag,description,price,currency,lang,status,sid)
        )
        log(' '.join((str(pid), author, title)), LogLevel.INFO)
        reqQueue.push(Req('https://www.bookwalker.com.tw/ajax/product_data/'+str(pid)+'/0', 'price'))
        reqQueue.push(Req('https://taiwan-image.bookwalker.com.tw/product/'+str(pid)+'/'+str(pid)+'.jpg', 'img'))
        return False
    elif res.req.tag == 'price':
        pid = int(res.req.url.split('product_data/')[1].split('/')[0])
        try:
            price = float(json.loads(res.response.text)['price']['price'])
        except json.decoder.JSONDecodeError:
            reqQueue.push(res.req)
            log(res.req.url+' 内容解析失败，将会重载该页。网页内容如下：\n'+res.response.text, LogLevel.WARN)
            return flag
        mysql.commitOne('UPDATE bookwalker_tw_products SET price=%s WHERE pid=%s', (price,pid))
        log(' '.join((str(pid),str(price))), LogLevel.INFO)
        return False
    elif res.req.tag == 'img':
        pid = int(res.req.url.split('/')[-1].split('.')[0])
        try:
            os.mkdir('./img/bookwalker_tw/'+str(int(pid/10000)))
        except FileExistsError:
            pass
        with open('./img/bookwalker_tw/'+str(int(pid/10000))+'/'+str(pid)+'.jpg', 'wb') as imageFile:
            imageFile.write(res.response.content)
        log(' '.join((str(pid), './img/bookwalker_tw/'+str(int(pid/10000))+'/'+str(pid)+'.jpg')), LogLevel.INFO)
        return False
    else:
        return False