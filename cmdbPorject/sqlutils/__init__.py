from DBUtils.PooledDB import PooledDB
import pymysql
from django.conf import settings


class DBConnect:
    def __init__(self):
        self.conn = DBConnect.connect()
        self.cour = self.conn.cursor(pymysql.cursors.DictCursor)

    @staticmethod
    def connect():
        pool = PooledDB(creator=pymysql, mincached=5, user=settings.DBUSER, passwd=settings.DBPASS,
                        port=settings.DBPORT, database=settings.DATABASE)
        return pool.connection()

    def Query(self, sql):
        self.cour.execute(sql)
        res = self.cour.fetchall()
        return res

    def Modify(self, sql, args: list):
        self.cour.execute(sql, args)
        res = self.conn.commit()
        return res


db = DBConnect()