#!/usr/bin/python3
#coding=utf-8
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import sqlite3
import pymysql
from qiniu import Auth, put_file, etag
import qiniu.config

LOCAL_SQLITE_FILE = ''
REMOTE_MYSQL_ADDR = ''
REMOTE_MYSQL_PORT = 3306
REMOTE_MYSQL_USER = ''
REMOTE_MYSQL_PASS = ''
QINIU_ACCESS_KEY = ''
QINIU_SECRET_KEY = ''
QINIU_BUCKET_NAME = ''

qn = Auth(QINIU_ACCESS_KEY, QINIU_SECRET_KEY)

bid=pid=title=author=illustrator=translator=publisher=release_year=release_month=release_day=isbn=description=lang=database=path = None

root = tk.Tk()
root.title('图书信息上传')
root.geometry('1000x666+200+20')
root.resizable(0,0)

lbImage = tk.Label(root, text='封面图片', font=('System',15))
lbImage.place(x=0, y=0, width=444, height=666)

lbTitle = tk.Label(root, text='标题', font=('System',15))
lbTitle.place(x=444, y=0, width=75, height=30)

entTitle = tk.Entry(root, font=('System',15))
entTitle.place(x=519, y=0, width=481, height=30)

lbAuthor = tk.Label(root, text='作者', font=('System',15))
lbAuthor.place(x=444, y=30, width=75, height=30)

entAuthor = tk.Entry(root, font=('System',15))
entAuthor.place(x=519, y=30, width=481, height=30)

lbIllustrator = tk.Label(root, text='绘者', font=('System',15))
lbIllustrator.place(x=444, y=60, width=75, height=30)

entIllustrator = tk.Entry(root, font=('System',15))
entIllustrator.place(x=519, y=60, width=481, height=30)

lbTranslator = tk.Label(root, text='译者', font=('System',15))
lbTranslator.place(x=444, y=90, width=75, height=30)

entTranslator = tk.Entry(root, font=('System',15))
entTranslator.place(x=519, y=90, width=481, height=30)

lbPublisher = tk.Label(root, text='出版者', font=('System',15))
lbPublisher.place(x=444, y=120, width=75, height=30)

entPublisher = tk.Entry(root, font=('System',15))
entPublisher.place(x=519, y=120, width=481, height=30)

lbDate = tk.Label(root, text='出版日期', font=('System',15))
lbDate.place(x=444, y=150, width=75, height=30)

entYear = tk.Entry(root, font=('System',15))
entYear.place(x=519, y=150, width=131, height=30)

lbYear = tk.Label(root, text='年',font=('System',15))
lbYear.place(x=650, y=150, width=30, height=30)

entMonth = tk.Entry(root, font=('System',15))
entMonth.place(x=680, y=150, width=130, height=30)

lbMonth = tk.Label(root, text='月', font=('System',15))
lbMonth.place(x=810, y=150, width=30, height=30)

entDay = tk.Entry(root, font=('System',15))
entDay.place(x=840, y=150, width=130, height=30)

lbDay = tk.Label(root, text='日', font=('System',15))
lbDay.place(x=970, y=150, width=30, height=30)

lbISBN = tk.Label(root, text='ISBN', font=('System',15))
lbISBN.place(x=444, y=180, width=75, height=30)

entISBN = tk.Entry(root, font=('System',15))
entISBN.place(x=519, y=180, width=481, height=30)

txtDescription = tk.Text(root, font=('System',15))
txtDescription.place(x=444, y=210, width=556, height=356) 

def btnDelete_onCommand():
    btnDelete['state'] = 'disabled'
    btnUpload['state'] = 'disabled'
    if messagebox.askyesno('从本地删除','确定要从本地数据库和文件系统删除图书信息及封面图片吗？'):
        local_sqlite_conn = sqlite3.connect(LOCAL_SQLITE_FILE)
        local_sqlite_cur = local_sqlite_conn.cursor()
        local_sqlite_cur.execute('DELETE FROM %s WHERE pid=?' % database, (pid,))
        local_sqlite_conn.commit()
        local_sqlite_conn.close()
        if os.path.exists(path):
            os.remove(path)
    btnDelete['state'] = 'active'
    btnUpload['state'] = 'active'

