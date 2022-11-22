#!/usr/bin/python3
#coding=utf-8
'''任务：广州天闻角川'''
import os
from pyquery import PyQuery
from AddressPool import Req,ReqQueue
from Downloader import Res
from DataPool import MySQL
from logger import LogLevel

def init(reqQueue:ReqQueue):
    reqQueue.push(Req('http://www.gztwkadokawa.com/?gallery-2-grid.html', 'init'))

def parse(res:Res, mysql:MySQL, reqQueue:ReqQueue, flag:bool, log) -> bool:
    if not res.response.ok:
        log(res.req.url+' '+str(res.response.status_code)+' '+res.response.reason, LogLevel.WARN)
        reqQueue.push(res.req)
        return flag
    res.response.encoding = 'utf-8'
    d = PyQuery(res.response.text)

    def formatName(name:str) -> str:
        return name.replace('[日]', '').replace('(日)', '').replace('（日）', '').replace('[著]', '').replace('(著)', '').replace('（著）', '').replace('[绘]', '').replace('(绘)', '').replace('（绘）', '').replace('[译]', '').replace('(译)', '').replace('（译）', '').replace(';  ', ',').replace('; ', ',').replace(';', ',').replace('； ', ',').replace('；', ',').replace('、 ', ',').replace('、', ',').replace('， ', ',').replace('，', ',').replace(',  ', ',').replace(', ', ',').replace('  ,', ',').replace(' ,', ',').replace('/原作', '').replace(' 原作', '').replace('原作,', ',').replace('/著', '').replace(' 著', '').replace('著,', ',').replace('/绘', '').replace(' 绘', '').replace('绘,', ',').replace('/译', '').replace(' 译', '').replace('译,', ',').replace('/', ',').replace('  ', ',').removesuffix('原作').removesuffix('著').removesuffix('绘').removesuffix('译').strip(' ')
    def formatDate(dateStr:str) -> tuple:
        year=month=day = None
        if dateStr.find('年') > -1:
            year = int(dateStr.split('年')[0])
            if dateStr.find('月') > -1:
                month = int(dateStr.split('年')[1].split('月')[0])
                if dateStr.find('日') > -1:
                    day = int(dateStr.split('年')[1].split('月')[1].split('日')[0])
        elif dateStr.find('-') > -1:
            if len(dateStr.split('-')) == 3:
                year = int(dateStr.split('-')[0])
                month = int(dateStr.split('-')[1])
                day = int(dateStr.split('-')[2])
            elif len(dateStr.split('-')) == 2:
                year = int(dateStr.split('-')[0])
                month = int(dateStr.split('-')[1])
        return (year,month,day)
    def formatNum(numS:str) -> int:
        s = ''
        for c in numS:
            if c.isdigit():
                s = s + c
        return int(s)
    def formatDescription(s:str) -> str:
        return s.replace('    \n', '\n').replace('   \n', '\n').replace('  \n', '\n').replace(' \n', '\n').replace('\n\n\n\n', '\n').replace('\n\n\n', '\n').replace('\n\n', '\n').replace('\n', '\n\n').strip(' ').strip('\n')
    def formatPrice(priceS:str) -> float:
        return float(priceS.replace('￥', '').strip(' '))

    if res.req.tag == 'init':
        maxPage = int(d('span.pageall').text())
        for i in range(maxPage):
            pageNum = i+1
            reqQueue.push(Req('http://www.gztwkadokawa.com/?gallery-2--0--'+str(pageNum)+'--grid.html', 'page'))
        return True
    elif res.req.tag == 'page':
        for a in d('a.entry-title').items():
            url = 'http://www.gztwkadokawa.com/' + a.attr('href')
            pid = int(a.attr('href').split('?product-')[1].split('.html')[0])
            if mysql.selectOne('SELECT pid FROM kadokawa_cn WHERE pid=%s', (pid,)) != None:
                continue
            reqQueue.push(Req(url, 'pid'))
        return False
    elif res.req.tag == 'pid':
        pid = int(res.req.url.split('/')[-1].split('?product-')[1].split('.html')[0])
        title = d('h1.goodsname').text().split('《')[-1].split('》')[0]
        if title == '' or title == None:
            reqQueue.push(res.req)
            log(res.req.url+' 内容解析失败，将会重载该页。网页内容如下：\n'+res.response.text, LogLevel.WARN)
            return flag
        author=illustrator=translator=publisher=description = ''
        release_year=release_month=release_day=ean=page_count=price = None
        currency = 'CNY'
        lang = 'zh-Hans'
        status = 2
        for li in d('ul.goodsprops').children('li').items():
            key = li.text().split('：')[0]
            value = li.text().split('：')[1].strip(' ')
            if key == '作者':
                author = formatName(value)
            elif key == '插画' or key == '绘者':
                illustrator = formatName(value)
            elif key == '译者':
                translator = formatName(value)
            elif key == '出版社' or key == '出版者':
                publisher = formatName(value)
            elif key == '出版时间' or key == '版次':
                if key == '版次' and release_year != None:
                    continue
                date = formatDate(value)
                release_year = date[0]
                release_month = date[1]
                release_day = date[2]
            elif key == 'ISBN':
                ean = formatNum(value)
            elif key == '页数':
                page_count = formatNum(value)
        description = formatDescription(d('div#goods-intro').text())
        price = formatPrice(d('i.mktprice1').text())
        mysql.commitOne('INSERT INTO kadokawa_cn(pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,ean,page_count,description,price,currency,lang,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', (pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,ean,page_count,description,price,currency,lang,status))
        log(' '.join((str(pid), author, title)), LogLevel.INFO)
        reqQueue.push(Req(d('div.goods-detail-pic').attr('bigpicsrc'), 'img/'+str(pid)))
        return False
    elif res.req.tag.split('/')[0] == 'img':
        pid = int(res.req.tag.split('/')[1])
        try:
            os.mkdir('./img/kadokawa_cn/'+str(int(pid/10000)))
        except FileExistsError:
            pass
        with open('./img/kadokawa_cn/'+str(int(pid/10000))+'/'+str(pid)+'.jpg', 'wb') as imgFile:
            imgFile.write(res.response.content)
        log(' '.join((str(pid), './img/kadokawa_cn/'+str(int(pid/10000))+'/'+str(pid)+'.jpg')), LogLevel.INFO)
        return False
    else:
        return False