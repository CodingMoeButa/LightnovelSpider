#!/usr/bin/python3
#coding=utf-8
'''调度器（入口）'''
import os
import time
import json
import importlib
import threading

# 初始化记录器
from logger import Logger
logger = Logger()
# 初始化任务池
tasknames = [taskfile.split('.py')[0] for taskfile in os.listdir('TaskPool') if taskfile.find('.py')>0]
print('序号\t任务')
for i in range(len(tasknames)): print(str(i), tasknames[i], sep='\t')
taskname = tasknames[int(input('输入要启动的任务序号：'))] # 列出任务池中预定义的任务供用户选择
task = importlib.import_module('TaskPool.'+taskname) # 导入任务模块
# 初始化调度器
with open('config.json', 'r', encoding='utf-8') as configFile: configObj = json.loads(configFile.read()) # 载入配置对象
threads = [] # 声明线程列表
flag = True # 线程持久化信号
# 初始化地址池
from AddressPool import ReqQueue
reqQueue = ReqQueue() # 创建请求队列对象
# 初始化下载器
from Downloader import Requester
requester = Requester(configObj['downloader'], logger.log)
# 初始化数据池
from DataPool import MySQL
mysql = MySQL(configObj['dataPool']['mysql'], logger.log)

# 定义线程执行函数
def run():
    global flag
    while True:
        req = reqQueue.pop()
        if req == None:
            if flag:
                time.sleep(1)
                continue
            else:
                break
        res = requester.send(req)
        if res == None:
            reqQueue.push(req)
            continue
        flag = task.parse(res, mysql, reqQueue, flag, logger.log)

task.init(reqQueue) # 执行初始化任务事件
for i in range(configObj['scheduler']['threadNum']): threads.append(threading.Thread(target=run)) # 构造线程
for i in range(configObj['scheduler']['threadNum']): threads[i].start() # 拉起线程
for i in range(configObj['scheduler']['threadNum']): threads[i].join() # 等待线程