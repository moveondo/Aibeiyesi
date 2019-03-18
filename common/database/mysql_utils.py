#!/usr/bin/env python
# -*- coding:utf-8 -*-
import pymysql, os, configparser
from pymysql.cursors import DictCursor
from DBUtils.PooledDB import PooledDB


class Config(object):
    """
    # Config().get_content("user_information")

    配置文件里面的参数
    [notdbMysql]
    host = 192.168.1.101
    port = 3306
    user = root
    password = python123
    """

    def __init__(self, file_path):
        self.cf = configparser.ConfigParser()
        self.cf.read(file_path)

    def get_sections(self):
        return self.cf.sections()

    def get_options(self, section):
        return self.cf.options(section)

    def get_content(self, section):
        result = {}
        for option in self.get_options(section):
            value = self.cf.get(section, option)
            result[option] = int(value) if value.isdigit() else value
        return result


class BasePymysqlPool(object):
    def __init__(self, host, port, user, password, db_name=None):
        self.db_host = host
        self.db_port = int(port)
        self.user = user
        self.password = str(password)
        self.db = db_name
        self.conn = None
        self.cursor = None


class MyPymysqlPool(BasePymysqlPool):
    """
    MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现获取连接对象：conn = Mysql.getConn()
            释放连接对象;conn.close()或del conn
    """
    # 连接池对象
    __pool = None

    def __init__(self, conf_path,conf_name=None):
        self.conf = Config(conf_path).get_content(conf_name)
        super(MyPymysqlPool, self).__init__(**self.conf)
        # 数据库构造函数，从连接池中取出连接，并生成操作游标
        self._conn = self.__getConn()
        self._cursor = self._conn.cursor()

    #实现单例模式
    @classmethod
    def instance(cls, *args, **kwargs):
        if not hasattr(MyPymysqlPool, "_instance"):
            MyPymysqlPool._instance = MyPymysqlPool(*args, **kwargs)
        return MyPymysqlPool._instance

    def reSetConnection(self):
        # 数据库构造函数，从连接池中取出连接，并生成操作游标
        self._conn = self.__getConn()
        self._cursor = self._conn.cursor()
        return self

    def __getConn(self):
        """
        @summary: 静态方法，从连接池中取出连接
        @return MySQLdb.connection
        """
        if MyPymysqlPool.__pool is None:
            __pool = PooledDB(creator=pymysql,
                              maxconnections=20,  # 连接池允许的最大连接数，0和None表示不限制连接数
                              mincached=1,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
                              maxcached=10,  # 链接池中最多闲置的链接，0和None不限制
                              blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
                              maxusage=None,
                              host=self.db_host,
                              port=self.db_port,
                              user=self.user,
                              passwd=self.password,
                              db=self.db,
                              use_unicode=True,
                              charset="utf8",
                              cursorclass=DictCursor)
        return __pool.connection()

    def createTale(self,sql,table_name):
        # 使用 execute() 方法执行 SQL，如果表存在则删除
        self._cursor.execute("DROP TABLE IF EXISTS "+table_name)
        self._cursor.execute(sql)

    def getAll(self, sql, param=None):
        """
        @summary: 执行查询，并取出所有结果集
        @param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list(字典对象)/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchall()
        else:
            result = False
        return result

    def getOne(self, sql, param=None):
        """
        @summary: 执行查询，并取出第一条
        @param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchone()
        else:
            result = False
        return result

    def getMany(self, sql, num, param=None):
        """
        @summary: 执行查询，并取出num条结果
        @param sql:查询ＳＱＬ，如果有查询条件，请只指定条件列表，并将条件值使用参数[param]传递进来
        @param num:取得的结果条数
        @param param: 可选参数，条件列表值（元组/列表）
        @return: result list/boolean 查询到的结果集
        """
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        if count > 0:
            result = self._cursor.fetchmany(num)
        else:
            result = False
        return result

    def insertMany(self, sql, values):
        """
        @summary: 向数据表插入多条记录
        @param sql:要插入的ＳＱＬ格式
        @param values:要插入的记录数据tuple(tuple)/list[list]
        @return: count 受影响的行数
        """
        count = self._cursor.executemany(sql, values)
        return count

    def __query(self, sql, param=None):
        if param is None:
            count = self._cursor.execute(sql)
        else:
            count = self._cursor.execute(sql, param)
        return count

    def update(self, sql, param=None):
        """
        @summary: 更新数据表记录
        @param sql: ＳＱＬ格式及条件，使用(%s,%s)
        @param param: 要更新的  值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    def insert(self, sql, param=None):
        """
        @summary: 更新数据表记录
        @param sql: ＳＱＬ格式及条件，使用(%s,%s)
        @param param: 要更新的  值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    def delete(self, sql, param=None):
        """
        @summary: 删除数据表记录
        @param sql: ＳＱＬ格式及条件，使用(%s,%s)
        @param param: 要删除的条件 值 tuple/list
        @return: count 受影响的行数
        """
        return self.__query(sql, param)

    def begin(self):
        """
        @summary: 开启事务
        """
        self._conn.autocommit(0)

    def end(self, option='commit'):
        """
        @summary: 结束事务
        """
        if option == 'commit':
            self._conn.commit()
        else:
            self._conn.rollback()

    def dispose(self, isEnd=1):
        """
        @summary: 释放连接池资源
        """
        if isEnd == 1:
            self.end('commit')
        else:
            self.end('rollback')
        self._cursor.close()
        self._conn.close()

    def close_conn(self):
        self._conn.close()
        self._cursor.close()

if __name__ == '__main__':
    mp = MyPymysqlPool(conf_path=r"../../conf/mysql.ini",conf_name="MysqlTest")
    # sql = """select * from tb_text_tagging where id =14"""
    # result = mp.getAll(sql)
    # print(result[0]['queue_name'])
    # print(result)
    sql_create = """CREATE TABLE tb_ai (
                            id INT auto_increment primary key,
                            modelType CHAR(20),
                            predictFilePath CHAR(50) ,
                            predictResult TEXT ,
                            loadTime TIMESTAMP )"""
    result = mp.createTale(sql_create,'tb_ai')
    print(result)