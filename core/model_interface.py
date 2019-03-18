# coding=UTF-8
from abc import abstractmethod, ABCMeta, abstractclassmethod


class ModelInterface(metaclass=ABCMeta):  # 抽象类/接口类

    #存储模型
    @abstractmethod
    def save_model(self,model_path,*kwargs):pass

    #加载模型
    @abstractmethod
    def load_model(self,model_path):pass

    #训练模型
    @abstractmethod
    def train_model(self,trainData_path,save_model_path,model_name):pass

    #预测模型
    @abstractmethod
    def predict_model(self,predictDataFile,model_path,save_file,tagClassId_list,threshold=-0.2):pass

    #评估模型
    @abstractmethod
    def validation_model(self):pass