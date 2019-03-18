import json
import os


class PredictData():
    def __init__(self):
        pass

    def readJsonFile(self,filePath):
        with open(filePath,'r',encoding='utf-8') as fp:
            params_dict = json.load(fp)
        return params_dict

    def getPredictData(self,inputFilePath,outputPath):
        file_name = os.path.split(inputFilePath)[1].split('_tree')[0]
        self.title_list = []
        load_dict = self.readJsonFile(inputFilePath)
        predict_dict = {}
        for Level_0 in load_dict['children']:
            if Level_0['level'] == 'Text':
                continue
            elif 'children' not in Level_0:
                continue
            else:
                predict_dict['Level_0'] = Level_0['text']
                for Level_1 in Level_0['children']:
                    if Level_1['level'] == 'Text':
                        predict_dict['Level_1'] = 'self_1'
                        message_dict = self.getTextMessage(Level_1)
                        self.process(predict_dict,message_dict)
                        continue
                    elif 'children' not in Level_1:
                        message_dict = self.getTextMessage(Level_1)
                        self.process(predict_dict,message_dict)
                        continue
                    else:
                        predict_dict['Level_1'] = Level_1['text']
                        for Level_2 in Level_1['children']:
                            if Level_2['level'] == 'Text':
                                predict_dict['Level_2'] = 'self_2'
                                message_dict = self.getTextMessage(Level_2)
                                self.process(predict_dict, message_dict)
                                continue
                            elif 'children' not in Level_2:
                                message_dict = self.getTextMessage(Level_2)
                                self.process(predict_dict, message_dict)
                                continue
                            else:
                                predict_dict['Level_2'] = Level_2['text']
                                for Level_3 in Level_2['children']:
                                    predict_dict['Level_3'] = 'self_3'
                                    message_dict = self.getTextMessage(Level_3)
                                    self.process(predict_dict,message_dict)
        filePath = os.path.join(outputPath,file_name+'_prePredict.json')
        self.writeFile(self.title_list,filePath)

    def getTextMessage(self,Level_x):
        page_id = Level_x['pageid']
        data_offset_start = Level_x['data_offset_start']
        data_offset_end = Level_x['data_offset_end']
        return {'page_id':page_id,
                'data_offset_start':data_offset_start,
                'data_offset_end':data_offset_end}

    def process(self,predict_dict,message_dict):
        tmp_dict = {}
        li = [predict_dict[k] for k in sorted(predict_dict.keys())]
        title_str = ''
        for i in li:
            if i.startswith('self'):
                break
            else:
                title_str += i + ' / '
        tmp_dict['title'] = title_str
        tmp_dict['textMessage'] = message_dict
        self.title_list.append(tmp_dict)

    def writeFile(self,obj,filePath):
        with open(filePath, 'w', encoding='utf-8') as fp:
            json.dump(obj, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    filePath = '../data/tree/be5ce31ffa0d4bdb86f3a82d5680d6f4_tree.json'
    outputFilePath = '../data/'
    pd = PredictData()
    pd.getPredictData(filePath,outputFilePath)