btnDelete = tk.Button(root, text='从本地删除', font=('System',15), command=btnDelete_onCommand)
btnDelete.place(x=444, y=566, width=278, height=100)

def get_kadokawa_cn()->bool:
    global pid,title,author,illustrator,publisher,release_year,release_month,isbn,description,path,database,lang
    database = 'kadokawa_cn'
    lang = 'zh_hans'
    local_sqlite_conn = sqlite3.connect(LOCAL_SQLITE_FILE)
    local_sqlite_cur = local_sqlite_conn.cursor()
    local_sqlite_result = local_sqlite_cur.execute('SELECT pid,title,author,illustrator,publisher,release_year,release_month,isbn,description FROM kadokawa_cn WHERE submit=0 LIMIT 1')
    local_sqlite_result_list = list(local_sqlite_result)
    if len(local_sqlite_result_list)==0:
        local_sqlite_conn.close()
        return False
    for local_sqlite_row in local_sqlite_result_list:
        pid = local_sqlite_row[0]
        title = local_sqlite_row[1]
        author = local_sqlite_row[2]
        illustrator = local_sqlite_row[3]
        publisher = local_sqlite_row[4]
        release_year = local_sqlite_row[5]
        release_month = local_sqlite_row[6]
        isbn = local_sqlite_row[7]
        description = local_sqlite_row[8]
    local_sqlite_conn.close()
    entTitle.delete(0, 'end')
    entTitle.insert(0, title)
    entAuthor.delete(0, 'end')
    entAuthor.insert(0, author)
    entIllustrator.delete(0, 'end')
    entIllustrator.insert(0, illustrator)
    entPublisher.delete(0, 'end')
    entPublisher.insert(0, publisher)
    entYear.delete(0, 'end')
    entYear.insert(0, release_year)
    entMonth.delete(0, 'end')
    entMonth.insert(0, release_month)
    entISBN.delete(0, 'end')
    entISBN.insert(0, isbn)
    txtDescription.delete('1.0','end')
    txtDescription.insert('1.0', description)
    #Initialize the file name in a variable
    path = './img/kadokawa_cn/'+str(int(int(pid)/10000))+'/'+str(pid)+'.jpg'
    if os.path.exists(path):
        #Create an object of tkinter ImageTk
        img = ImageTk.PhotoImage(Image.open(path).resize((444,666)))
        lbImage['image'] = img
        img.image = img
    else:
        lbImage['image'] = ''
    return True

def get_bookwalker_tw()->bool:
    global pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,isbn,description,path,database,lang
    database = 'bookwalker_tw'
    lang = 'zh_hant'
    local_sqlite_conn = sqlite3.connect(LOCAL_SQLITE_FILE)
    local_sqlite_cur = local_sqlite_conn.cursor()
    local_sqlite_result = local_sqlite_cur.execute('SELECT pid,title,author,illustrator,translator,publisher,release_year,release_month,release_day,isbn,description FROM bookwalker_tw WHERE submit=0 LIMIT 1')
    local_sqlite_result_list = list(local_sqlite_result)
    if len(local_sqlite_result_list)==0:
        local_sqlite_conn.close()
        return False
    for local_sqlite_row in local_sqlite_result_list:
        pid = local_sqlite_row[0]
        title = local_sqlite_row[1]
        author = local_sqlite_row[2]
        illustrator = local_sqlite_row[3]
        translator = local_sqlite_row[4]
        publisher = local_sqlite_row[5]
        release_year = local_sqlite_row[6]
        release_month = local_sqlite_row[7]
        release_day = local_sqlite_row[8]
        isbn = local_sqlite_row[9]
        description = local_sqlite_row[10]
    local_sqlite_conn.close()
    entTitle.delete(0, 'end')
    entTitle.insert(0, title)
    entAuthor.delete(0, 'end')
    entAuthor.insert(0, author)
    entIllustrator.delete(0, 'end')
    entIllustrator.insert(0, illustrator)
    entTranslator.delete(0, 'end')
    entTranslator.insert(0, translator)
    entPublisher.delete(0, 'end')
    entPublisher.insert(0, publisher)
    entYear.delete(0, 'end')
    entYear.insert(0, release_year)
    entMonth.delete(0, 'end')
    entMonth.insert(0, release_month)
    entDay.delete(0, 'end')
    entDay.insert(0, release_day)
    entISBN.delete(0, 'end')
    entISBN.insert(0, isbn)
    txtDescription.delete('1.0','end')
    txtDescription.insert('1.0', description)
    #Initialize the file name in a variable
    path = './img/bookwalker_tw/'+str(int(int(pid)/10000))+'/'+str(pid)+'.jpg'
    if os.path.exists(path):
        #Create an object of tkinter ImageTk
        img = ImageTk.PhotoImage(Image.open(path).resize((444,666)))
        lbImage['image'] = img
        img.image = img
    else:
        lbImage['image'] = ''
    return True

