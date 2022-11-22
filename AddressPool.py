#!/usr/bin/python3
#coding=utf-8
'''地址池层'''
import threading
from enum import Enum
from collections import deque

class HttpMethod(Enum):
    '''HTTP方法枚举类：请求类支持的HTTP方法。'''
    GET = 1

class Req:
    '''请求类：用于在任务池的任务中实例化请求对象。'''
    def __init__(self, url:str, tag:str='', method:HttpMethod=HttpMethod.GET) -> None:
        self.url = url
        self.tag = tag
        self.method = method

class ReqQueue:
    '''请求队列类（线程安全）：用于在调度器中实例化请求队列对象。'''
    def __init__(self) -> None:
        self.reqs = deque()
        self._lock = threading.Lock()
    def push(self, req:Req) -> None:
        self._lock.acquire()
        self.reqs.append(req)
        self._lock.release()
    def pop(self) -> Req:
        try:
            self._lock.acquire()
            req = self.reqs.popleft()
            return req
        except IndexError:
            return None
        finally:
            self._lock.release()