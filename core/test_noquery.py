# coding=UTF-8
import logging
import os
import sys

from core.TrainData import TrainData
from core.bys_model import bys_model
from core.bysparams import BysParams
from core.loadFile2db import Load2DB
from core.predictData import PredictData
from common.taskManager import TaskManager
from common.decorator import caltime
from common.execute_engine import execute_engine
from core.svm_model import svm_model
from core.unsupervised.downloadTxt import DownLoad
from core.unsupervised.unsupervised_model import unsupervised_model

from interface.execute_abstract import ExecuteAbstract


class AI_Bys_Main(ExecuteAbstract):

    def __init__(self,params = None):
        self.bys_params = params
        super(AI_Bys_Main,self).__init__(log_name='Demo')
        self.logger = logging.getLogger('root.'+self.__class__.__name__)


    @caltime
    def execute(self,model_name):
        if model_name == 'bys':
            mod = bys_model()
            bysparams.model_path = '../data/save_model/bys_save_model'
        elif model_name == 'svm':
            mod = svm_model()
            bysparams.model_path = '../data/save_model/svm_save_model'
        elif model_name == 'unsupervised':
            mod = unsupervised_model()
            self.bys_params.model_path = '../data/save_model/unsupervised_save_model'

        ld = Load2DB(self.bys_params.load_db_env)
        if self.bys_params.run_type == 'train':
            if not model_name == 'unsupervised':
                if self.bys_params.new_trainData == 'yes':
                    #根据用户标注内容和解析的tree.json文件构造出训练集
                    td = TrainData(self.bys_params.env,self.bys_params.need_download)
                    params_dict = td.getLabelPosition(self.bys_params.labelPositionFile,self.bys_params.change)
                    td.TrainDataFile(params_dict,self.bys_params.trainDataFile)
                #训练模型
                mod.train_model(self.bys_params.trainDataFile, self.bys_params.model_path,model_name)
            else:
                d = DownLoad()
                train_data_path = r'../data/unsupervised_data/'
                result = d.downloadTask('pdf2txt', train_data_path, 10,self.bys_params.need_download)
                # 训练模型
                #result结果有两种格式，在本地运行时，会将txt文件下到本地，result为string类型，是多个txt的路径
                #result在集群运行时，会返回list<Row>类型，row是dict类型，有doc_id,dest,source三种数据类型,使用row['dest']获得各txt文件路径
                mod.train_model(result, self.bys_params.model_path,model_name)
            #训练好模型后关闭进程
            # pid = os.getpid()
            # os.system('kill -9 '+pid)
        elif self.bys_params.run_type == 'predict':
            #预测时首先删除原有数据
            if self.predict_type == 'all':
                ld.deleteData('tb_ai_text_tagging',self.corp_analyze_id,model_name)
                pass
            if not os.path.exists(self.file_path):
                print(self.file_path,'不存在')
            # model_path = os.path.join(self.bys_params.model_path, model_name+'_modelFile_' + str(self.bm_id) + '.pkl')
            model_path = os.path.join(self.bys_params.model_path, model_name+'_modelFile_common' +'.pkl')
            # TaskManager.updateData({'dest': save_result_path})
            save_result_path = os.path.join(os.path.split(self.file_path)[0], 'predictResult')
            a = os.path.split(os.path.split(self.file_path)[0])[1]
            if not os.path.exists(save_result_path):
                os.makedirs(save_result_path)
            save_result_file = os.path.join(save_result_path,
                                            os.path.split(os.path.split(self.file_path)[0])[1] + '_' + model_name + '_vp_predictResult_' + str(
                                                self.bm_id) + '.json')
            # 根据模型预测结果
            mod.predict_model(self.file_path, model_path, save_result_file,
                              self.tagClassId_list,self.bys_params.threshold)
            # 将结果load到数据库
            # ld.loadFile2DB('tb_ai_text_tagging', 'paragraph',save_result_file, self.docId, self.stockCode,self.corp_analyze_id,self.bys_params.user_id,self.bm_id)
                # ld.loadFile2DB_tb_ai('tb_ai', 'aiBysModel', predictFilePath, save_result_file, self.docId,
                #                      self.stockCode)

if __name__ == '__main__':
    bysparams = BysParams()
    bysparams.env = 'dev'
    bysparams.load_db_env = 'test'
    bysparams.change = 'no'
    bysparams.need_download = 'no'
    bysparams.threshold = '-2.0'
    bysparams.run_type = 'predict'
    bysparams.new_trainData = 'no'

    bysparams.user_id = '90'
    abm = AI_Bys_Main(bysparams)
    abm.tagClassId_list = abm.getTagClassId(63)
    abm.bm_id = 74
    abm.docId = 3908
    abm.predict_type = 'all' #increment
    abm.corp_analyze_id = 63
    abm.stockCode = '000333'
    abm.file_path = r'../data/92254a02922b414886f84793b2a7209b/paragraph'
    abm.execute('bys')

    # abm.getPredictMessage(10,'increment')