def get_new():
    if not get_kadokawa_cn():
        if not get_bookwalker_tw():
            messagebox.showinfo('已完成', '已经没有待处理的图书信息了。')
            exit()

def btnUpload_onCommand():
    btnDelete['state'] = 'disabled'
    btnUpload['state'] = 'disabled'
    flag = messagebox.askyesnocancel('上传到服务器', '即将上传到服务器。这是限制级作品吗？')
    if flag == True:
        status = 1
    elif flag == False:
        status = 2
    else:
        btnDelete['state'] = 'active'
        btnUpload['state'] = 'active'
        return
    title = entTitle.get()
    author = entAuthor.get()
    illustrator = entIllustrator.get()
    translator = entTranslator.get()
    publisher = entPublisher.get()
    release_year = entYear.get()
    release_month = entMonth.get()
    release_day = entDay.get()
    isbn = entISBN.get()
    if release_year == '': release_year = None
    if release_month == '': release_month = None
    if release_day == '': release_day = None
    if isbn == '': isbn = None
    description = txtDescription.get('1.0','end').removesuffix('\n')
    remote_mysql_conn = pymysql.connect(host=REMOTE_MYSQL_ADDR, port=REMOTE_MYSQL_PORT, user=REMOTE_MYSQL_USER, password=REMOTE_MYSQL_PASS, database='lightnovel')
    remote_mysql_cur = remote_mysql_conn.cursor()
    remote_mysql_sql = "INSERT INTO ln_book(title, author, illustrator, translator, publisher, release_year, release_month, release_day, isbn, description, lang, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    try:
        remote_mysql_cur.execute(remote_mysql_sql, (title, author, illustrator, translator, publisher, release_year, release_month, release_day, isbn, description, lang, status))
        remote_mysql_conn.commit()
    except Exception as e:
        remote_mysql_conn.rollback()
        remote_mysql_conn.close()
        print(e)
        messagebox.showerror('上传到服务器', '提交信息到远程数据库时出错。')
        return
    remote_mysql_sql = "SELECT bid FROM ln_book WHERE title=%s AND author=%s AND publisher=%s"
    try:
        remote_mysql_cur.execute(remote_mysql_sql, (title, author, publisher))
        remote_mysql_result = remote_mysql_cur.fetchall()
        for remote_mysql_row in remote_mysql_result:
            bid = remote_mysql_row[0]
    except:
        remote_mysql_conn.close()
        messagebox.showerror('上传到服务器', '获取新提交记录的bid时出错。')
    remote_mysql_conn.close()
    filename = 'cover/'+str(int(int(bid)/10000))+'/'+str(bid)+'.jpg'
    qiniu_token = qn.upload_token(QINIU_BUCKET_NAME, filename, 3600)
    ret, info = put_file(qiniu_token, filename, path, version='v2') 
    local_sqlite_conn = sqlite3.connect(LOCAL_SQLITE_FILE)
    local_sqlite_cur = local_sqlite_conn.cursor()
    local_sqlite_cur.execute('UPDATE %s SET submit=1 WHERE pid=?' % (database,), (pid,))
    local_sqlite_conn.commit()
    local_sqlite_conn.close()
    get_new()
    btnDelete['state'] = 'active'
    btnUpload['state'] = 'active'

btnUpload = tk.Button(root, text='上传到服务器', font=('System',15), command=btnUpload_onCommand)
btnUpload.place(x=722, y=566, width=278, height=100)

get_new()

root.mainloop()