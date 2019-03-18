#!/usr/bin/python
# coding=utf-8
from core.model_interface import ModelInterface


class unsupervised_model(ModelInterface):

   def __init__(self):
       pass

   def load_model(self, model_path):
       pass

   def train_model(self, trainData_path, save_model_path, model_name):
       pass

   def predict_model(self, predictDataFile, model_path, save_file,tagClassId_list,threshold=-0.2):
       pass

   def save_model(self, model_path, *kwargs):
       pass

   def validation_model(self):
       pass


if __name__ == '__main__':
    pass
