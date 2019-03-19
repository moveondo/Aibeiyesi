import json
import os

import logging
import traceback

import requests

from common.database.mysql_utils import MyPymysqlPool
from core.download import DownLoad


class TrainData():

    def __init__(self,env,need_download):
        self.logger = logging.getLogger('root.'+self.__class__.__name__)
        self.d = DownLoad()
        self.env = env
        self.need_download = need_download

    def writeFile(self,obj,filePath):
        with open(filePath, 'w', encoding='utf-8') as fp:
            json.dump(obj, fp, ensure_ascii=False, indent=4)

    def readFile(self,filePath):
        with open(filePath,'r',encoding='utf-8') as fp:
            params_dict = json.load(fp)
        return params_dict

    def queryDB(self,labelPositionFile):
        if self.env == 'test':
            conf_name = 'MysqlTest'
        elif self.env == 'dev':
            conf_name = 'MysqlDev'
        mp = MyPymysqlPool.instance(conf_path=r"../conf/mysql1.ini",conf_name=conf_name)
        params = ('a.id','a.doc_id','a.start_offset','a.end_offset','a.page_ind','a.tag_class_name','a.tag_class','b.bm_id','c.name')
        params = str(params).replace("'", '').replace("(",'').replace(")",'')
        sql = """SELECT %s FROM tb_text_tagging AS a INNER JOIN tb_corp_analyze AS b ON a.corp_analyze_id=b.id INNER JOIN tb_biz_model AS c ON b.bm_id=c.id WHERE a.type='annotation' and a.id>2752""" % params
        result = mp.getAll(sql)
        labelPosition_dict = {}
        for row in result:
            id = row['id']
            doc_id = row['doc_id']
            outFilePath = self.d.downloadTask('../data',doc_id,self.need_download,conf_name)
            start_offset = row['start_offset']
            end_offset = row['end_offset']
            page_id = row['page_ind']
            tag_class_name = row['tag_class_name']
            tag_class_id = row['tag_class']
            bm_id = row['bm_id']
            bm_name = row['name']
            tag_dict = {'start_offset':start_offset,
                        'end_offset':end_offset,
                        'page_id':page_id,
                        'outFilePath':outFilePath,
                        'id':id,
                        'tag_class_id':tag_class_id,
                        'tag_class_name':tag_class_name,
                        'bm_id':bm_id,
                        'bm_name':bm_name}
            if outFilePath:
                if doc_id in labelPosition_dict.keys():
                    labelPosition_list = labelPosition_dict[doc_id]
                    labelPosition_list.append(tag_dict)
                    labelPosition_dict[doc_id] = labelPosition_list
                else:
                    labelPosition_list = []
                    labelPosition_list.append(tag_dict)
                    labelPosition_dict[doc_id] = labelPosition_list
            else:
                labelPosition_list = []
                tag_dict['outFilePath']='null'
                labelPosition_list.append(tag_dict)
                labelPosition_dict[doc_id] = labelPosition_list
        self.writeFile(labelPosition_dict,labelPositionFile)
        return labelPosition_dict

    def getLabelPosition(self,labelPositionFile,change='no'):
        if os.path.exists(labelPositionFile) and change == 'no':
            self.logger.info('从文件读取labelPositionFile')
            params_dict = self.readFile(labelPositionFile)
        else:
            self.logger.info('从数据库查询labelPosition')
            params_dict = self.queryDB(labelPositionFile)
        return params_dict

    def TrainDataFile(self,labelPosition_dict,trainDataFile):
        self.logger.info('正在构建训练数据，请耐心等待')
        train_dict = {}
        for key,values_list in labelPosition_dict.items():
            for value in values_list:
                filePath = value['outFilePath']
                if filePath=='null':
                    continue
                start_offset = value['start_offset']
                end_offset = value['end_offset']
                page_id = value['page_id']
                label = value['tag_class_name']
                tag_class_id = value['tag_class_id']
                bm_id = value['bm_id']
                bm_name = value['bm_name']
                source_dict = {}
                source_dict['docId'] = key
                source_dict['pageInd'] = page_id
                source_dict['pageEnd'] = page_id
                source_dict['startOffset'] = start_offset
                source_dict['endOffset'] = end_offset
                source_str = self.getSource(source_dict)
                if start_offset and page_id and label:
                    try:
                        train_str = self.parseJsonFile(filePath,start_offset,page_id)
                    except BaseException:
                        traceback.print_exc()
                        continue
                    tagging_dict = {}
                    tagging_dict['label'] = label
                    tagging_dict['start_offset'] = start_offset
                    tagging_dict['end_offset'] = end_offset
                    tagging_dict['page_id'] = page_id
                    tagging_dict['tag_class_id'] = tag_class_id
                    tagging_dict['bm_id'] = bm_id
                    tagging_dict['bm_name'] = bm_name
                    tagging_dict['text'] = source_str
                    if train_str in train_dict:
                        # label_list = train_dict[train_str]
                        # if label not in label_list:          #在不考虑标注位置的情况下
                                                               #可去除重复的lable
                        #     label_list.append(label)
                        #     train_dict[train_str] = label_list
                        tagging_list = train_dict[train_str]
                        tagging_list.append(tagging_dict)
                        train_dict[train_str] = tagging_list
                    else:
                        # label_list =[]
                        # label_list.append(label)
                        # train_dict[train_str] = label_list
                        tagging_list = []
                        tagging_list.append(tagging_dict)
                        train_dict[train_str] = tagging_list
        self.logger.info('训练数据构建完成，存入{}'.format(trainDataFile))
        self.writeFile(train_dict,trainDataFile)

    def parseJsonFile(self,filePath,start_offset,page_id):
        """
        :param filePath: tree.json文件，解析标题的文件
        :param start_offset: 用户标注的开始位置
        :param page_id: 用户标注时对应的页码
        :return:
        深度遍历tree_dict,依次将遍历到的标题按层级放入dict中
        设置结束条件为page_id和start_offset
        """

        with open(filePath, 'r', encoding='utf-8') as load_f:
            load_dict = json.load(load_f)

        before_dict = {}
        stop = False
        break_point = 3
        for Level_0 in load_dict['children']:
            if stop:
                break
            if 'text' in Level_0:
                before_dict['Level_0'] = Level_0['text']
            else:
                before_dict['Level_0'] = '无Level_0'
            if page_id == Level_0['pageid']:
                if start_offset<Level_0['data_offset_start']:
                    stop = True
                    break_point = 0
            if 'children' not in Level_0:
                before_dict['Level_0'] = '无Level_0'
                continue
            for Level_1 in Level_0['children']:
                if stop:
                    break
                if 'text' in Level_1:
                    before_dict['Level_1'] = Level_1['text']
                else:
                    before_dict['Level_1'] = '无Leve1_1'
                if page_id == Level_1['pageid']:
                    if start_offset<Level_1['data_offset_start']:
                        stop = True
                        break_point = 1
                if 'children' not in Level_1:
                    before_dict['Level_2'] = '无Level_2'
                    continue
                for Level_2 in Level_1['children']:
                    if stop:
                        break
                    if 'text' in Level_2:
                        before_dict['Level_2'] = Level_2['text']
                    else:
                        before_dict['Level_2'] = '无Leve1_2'
                    if page_id == Level_2['pageid']:
                        if start_offset<Level_2['data_offset_start']:
                            stop = True
                            break_point = 2
                    if 'children' not in Level_2:
                        before_dict['Level_3'] = '无Leve1_3'
                        continue
                    for Level_3 in Level_2['children']:
                        if stop:
                            break
                        if 'text' in Level_3:
                            before_dict['Level_3'] = Level_3['text']
                        else:
                            before_dict['Level_3'] = '无Leve1_3'
                        if page_id == Level_3['pageid']:
                            if start_offset<Level_3['data_offset_start']:
                                stop = True
                                break_point =  3
        if break_point == 0:
            pass
        elif break_point == 1:
            before_dict['Level_1'] = 'self'
            before_dict['Level_2'] = 'null'
            before_dict['Level_3'] = 'null'
        elif break_point == 2:
            before_dict['Level_2'] = 'self'
            before_dict['Level_3'] = 'null'
        elif break_point == 3:
            before_dict['Level_3'] = 'self'

        li = [before_dict[k] for k in sorted(before_dict.keys())]
        str = ''
        for i in li:
            if i == 'self':
                break
            else:
                str += i+' / '
        return str
    def getSource(self,source_dict):
        url = 'http://tftest.hipland.net/tagmanage/labelDisplay/queryLabel'
        body = json.dumps(source_dict)
        self.logger.info(body)
        headers = {'content-type': "application/json"}
        response = requests.post(url, data=body, headers=headers)
        status_code = response.status_code
        source_str = ''
        if status_code == 200:
            result = response.text
            result_dict = json.loads(result)
            # print(result_dict)
            if result_dict['data']:
                source_str = result_dict['data']['text']
        if source_str == '':
            self.logger.info('未提取到text')
        else:
            self.logger.info(source_str)
        return source_str

if __name__ == '__main__':
    trainDataFile = r'../data/trainData.json'
    labelPositionFile = r'../data/labelPosition.json'
    env = 'dev'
    need_download = 'no'
    change = 'no'
    td = TrainData(env,need_download)
    params_dict = td.getLabelPosition(labelPositionFile,change)
    td.TrainDataFile(params_dict,trainDataFile)