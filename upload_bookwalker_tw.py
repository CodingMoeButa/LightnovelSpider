#!/usr/bin/python3
#coding=utf-8
import os
import sqlite3
import pymysql
from qiniu import Auth, put_file

LOCAL_SQLITE_FILE = 'spider.db'
REMOTE_MYSQL_ADDR = ''
REMOTE_MYSQL_PORT = 3306
REMOTE_MYSQL_USER = ''
REMOTE_MYSQL_PASS = ''
QINIU_ACCESS_KEY = ''
QINIU_SECRET_KEY = ''
QINIU_BUCKET_NAME = ''

qn = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)

local_sqlite_conn = sqlite3.connect(LOCAL_SQLITE_FILE)
local_sqlite_cur = local_sqlite_conn.cursor()
local_sqlite_result = local_sqlite_cur.execute('''SELECT pid,title,author,illustrator,translator,publisher,
release_year,release_month,release_day,isbn,description,status
FROM bookwalker_tw
WHERE submit=0''')
for local_sqlite_row in list(local_sqlite_result):
    pid = local_sqlite_row[0]
    title = local_sqlite_row[1]
    author = local_sqlite_row[2]
    illustrator = local_sqlite_row[3]
    translator = local_sqlite_row[4]
    publisher = local_sqlite_row[5]
    release_year = local_sqlite_row[6]
    if release_year == '': release_year = None
    release_month = local_sqlite_row[7]
    if release_month == '': release_month = None
    release_day = local_sqlite_row[8]
    if release_day == '': release_day = None
    isbn = local_sqlite_row[9]
    if isbn == '': isbn = None
    description = local_sqlite_row[10]
    lang = 'zh_hant'
    status = local_sqlite_row[11]
    remote_mysql_conn = pymysql.connect(
        host=REMOTE_MYSQL_ADDR,
        port=REMOTE_MYSQL_PORT,
        user=REMOTE_MYSQL_USER,
        password=REMOTE_MYSQL_PASS,
        database='lightnovel')
    remote_mysql_cur = remote_mysql_conn.cursor()
    remote_mysql_cur.execute('''INSERT INTO ln_book(title,author,illustrator,translator,publisher,
    release_year,release_month,release_day,isbn,description,lang,status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
    (title,author,illustrator,translator,publisher,release_year,release_month,release_day,isbn,description,lang,status))
    remote_mysql_conn.commit()
    remote_mysql_cur.execute('''SELECT bid FROM ln_book WHERE title=%s AND author=%s AND publisher=%s''', (title, author, publisher))
    remote_mysql_result = remote_mysql_cur.fetchall()
    for remote_mysql_row in remote_mysql_result:
        bid = remote_mysql_row[0]
    img_path = './img/bookwalker_tw/'+str(int(int(pid)/10000))+'/'+str(pid)+'.jpg'
    if os.path.exists(img_path):
        key_path = 'cover/'+str(int(int(bid)/10000))+'/'+str(bid)+'.jpg'
        qiniu_token = qn.upload_token(QINIU_BUCKET_NAME, key_path, 3600)
        put_file(qiniu_token, key_path, img_path, version='v2')
    local_sqlite_cur.execute('UPDATE bookwalker_tw SET submit=1 WHERE pid=?', (pid,))
    local_sqlite_conn.commit()
    print(pid, bid, author, title)
local_sqlite_conn.close()