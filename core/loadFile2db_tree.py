# coding=utf-8
import json

import time

import datetime

import logging

import requests

from common.database.mysql_utils import MyPymysqlPool


class Load2DB():
    def __init__(self,env,mp=None):
        self.logger = logging.getLogger('root.'+self.__class__.__name__)
        self.mp = mp
        if not self.mp:
            if env == 'test':
                conf_name = 'MysqlTest'
            elif env == 'dev':
                conf_name = 'MysqlDev'
            self.mp = MyPymysqlPool(conf_path=r"../conf/mysql1.ini", conf_name=conf_name)

    def deleteData(self,dbName,corp_analyze_id):
        self.logger.info('删除数据，corp_analyze_id：'+str(corp_analyze_id))
        sql = """delete from %s where corp_analyze_id=%s and TYPE='ai_annotation'""" %(dbName,corp_analyze_id)
        self.logger.info(sql)
        self.mp.reSetConnection().delete(sql)
        self.mp.dispose()

    def load2record(self,doc_id,corp_analyze_id):
        sql = """INSERT INTO %s%s VALUES (%s,%s)""" % ('tb_doc_corp_analyze_execute', '(doc_id,corp_analyze_id)',doc_id,corp_analyze_id)
        self.logger.info('sql语句：{}'.format(sql))
        result = self.mp.reSetConnection().insert(sql)
        self.mp.dispose(isEnd=1)
        self.logger.info('插入' + str(result) + '条记录数据')


    def loadFile2DB(self,dbName,modelType,resultFilePath,docId,stock_code,corp_analyze_id,user_id,bm_id):
        self.logger.info('加载{}数据到数据库'.format(resultFilePath))
        file_dict = self.readJsonFile(resultFilePath)
        time1_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        args = []
        start_offset_tmp = -10
        end_offset_tmp = -10
        over = False
        for label_key in file_dict.keys():
            contents_list = file_dict[label_key]
            for contents_dict in contents_list:
                if abs(contents_dict['start_offset']-end_offset_tmp)<5:
                    end_offset_tmp = contents_dict['end_offset']
                else:
                    if over:
                        # 调用java restful接口，获取source_str
                        if end_offset_tmp-start_offset_tmp>50:#大于50的字段存入
                            source_dict = {}
                            source_dict['docId'] = docId
                            source_dict['pageInd'] = contents_dict['page_id']
                            source_dict['pageEnd'] = contents_dict['page_id']
                            source_dict['startOffset'] = start_offset_tmp
                            source_dict['endOffset'] = end_offset_tmp
                            titles = contents_dict['title'].split('/')
                            source_str = self.getSource(source_dict)
                            if source_str=='未提取到text':
                                continue
                            tmp = ''
                            count = 0
                            for title in titles:
                                if title:
                                    tmp += '  '*count+title + '\n'
                                count+=1
                            source_str = tmp + '  '*count+source_str
                            aspectId = self.getAspectId(bm_id,contents_dict['tag_class_id'])
                            dbValue = (docId, aspectId,contents_dict['page_id'], contents_dict['page_id'], start_offset_tmp,
                                       end_offset_tmp, contents_dict['tag_class_id'], stock_code, label_key,0,
                                       'ai_annotation',modelType,resultFilePath,
                                       user_id, time1_str, time1_str, contents_dict['confidence'], corp_analyze_id, source_str)
                            args.append(dbValue)
                        start_offset_tmp = contents_dict['start_offset']
                        end_offset_tmp = contents_dict['end_offset']
                    else:
                        #新的一段
                        start_offset_tmp = contents_dict['start_offset']
                        end_offset_tmp = contents_dict['end_offset']
                        over = True

        dbField = ('doc_id','analyze_aspect_id', 'page_ind', 'page_end','start_offset', 'end_offset', 'tag_class','stock_code','tag_class_name','status','type','model_type','predict_file_path','user_id','created_at','updated_at','confidence','corp_analyze_id','source_str')
        dbField = str(dbField).replace("'", '')
        sql = """INSERT INTO %s%s VALUES """ %(dbName,dbField)
        sql = sql+""" (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        self.logger.info(sql)
        # try:
        result = self.mp.reSetConnection().insertMany(sql,args)
        self.mp.dispose(isEnd=1)
        self.logger.info('插入'+str(result)+'条预测数据')
        # except Exception as e:
        #     print("执行Mysql: %s时出错： %s" % (sql, e))
        #     self.mp.dispose(isEnd=0)

    def getAspectId(self,bm_id,tag_class_id):
        sql = """select id from tb_analyze_aspect where biz_model=%s and tag_class_id=%s""" % (bm_id,tag_class_id)
        result = self.mp.reSetConnection().getAll(sql)
        for row in result:
            aspectId = row['id']
        self.mp.dispose()
        return aspectId

    def getSource(self,source_dict):
        url = 'http://tftest.hipland.net/tagmanage/labelDisplay/queryLabel'
        body = json.dumps(source_dict)
        self.logger.info(body)
        headers = {'content-type': "application/json"}
        response = requests.post(url, data=body, headers=headers)
        status_code = response.status_code
        source_str = '未提取到text'
        if status_code == 200:
            result = response.text
            result_dict = json.loads(result)
            # print(result_dict)
            if result_dict['data']:
                source_str = result_dict['data']['text']
        self.logger.info(source_str)
        return source_str

    def readJsonFile(self,filePath):
        with open(filePath,'r',encoding='utf-8') as f:
            contents_dict = json.load(f)
        return contents_dict

    def readFile(self,filePath):
        with open(filePath,'r',encoding='utf-8') as f:
            contents_json = f.read()
        return contents_json

if __name__ == '__main__':
    ld = Load2DB('test')
    # ld.loadFile2DB('tb_text_tagging',r'D:\Projects\pdfTransform\aiBysModle\data\d0f3ebc5329443068bb0ceafd6b889c5\predictResult\d0f3ebc5329443068bb0ceafd6b889c5_predictResult_26.json',0,0,12)
    # ld.loadFile2DB_tb_ai('tb_ai','aiBysModel','test',r'../../data/predict_result.json',0,0)
    # ld.getAspectId(27,82)
    ld.load2record(3901,10)