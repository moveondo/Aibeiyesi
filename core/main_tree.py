# coding=UTF-8
import logging
import os
import sys
import traceback

sys.path.append(sys.argv[2])
print(sys.path)
from core.svm_model import svm_model
from core.TrainData import TrainData
from core.bys_model import bys_model
from core.loadFile2db import Load2DB
from core.predictData import PredictData
from common.taskManager import TaskManager
from common.decorator import caltime
from common.execute_engine import execute_engine
from interface.execute_abstract import ExecuteAbstract


class BysModel_Main(ExecuteAbstract):

    def __init__(self):
        log_name = os.path.basename(__file__).split('.')[0]
        super(BysModel_Main,self).__init__(log_name = log_name)
        self.logger = logging.getLogger('root.'+self.__class__.__name__)


    @caltime
    def execute(self):
        if self.model_name == 'bys':
            mod = bys_model()
            self.bys_params.model_path = '../data/save_model/bys_save_model'
        elif self.model_name == 'svm':
            mod = svm_model()
            self.bys_params.model_path = '../data/save_model/svm_save_model'

        ld = Load2DB(self.bys_params.load_db_env)
        if self.bys_params.run_type == 'train' and self.train_start == 'yes':
            if self.bys_params.new_trainData == 'yes':
                #根据用户标注内容和解析的tree.json文件构造出训练集
                td = TrainData(self.bys_params.env,self.bys_params.need_download)
                params_dict = td.getLabelPosition(self.bys_params.labelPositionFile,self.bys_params.change)
                td.TrainDataFile(params_dict,self.bys_params.trainDataFile)
            #训练模型
            mod.train_model(self.bys_params.trainDataFile, self.bys_params.model_path,self.model_name)

        elif self.bys_params.run_type == 'predict':
            # ld.deleteData('tb_ai_text_tagging', self.corp_analyze_id)
            for row in self.result:
                b = False
                self.docId = row['id']
                self.stockCode = row['stock_code']
                self.type = row['type']
                file_path = row['file_path']
                self.file_path = os.path.join(os.path.splitext(str(file_path))[0], 'tree').replace('bhpdf', 'ahpdf1')
                self.file_path = os.path.join(self.basePath,self.file_path)
                if not os.path.exists(self.file_path):
                    print(self.file_path,'不存在')
                    continue
                id = TaskManager.addTask(self.mq_message, self.jobId, self.docId, self.type, self.taskName,
                                         self.stockCode,
                                         self.file_path, 'null')
                TaskManager.setId(id)
                pd = PredictData()
                list = os.listdir(self.file_path)
                count = len(list)
                for i in range(0, count):
                    file_path = os.path.join(self.file_path, list[i])
                    predictOPFilePath = os.path.join(os.path.split(self.file_path)[0], 'prePredictData')
                    if not os.path.exists(predictOPFilePath):
                        os.makedirs(predictOPFilePath)
                    if os.path.isfile(file_path) and file_path.endswith('tree.json'):
                        # 从原始文件中提炼出待预测数据
                        self.logger.info('预测文章:{}'.format(file_path))
                        pd.getPredictData(file_path, predictOPFilePath)
                        list1 = os.listdir(predictOPFilePath)
                        count1 = len(list1)
                        for i in range(0, count1):
                            predictFilePath = os.path.join(predictOPFilePath, list[i].split('_tree')[0] + '_prePredict.json')
                            save_result_path = os.path.join(os.path.split(self.file_path)[0], 'predictResult')
                            if not os.path.exists(save_result_path):
                                os.makedirs(save_result_path)
                            save_result_file = os.path.join(save_result_path,
                                                            list[i].split('_tree')[0] +'_'+self.model_name+ '_predictResult_' + str(
                                                                self.bm_id) + '.json')
                            model_path = os.path.join(self.bys_params.model_path, self.model_name+'_modelFile_' + str(self.bm_id) + '.pkl')
                            TaskManager.updateData({'dest': save_result_path})

                            try:
                                # 根据模型预测结果
                                load = mod.predict_model(predictFilePath, model_path, save_result_file,
                                            self.bys_params.threshold)
                            except Exception as e:
                                TaskManager.updateTask('异常', str(e), 0)
                                traceback.print_exc()
                                continue
                            # 将结果load到数据库
                            if load:
                                ld.loadFile2DB('tb_ai_text_tagging', self.model_name, save_result_file, self.docId,
                                           self.stockCode, self.corp_analyze_id, self.bys_params.user_id, self.bm_id)
                                b = True
                            # ld.loadFile2DB_tb_ai('tb_ai', 'aiBysModel', predictFilePath, save_result_file, self.docId,
                            #                      self.stockCode)
                            TaskManager.updateTask('完成', 'over', 100)
                if b:
                    ld.load2record(self.docId,self.corp_analyze_id)

if __name__ == '__main__':
    args = sys.argv
    execute_engine(BysModel_Main(),args=args[3:])