#!/usr/bin/python3
#coding=utf-8
'''下载器层'''
import requests
from AddressPool import HttpMethod,Req
from logger import LogLevel

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.49 LightnovelSpider/2.0'

class Res:
    '''响应类'''
    def __init__(self, req:Req, response:requests.Response) -> None:
        self.req = req
        self.response = response

class Requester:
    '''请求器类：用于在调度器中实例化请求器对象。'''
    def __init__(self, configDict:dict, log) -> None:
        self._proxy = configDict['proxy']
        self._timeout = configDict['timeout']
        self._domains = configDict['domains']
        self._log = log
    def send(self, req:Req) -> Res:
        headers = {
            'User-Agent': USER_AGENT
        }
        cookies = {}
        proxy = self._proxy
        timeout = self._timeout
        for domainConfig in self._domains:
            if req.url.find(domainConfig['domain']) > -1:
                proxy = domainConfig['proxy']
                timeout = domainConfig['timeout']
                cookies = {cookie.split("=")[0]:cookie.split("=")[-1] for cookie in domainConfig['cookies'].split("; ")}
        proxies = {
            'http': proxy,
            'https': proxy
        }
        try:
            if req.method == HttpMethod.GET:
                return Res(req, requests.get(url=req.url, headers=headers, cookies=cookies, proxies=proxies, timeout=timeout))
            else:
                self._log('使用了不受支持的HTTP请求方法。', LogLevel.ERROR)
                return None
        except requests.RequestException as e:
            self._log(e, LogLevel.WARN)
            return None