# author: stanley
# crated date: 2021/4/25
# -*- coding:utf-8 -*-
import pymysql
from pymysql import OperationalError


class DBHelper:
    def __init__(self, host, port, user, passwd):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, charset='utf8', autocommit=True)
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    def __del__(self):
        self.cursor.close()
        self.conn.close()

    def _reCon(self):
        """ MySQLdb.OperationalError异常"""
        # self.con.close()
        while True:
            try:
                self.conn.ping()
                break
            except OperationalError:
                self.conn.ping(True)

    def select_db(self, db_name):
        try:
            self.conn.select_db(db_name)
        except Exception as e:
            print('db_name is not exist')
            pass

    def query_db(self, sql, state='all'):
        self._reCon()
        with self.conn:
            self.cursor.execute(sql)
            if state == 'all':
                data = self.cursor.fetchall()
            else:
                data = self.cursor.fetchone()
            return data

    def delete_db(self, sql):
        effect_row = self.cursor.execute(sql)
        return effect_row

    def insert_db(self, sql, val):
        try:
            data = self.cursor.executemany(sql, val)
            self.conn.commit()
            return data
        except:
            self.conn.rollback()


