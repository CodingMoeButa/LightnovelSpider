#!/usr/bin/python3
#coding=utf-8
'''线程安全日志记录器库'''
import time
import threading
from enum import Enum

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    FATAL = 5

class Logger:
    def __init__(self) -> None:
        self._lock = threading.Lock()
    def log(self, s, level:LogLevel=LogLevel.DEBUG):
        if level is LogLevel.FATAL:
            levelS = 'FATAL'
        elif level is LogLevel.ERROR:
            levelS = 'ERROR'
        elif level is LogLevel.WARN:
            levelS = 'WARN'
        elif level is LogLevel.INFO:
            levelS = 'INFO'
        else:
            levelS = 'DEBUG'
        self._lock.acquire()
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), '['+levelS+']', s)
        self._lock.release()