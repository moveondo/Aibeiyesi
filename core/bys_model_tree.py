#!/usr/bin/python
# coding=utf-8
#https://www.cnblogs.com/ahu-lichang/p/7157855.html
import json
import numpy as np

import jieba
import logging

import sklearn
from numpy import *
import os
import pickle

from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import Bunch

from core.loadData import LoadData
from core.model_interface import ModelInterface


class bys_model(ModelInterface):
    def __init__(self):
        self.logger = logging.getLogger('root.'+self.__class__.__name__)
        self.stopWords = open("../data/stop_words.txt", encoding='UTF-8').read().split("\n")

    def getTFIDFMat(self,bunch, stopWordList,vocabulary = None):  # 求得TF-IDF向量
        tfidfspace = Bunch(target_name=bunch.target_name,label=bunch.label, filenames=bunch.filenames, tdm=[],contents=[],
                           vocabulary={},page_id=bunch.page_id,start_offsets = bunch.start_offsets,end_offsets = bunch.end_offsets,
                           tag_class_id=bunch.tag_class_id)
        # 初始化向量空间
        vectorizer = TfidfVectorizer(stop_words=stopWordList, sublinear_tf=True, min_df=0.1,max_df=1.0,
                                     vocabulary = vocabulary)
        transformer = TfidfTransformer()  # 该类会统计每个词语的TF-IDF权值
        # 文本转化为词频矩阵，单独保存字典文件
        tfidfspace.tdm = vectorizer.fit_transform(bunch.contents)
        tfidfspace.vocabulary = vectorizer.vocabulary_   #获取词汇
        if not vocabulary:
            tfidfspace.contents = bunch.contents
        return tfidfspace


    def textParse(self,inputData):
        import re
        global stopWords
        inputData = "".join(re.findall(u'[\u4e00-\u9fa5]+', inputData))
        wordList = "/".join(jieba.cut(inputData))
        listOfTokens = wordList.split("/")
        return [tok for tok in listOfTokens if (tok not in self.stopWords and len(tok) >= 2)]

    def save_model(self,model_path,*kwargs):
        print('存储模型到：'+model_path)
        with open(model_path, 'wb') as f:
            for i in kwargs:
                pickle.dump(i, f, pickle.HIGHEST_PROTOCOL)

    def load_model(self,model_path ):
        self.logger.info('从模型中读取参数')
        with open(model_path, 'rb') as f:
            bunch = pickle.load(f)
            clf = pickle.load(f)
            accuracy = pickle.load(f)
            self.logger.info('模型准确率为：{}'.format(accuracy))
            return bunch,clf,accuracy

    def writeJsonFile(self,obj,filePath):
        with open(filePath, 'w', encoding='utf-8') as fp:
            json.dump(obj, fp, ensure_ascii=False, indent=4);

    def train_model(self,trainData_path,save_model_path,model_name):
        ld = LoadData()
        train_bunch_ori_dict = ld.loadData_userTagging(trainData_path)
        for key in train_bunch_ori_dict.keys():
            train_bunch_ori = train_bunch_ori_dict[key]
            try:
                self.train_bunch = self.getTFIDFMat(train_bunch_ori, ld.stopWords)
                if len(self.train_bunch['contents']) <= 1:
                    continue
                clf, accuracy = self.validation_model(self.train_bunch.tdm, self.train_bunch.label,100)
                print('模型准确率为:',accuracy)
            except ValueError:
                #产生原因通常是该标题全部属于停止词
                continue
            if not os.path.exists(save_model_path):
                os.makedirs(save_model_path)
            save_model_file_path = os.path.join(save_model_path,model_name+'_modelFile_'+str(key)+'.pkl')
            self.save_model(save_model_file_path,self.train_bunch,clf,accuracy)
        return clf

    def validation_model(self,train_data,train_label,max_train_count):
        count = 0
        tmp_clf = None
        tmp_accuracy = 0
        while True:
            count += 1
            x_train, x_test, y_train, y_test=\
                train_test_split(train_data,train_label,test_size=0.2)
            clf = MultinomialNB(alpha=0.001).fit(x_train, y_train)
            doc_class_predicted = clf.predict(x_test)
            # 求均值方法得到准确率
            me = np.mean(doc_class_predicted == y_test)
            labels = list(set(train_label))
            #使用混淆矩阵和kappa系数求模型准确率
            try:
                confusion = confusion_matrix(y_test, doc_class_predicted,labels)
            except Exception as e:
                print(e)
                print('dsfd')
            ka = self.kappa(confusion)
            accuracy = (me+ka)/2
            if accuracy>tmp_accuracy:
                tmp_accuracy = accuracy
                tmp_clf = clf
            if count>= max_train_count:
                return tmp_clf,tmp_accuracy


    def kappa(self,matrix):
        n = np.sum(matrix)
        sum_po = 0
        sum_pe = 0
        for i in range(len(matrix[0])):
            sum_po += matrix[i][i]
            row = np.sum(matrix[i, :])
            col = np.sum(matrix[:, i])
            sum_pe += row * col
        po = sum_po / n
        pe = sum_pe / (n * n)
        return (po - pe) / (1.1 - pe)

    def predict_model(self,predictDataFile,model_path,save_file,threshold=-0.2):
        ld = LoadData()
        if os.path.exists(model_path):
            self.logger.info('model_path is :'+model_path)
            train_bunch,clf,accuracy = self.load_model(model_path)
            predict_bunch_ori = ld.loadData_userTaggingPredict(predictDataFile)
            try:
                predict_bunch = self.getTFIDFMat(predict_bunch_ori, ld.stopWords,vocabulary=train_bunch.vocabulary)
            except ValueError:
                return False
            predicted = clf.predict(predict_bunch.tdm)#预测结果，未处理阀值，结果不够准确
            labels = clf.classes_.tolist()
            predict_log_proba = clf.predict_log_proba(predict_bunch.tdm)
            predict_log_proba_list = predict_log_proba.tolist()
            label_tagClassId = dict(zip(train_bunch.label, train_bunch.tag_class_id))
            #进行转置方便之后做归一化
            # predict_log_proba_list_tran = np.transpose(predict_log_proba_list)

            predict_reuslt = {}
            expct_cate_count = 0
            max_value_list = []
            for title,log_probas,page_id,start,end in zip(predict_bunch_ori.titles, predict_log_proba_list,predict_bunch_ori.page_id,predict_bunch_ori.start_offsets,predict_bunch_ori.end_offsets):
                max_value = max(log_probas)
                # min_value = min(log_probas)
                # a = map(lambda x:(x-min_value)/(max_value-min_value),log_probas)
                # b = list(a)
                if max_value < float(threshold):
                    continue
                max_value_list.append(max_value)
                index = log_probas.index(max_value)
                expct_cate = labels[index]
                # print( contents, "-->预测类别：", expct_cate,'-->page_id:',page_id,'start-end:',start,'--',end)
                position = {}
                pre_list = []
                position['page_id'] = page_id
                position['start_offset'] = start
                position['end_offset'] = end
                position['title'] = title
                position['confidence'] = max_value
                position['tag_class_id'] = label_tagClassId[expct_cate]
                position['id'] = expct_cate_count
                position['accuracy'] = accuracy
                position['threshold'] = float(threshold)
                expct_cate_count += 1
                if expct_cate in predict_reuslt:
                    pre_list = predict_reuslt[expct_cate]
                    pre_list.append(position)
                    predict_reuslt[expct_cate] = pre_list
                else:
                    pre_list.append(position)
                    predict_reuslt[expct_cate] = pre_list
            # 归一化
            if len(max_value_list) == 0:
                return False
            minMax = MinMaxScaler()
            max_value_np = np.array(max_value_list).reshape(len(max_value_list),1)
            max_value_np_std = minMax.fit_transform(max_value_np)
            for data_values in predict_reuslt.values():
                for position in data_values:
                    id = position['id']
                    confidence0 = max_value_np_std[id, 0]
                    position['confidence']=confidence0 + float(threshold)
            self.logger.info('生成预测结果文件:{}'.format(save_file))
            self.writeJsonFile(predict_reuslt,save_file)
            return True

            #显示训练集中标签对应信息，在调试时使用
            # train_result = {}
            # for label,content,page_id,start_offset,end_offset in zip(train_bunch.label,train_bunch.contents,train_bunch.page_id,train_bunch.start_offsets,train_bunch.end_offsets):
            #     print(label,'对应-->',page_id,' ',start_offset,'--',end_offset)
            #     position = {}
            #     train_list = []
            #     position['page_id'] = page_id
            #     position['start_offset'] = start_offset
            #     position['end_offset'] = end_offset
            #     position['title'] = content
            #     if label in train_result:
            #         train_list = train_result[label]
            #         train_list.append(position)
            #         train_result[label] = train_list
            #     else:
            #         train_list.append(position)
            #         train_result[label] = train_list
        else:
            print('模型'+model_path+'不存在')
            raise RuntimeError

if __name__ == '__main__':
    tarin_model_path = r'../data/'
    trainData_path = r'../data/trainData.json'
    predictDataFile = r'../data/9fb125d66147473cbfb3504feefff764/prePredictData/9fb125d66147473cbfb3504feefff764_prePredict.json'
    predict_model_path = r'../data/modelFile_26.pkl'
    save_result_file = r'../data/predictResult_26.json'
    threshold = -0.2
    bm = bys_model()
    # bm.train_model(trainData_path,tarin_model_path)
    bm.predict_model(predictDataFile,predict_model_path,save_result_file,threshold)

