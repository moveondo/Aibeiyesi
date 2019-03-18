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

        ld = Load2DB(self.bys_params.load_db_env)
        if self.bys_params.run_type == 'train':
            if self.bys_params.new_trainData == 'yes':
                #根据用户标注内容和解析的tree.json文件构造出训练集
                td = TrainData(self.bys_params.env,self.bys_params.need_download)
                params_dict = td.getLabelPosition(self.bys_params.labelPositionFile,self.bys_params.change)
                td.TrainDataFile(params_dict,self.bys_params.trainDataFile)
            #训练模型
            mod.train_model(self.bys_params.trainDataFile, self.bys_params.model_path,model_name)
            #训练好模型后关闭进程
            # pid = os.getpid()
            # os.system('kill -9 '+pid)
        elif self.bys_params.run_type == 'predict':
            #预测时首先删除原有数据
            if self.predict_type == 'all':
                # ld.deleteData('tb_ai_text_tagging',self.corp_analyze_id)
                pass
            if not os.path.exists(self.file_path):
                print(self.file_path,'不存在')
            pd = PredictData()
            list = os.listdir(self.file_path)
            count = len(list)
            for i in range(0, count):
                file_path = os.path.join(self.file_path, list[i])
                predictOPFilePath = os.path.join(os.path.split(self.file_path)[0], 'prePredictData')
                if not os.path.exists(predictOPFilePath):
                    os.makedirs(predictOPFilePath)
                if os.path.isfile(file_path) and file_path.endswith('.json'):
                    # 从原始文件中提炼出预测数据
                    pd.getPredictData(file_path, predictOPFilePath)
                    list1 = os.listdir(predictOPFilePath)
                    count1 = len(list1)
                    for i in range(0, count1):
                        predictFilePath = os.path.join(predictOPFilePath, list[i].split('_tree')[0] + '_prePredict.json')
                        save_result_path = os.path.join(os.path.split(self.file_path)[0], 'predictResult')
                        if not os.path.exists(save_result_path):
                            os.makedirs(save_result_path)
                        save_result_file = os.path.join(save_result_path,
                                                        list[i].split('_tree')[0] + '_'+model_name+'_predictResult_' + str(
                                                            self.bm_id) + '.json')
                        model_path = os.path.join(self.bys_params.model_path, model_name+'_modelFile_' + str(self.bm_id) + '.pkl')
                        # TaskManager.updateData({'dest': save_result_path})


                        # 根据模型预测结果
                        mod.predict_model(predictFilePath, model_path, save_result_file,
                                        self.bys_params.threshold)
                        # 将结果load到数据库
                        ld.loadFile2DB('tb_ai_text_tagging', 'nbysModel',save_result_file, self.docId, self.stockCode,self.corp_analyze_id,self.bys_params.user_id,self.bm_id)
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
    abm.bm_id = 26
    abm.docId = 3908
    abm.predict_type = 'all' #increment
    abm.corp_analyze_id = 12
    abm.stockCode = '000333'
    abm.file_path = r'../data/2ab0281819174d1eaa662a4ba50e7f83/tree'
    abm.execute('bys')

    # abm.getPredictMessage(10,'increment')