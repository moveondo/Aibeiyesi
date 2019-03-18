# coding=UTF-8
import abc
import json
import os
from abc import abstractclassmethod, ABCMeta
from json import JSONDecodeError
import _operator as op
import logging

import requests
from PyPDF2 import PdfFileReader

from common import mylogger
from common.database.mysql_utils import MyPymysqlPool
from common.taskManager import TaskManager
from core.bysparams import BysParams
from interface.execute_interface import ExecuteInterface


class ExecuteAbstract(ExecuteInterface):  # 抽象类


    def __init__(self,log_name):
        mylogger.setup_logging(fileName = '../log/'+log_name+'.log')
        self.logger = logging.getLogger('console.'+log_name)
        self.params_dict = {}
        self.store_message_dict = {}
        self.output_values = {}
        self.mq_message = ''
        self.basePath = ''
        self.file_path = ''
        self.taskName = ''
        self.jobId = ''
        self.docId = ''
        self.stockCode = ''
        self.bm_id = ''
        self.corp_analyze_id = ''
        self.train_start = ''
        self.predict_result_file = ''
        self.predict_type = ''
        self.model_name = ''
        self.tagClassId_list = []

    @abc.abstractmethod
    def execute(self):
        pass

    def getObj_params(self):
        self.bys_params = BysParams()
        return self.bys_params

    def getBmId(self,corp_analyze_id):
        if self.bys_params.env == 'test':
            self.conf_name = 'MysqlTest'
        elif self.bys_params.env == 'dev':
            self.conf_name = 'MysqlDev'
        mp = MyPymysqlPool.instance(conf_path=r"../conf/mysql.ini",conf_name=self.conf_name)
        sql = """SELECT bm_id FROM tb_corp_analyze WHERE id=%s""" %(corp_analyze_id)
        result = mp.getAll(sql)
        for row in result:
            bm_id = row['bm_id']
        return bm_id

    def getTagClassId(self,bm_id):
        if self.bys_params.env == 'test':
            self.conf_name = 'MysqlTest'
        elif self.bys_params.env == 'dev':
            self.conf_name = 'MysqlDev'
        sql = """SELECT tag_class_id FROM tb_analyze_aspect WHERE biz_model=%s""" %(bm_id)
        mp = MyPymysqlPool.instance(conf_path=r"../conf/mysql.ini",conf_name=self.conf_name)
        result = mp.getAll(sql)
        tagClassId_list = []
        if result:
            for row in result:
                tag_class_id = row['tag_class_id']
                tagClassId_list.append(tag_class_id)
        return tagClassId_list


    def getPredictMessage(self,corp_analyze_id,predict_type):
        if self.bys_params.env == 'test':
            self.conf_name = 'MysqlTest'
        elif self.bys_params.env == 'dev':
            self.conf_name = 'MysqlDev'
        mp = MyPymysqlPool.instance(conf_path=r"../conf/mysql.ini",conf_name=self.conf_name)
        if predict_type == 'all':
            sql = """SELECT * FROM tb_crawler_result WHERE stock_code=(SELECT corp_code FROM tb_corp_analyze WHERE id=%s) AND info_catagory_id IN (SELECT DISTINCT c.`info_catagory_id` FROM tb_corp_analyze AS a INNER JOIN tb_analyze_aspect AS b ON a.bm_id=b.biz_model INNER JOIN tb_analyze_source AS c ON b.id=c.analyze_aspect_id)""" % (corp_analyze_id)
            result = mp.getAll(sql)
        elif predict_type == 'increment':
            sql0 = """SELECT * FROM tb_crawler_result WHERE stock_code=(SELECT corp_code FROM tb_corp_analyze WHERE id=%s) AND info_catagory_id IN (SELECT DISTINCT c.`info_catagory_id` FROM tb_corp_analyze AS a INNER JOIN tb_analyze_aspect AS b ON a.bm_id=b.biz_model INNER JOIN tb_analyze_source AS c ON b.id=c.analyze_aspect_id)""" % (corp_analyze_id)
            sql1 = """select DISTINCT doc_id  from tb_doc_corp_analyze_execute where corp_analyze_id=%s""" % (corp_analyze_id)
            self.logger.info('查询数据库预测记录')
            result_crawler = mp.reSetConnection().getAll(sql0)
            result_record = mp.reSetConnection().getAll(sql1)
            if not result_crawler:
                raise BaseException('未查询到corp_analyze_id='+str(corp_analyze_id)+'相关的文档，还请检查')
            if not result_record:
                return result_crawler

            predict_result = []
            for row_crawler in result_crawler:
                doc_id = row_crawler['id']
                b = False
                for row_record in result_record:
                    if str(row_record['doc_id']) == str(doc_id):
                        b = True
                        continue
                if not b:
                    self.logger.info('还需要预测='+str(doc_id))
                    predict_result.append(row_crawler)
            result = predict_result
        return result



    def receiveMessage(self,message):
        self.mq_message = message
        try:
            self.params_dict = json.loads(self.mq_message)
            self.model_name = self.params_dict['model_name']
            if 'train_start' not in self.params_dict.keys():
                self.corp_analyze_id = self.params_dict['corp_anaylze_id']
                self.predict_type = self.params_dict['predict_type']
                self.bm_id = self.getBmId(self.corp_analyze_id)
                self.tagClassId_list = self.getTagClassId(self.bm_id)
                self.result = self.getPredictMessage(self.corp_analyze_id,self.predict_type)
            else:
                self.train_start = self.params_dict['train_start']
        except JSONDecodeError:
            self.logger.error('json转换出错')
            raise JSONDecodeError

    def process(self):
        produce_message_dict = {}
        close = False
        if self.bys_params.run_type=='train':
            self.logger.info('训练模式')
            close = True
        else:
            self.logger.info('预测模式')
            self.logger.debug('basePath:' + self.basePath)
            self.file_path = os.path.join(self.basePath, self.file_path)


            produce_message_dict['predictResult'] = self.predict_result_file  # 预测结果

        self.execute()

        produce_message_dict['modelPath'] = self.bys_params.model_path
        produce_message_dict['run_type'] = self.bys_params.run_type
        message_producer_json = json.dumps(produce_message_dict)
        TaskManager.updateData({'produce':message_producer_json})
        return message_producer_json,close
