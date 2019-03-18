# coding=UTF-8
import logging
import os
import sys
import traceback

sys.path.append(sys.argv[2])
from core.unsupervised.downloadTxt import DownLoadTxt
from core.unsupervised.unsupervised_model import unsupervised_model
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
        elif self.model_name == 'unsupervised':
            mod = unsupervised_model()
            self.bys_params.model_path = '../data/save_model/unsupervised_save_model'

        ld = Load2DB(self.bys_params.load_db_env)
        if self.bys_params.run_type == 'train' and self.train_start == 'yes':
            if not self.model_name == 'unsupervised':
                if self.bys_params.new_trainData == 'yes':
                    #根据用户标注内容和解析的tree.json文件构造出训练集
                    td = TrainData(self.bys_params.env,self.bys_params.need_download)
                    params_dict = td.getLabelPosition(self.bys_params.labelPositionFile,self.bys_params.change)
                    td.TrainDataFile(params_dict,self.bys_params.trainDataFile)
                #训练模型
                mod.train_model(self.bys_params.trainDataFile, self.bys_params.model_path,self.model_name)
            else:
                d = DownLoadTxt()
                train_data_path = r'../data/unsupervised_data/'
                result = d.downloadTask('pdf2txt', train_data_path, 10, self.bys_params.need_download)
                # 训练模型
                # result结果有两种格式，在本地运行时，会将txt文件下到本地，result为string类型，是多个txt的路径
                # result在集群运行时，会返回list<Row>类型，row是dict类型，有doc_id,dest,source三种数据类型,使用row['dest']获得各txt文件路径
                mod.train_model(result, self.bys_params.model_path,self.model_name)

        elif self.bys_params.run_type == 'predict':
            ld.deleteData('tb_ai_text_tagging', self.corp_analyze_id,self.model_name)
            for row in self.result:
                b = False
                self.docId = row['id']
                self.stockCode = row['stock_code']
                self.type = row['type']
                file_path = row['file_path']
                self.file_path = os.path.join(os.path.splitext(str(file_path))[0], 'paragraph').replace('bhpdf', 'ahpdf1')
                self.file_path = os.path.join(self.basePath,self.file_path)
                if not os.path.exists(self.file_path):
                    print(self.docId,self.file_path,'不存在')
                    continue
                id = TaskManager.addTask(self.mq_message, self.jobId, self.docId, self.type, self.taskName,
                                         self.stockCode,
                                         self.file_path, 'null')
                TaskManager.setId(id)
                save_result_path = os.path.join(os.path.split(self.file_path)[0], 'predictResult')
                if not os.path.exists(save_result_path):
                    os.makedirs(save_result_path)
                save_result_file = os.path.join(save_result_path,
                                            os.path.split(os.path.split(self.file_path)[0])[1] + '_' + self.model_name + '_vp_predictResult_' + str(
                                                self.bm_id) + '.json')
                model_path = os.path.join(self.bys_params.model_path, self.model_name+'_modelFile_common' + '.pkl')
                TaskManager.updateData({'dest': save_result_path})

                try:
                    # 根据模型预测结果
                    load = mod.predict_model(self.file_path, model_path, save_result_file,
                                self.tagClassId_list,self.bys_params.threshold)
                    self.logger.info(load)
                except Exception as e:
                    TaskManager.updateTask('异常', str(e), 0)
                    traceback.print_exc()
                    continue
                # 将结果load到数据库
                if load:
                    ld.loadFile2DB('tb_ai_text_tagging', self.model_name, save_result_file, self.docId,
                               self.stockCode, self.corp_analyze_id, self.bys_params.user_id, self.bm_id)
                    b = True
                TaskManager.updateTask('完成', 'over', 100)
                if b:
                    ld.load2record(self.docId,self.corp_analyze_id)

if __name__ == '__main__':
    args = sys.argv
    execute_engine(BysModel_Main(),args=args[3:])