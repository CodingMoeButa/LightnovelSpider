#!/usr/bin/python3
#coding=utf-8
'''数据池层'''
import pymysql
from dbutils.persistent_db import PersistentDB
from logger import LogLevel

class MySQL:
    def __init__(self, configDict:dict, log) -> None:
        self._pool = PersistentDB(
            creator=pymysql,
            host=configDict['host'],
            port=configDict['port'],
            user=configDict['username'],
            passwd=configDict['password'],
            database=configDict['database']
        )
        self._log = log
    def commitOne(self, query:str, args:tuple):
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query, args)
                    conn.commit()
                except pymysql.err.Error as e:
                    conn.rollback()
                    self._log(e, LogLevel.FATAL)
                    raise e
    def selectOne(self, query:str, args:tuple) -> tuple:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(query, args)
                    return cur.fetchone()
                except pymysql.err.Error as e:
                    self._log(e, LogLevel.FATAL)
                    raise e