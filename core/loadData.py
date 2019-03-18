#coding=utf-8
import json
import os

import jieba
import logging
from sklearn.utils import Bunch


class LoadData():

    def __init__(self):
        self.stopWords = open("../data/stop_words.txt", encoding='UTF-8').read().split("\n")
        self.logger = logging.getLogger('root.LoadData')

    def readFile(self,path):
        with open(path, 'r', errors='ignore') as file:  # 文档中编码有些问题，所有用errors过滤错误
            content = file.read()
            return content

    def saveFile(self,path, result):
        with open(path, 'w', errors='ignore') as file:
            file.write(result)

    def readJsonFile(self,filePath):
        with open(filePath,'r',encoding='utf-8') as fp:
            params= json.load(fp)
        return params

    def textParse(self,inputData):
        import re
        # inputData = "".join(re.findall(u'[\u4e00-\u9fa5]+', inputData))
        wordList = "|".join(jieba.cut(inputData))
        listOfTokens = wordList.split("|")
        return [tok for tok in listOfTokens if (tok not in self.stopWords and tok != ' ')]

    #不按行业分类模型了
    def loadData_userTagging_noBmid(self,filePath):
        bunch_dict = {}
        target_set = set()
        bunch = Bunch(target_name=[], label=[], label_name=[],contents=[], filenames=[],
                                  start_offsets=[], end_offsets=[], page_id=[], tag_class_id=[])
        train_dict = self.readJsonFile(filePath)
        for key in train_dict.keys():
            trainData = key
            tagging_list = train_dict[key]
            for tagging_dict in tagging_list:
                if trainData.strip() == '无Level_0 /':
                    continue
                trainData1=trainData+tagging_dict['text']
                cutTrainData = self.textParse(trainData1)
                if len(cutTrainData)==0:
                    continue
                bunch.contents.append(' '.join(cutTrainData))
                bunch.label.append(tagging_dict['tag_class_id'])
                bunch.label_name.append(tagging_dict['label'])
                bunch.start_offsets.append(tagging_dict['start_offset'])
                bunch.end_offsets.append(tagging_dict['end_offset'])
                bunch.page_id.append(tagging_dict['page_id'])
                bunch.tag_class_id.append(tagging_dict['tag_class_id'])
                target_set.add(tagging_dict['label'])
        bunch_dict['common'] = bunch
        return bunch_dict


    #按bm_id分类模型，现在不使用了
    def loadData_userTagging(self,filePath):
        bunch_dict = {}
        target_set = set()
        train_dict = self.readJsonFile(filePath)
        for key in train_dict.keys():
            trainData = key
            tagging_list = train_dict[key]
            for tagging_dict in tagging_list:
                bm_id = tagging_dict['bm_id']
                if bm_id in bunch_dict.keys():
                    bunch = bunch_dict[bm_id]
                else:
                    bunch = Bunch(target_name=[], label=[], contents=[], filenames=[],
                                  start_offsets=[], end_offsets=[], page_id=[], tag_class_id=[])
                if trainData.strip() == '无Level_0 /':
                    continue
                trainData+=tagging_dict['text']
                cutTrainData = self.textParse(trainData)
                bunch.contents.append(' '.join(cutTrainData))
                bunch.label.append(tagging_dict['label'])
                bunch.start_offsets.append(tagging_dict['start_offset'])
                bunch.end_offsets.append(tagging_dict['end_offset'])
                bunch.page_id.append(tagging_dict['page_id'])
                bunch.tag_class_id.append(tagging_dict['tag_class_id'])
                target_set.add(tagging_dict['label'])
                bunch_dict[bm_id] = bunch
                bunch.filenames.append(filePath)
                bunch.target_name.append(target_set)
        return bunch_dict

    def loadData_userTaggingPredict_v_paragraph(self,dirPath):
        files = os.listdir(dirPath)
        bunch = Bunch(target_name=[],label=[],contents=[],filenames=[],text=[],
                      start_offsets=[], end_offsets=[], page_id=[],tag_class_id=[],titles=[])
        for file in files:
            if not file.endswith('_catalog.json'):
                file_path = os.path.join(dirPath,file)
                predict_list = self.readJsonFile(file_path)
                for predict_dict in predict_list:
                    text = predict_dict['text']
                    if len(text)<30:
                        continue
                    try:
                        cutPredictData = self.textParse(predict_dict['text'])
                        bunch.contents.append(' '.join(cutPredictData))
                        bunch.text.append(predict_dict['text'])
                        bunch.page_id.append(os.path.splitext(file)[0].split('_p')[1])
                        try:
                            bunch.start_offsets.append(predict_dict['data_offset_start'])
                            bunch.end_offsets.append(predict_dict['data_offset_end'])
                        except KeyError:
                            bunch.start_offsets.append(predict_dict['data-offset-start'])
                            bunch.end_offsets.append(predict_dict['data-offset-end'])
                        bunch.target_name.append(file)
                        bunch.filenames.append(file)
                    except KeyError:
                        continue
        return bunch


    def loadData_userTaggingPredict(self,filePath):
        bunch = Bunch(target_name=[],label=[],contents=[],filenames=[],
                      start_offsets=[], end_offsets=[], page_id=[],tag_class_id=[],titles=[])
        predict_list = self.readJsonFile(filePath)
        for predict_dict in predict_list:
            cutPredictData = self.textParse(predict_dict['title'])
            bunch.contents.append(' '.join(cutPredictData))
            bunch.titles.append(predict_dict['title'])
            bunch.page_id.append(predict_dict['textMessage']['page_id'])
            bunch.start_offsets.append(predict_dict['textMessage']['data_offset_start'])
            bunch.end_offsets.append(predict_dict['textMessage']['data_offset_end'])
        bunch.target_name.append(filePath)
        bunch.filenames.append(filePath)
        return bunch



if __name__ == '__main__':
    ld = LoadData()
    trainFilePath = '../data/trainData.json'
    predictFilePath = '../data/be5ce31ffa0d4bdb86f3a82d5680d6f4_prePredict.json'
    # ld.loadData_userTagging(trainFilePath)
    # ld.loadData_userTagging_noBmid(trainFilePath)
    # ld.loadData_userTaggingPredict(predictFilePath)
    ld.loadData_userTaggingPredict_v_paragraph(r'../data/paragraph')