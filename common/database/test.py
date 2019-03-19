#!/usr/bin/python3
from common.database.mysql_utils import MyPymysqlPool

mp = MyPymysqlPool.instance(conf_path=r"../../conf/mysql1.ini", conf_name='MysqlTest')
mp1 = MyPymysqlPool.instance(conf_path=r"../../conf/mysql1.ini", conf_name='MysqlTest')
mp2 = MyPymysqlPool(conf_path=r"../../conf/mysql1.ini", conf_name='MysqlTest')
mp3 = MyPymysqlPool.instance(conf_path=r"../conf/mysql1.ini",conf_name='MysqlTest')
sql = """SELECT bm_id FROM tb_corp_analyze WHERE id=%s""" %(10)
result = mp3.getAll(sql)
mp.dispose()
print(result)
