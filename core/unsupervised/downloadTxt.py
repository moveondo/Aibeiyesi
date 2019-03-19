#encoding=utf-8
import json
import os

import requests

from common.database.mysql_utils import MyPymysqlPool


class DownLoadTxt():
    def __init__(self):
        self.baseUrl = 'http://tfstatic.hipland.net/'
        self.bashPath = '/home/pubdisk/'

    def queryTask(self,sql):
        result = self.mp.getAll(sql)
        return result

    def downloadTask(self,taskName,outputPath,limit,need_download):
        self.mp = MyPymysqlPool(conf_path=r"../conf/mysql1.ini", conf_name="MysqlDev")
        if need_download=='yes':
            result = self.getTaskFiles(taskName,outputPath,'.txt',limit)
        else:
            result = self.getTask(taskName,limit)
        #执行任一个下载任务后,关闭连接
        self.mp.dispose()
        return result

    def getTask(self,taskName,limit):
        sql = """select doc_id,dest,source from tb_task where status = '完成' and taskname = '"""+taskName+"""' limit """+str(limit)
        result = self.queryTask(sql)
        return result



    def getTaskFiles(self,taskName,outputPath,type,limit):
        sql = """select doc_id,dest,source from tb_task where status = '完成' and taskname = '"""+taskName+"""' limit """+str(limit)
        result = self.queryTask(sql)
        for row in result:
            docId = row['doc_id']
            fileName = os.path.splitext((row['source']).split('/')[-1])[0]
            if self.checkDocId(docId,taskName,fileName):
                continue
            sql_pageNumbers = """select page_numbers from tb_task where status = '完成' and taskname='pdf2html_v2' and doc_id ='""" + docId + "'" + """ and page_numbers is not null"""
            result_pageNumbers = self.queryTask(sql_pageNumbers)
            if not result_pageNumbers:
                continue
            pageNumbers = result_pageNumbers[0]['page_numbers']

            dirName = (row['dest']).split('/')[-1]
            outDirName = os.path.join(outputPath, os.path.join(fileName,dirName))
            if not os.path.exists(outDirName):
                os.makedirs(outDirName)

            # print('下载：'+row['dest'])
            print('下载：'+row['dest'])
            for page in range(1, int(pageNumbers) + 1):
                paragraphFileName = fileName + '_p' + str(page) + type
                url = self.baseUrl + row['dest'].replace(self.bashPath, '') + '/' + paragraphFileName
                outFilePath = os.path.join(outDirName, paragraphFileName)
                self.downloadFile(url, outFilePath)
        return outputPath

    def getTaskFile(self,taskName,name,outputPath,type,limit):
        sql = """select doc_id,dest from tb_task where status = '完成' and taskname = '"""+name+"""' limit """+str(limit)
        result = self.queryTask(sql)
        for row in result:
            docId = row['doc_id']
            fileName = (row['dest']).split('/')[-2]
            if self.checkDocId(docId,taskName,fileName):
                continue
            dirName = (row['dest']).split('/')[-1]
            outDirName = os.path.join(outputPath, os.path.join(fileName, dirName))
            if not os.path.exists(outDirName):
                os.makedirs(outDirName)
            url = self.baseUrl + row['dest'].replace(self.bashPath, '') + '/' + fileName + type
            outFilePath = os.path.join(outDirName, fileName + type)
            print('下载：'+url)
            self.downloadFile(url, outFilePath)

    def checkDocId(self,docId,taskName,fileNmae):
        already_download_files = '../../data/unsupervised_data/already_download.json'
        ad_dict = {}
        ad_list_docId = []
        df = docId+":"+fileNmae
        if not os.path.exists(already_download_files):
            ad_list_docId.append(df)
            ad_dict[taskName] = ad_list_docId
            with open(already_download_files, 'w', encoding='utf-8') as fw:
                json.dump(ad_dict, fw, ensure_ascii=False, indent=4)  # 操作文件
        else:
            with open(already_download_files, "r", encoding='utf-8') as f:
                ad_dict = json.load(f)
            if taskName in ad_dict:
                ad_list_docId = ad_dict[taskName]
                if df in ad_list_docId:
                    print('{}:{}已经存在，跳过下载'.format(taskName,df))
                    return True
                else:
                    ad_list_docId.append(df)
                    ad_dict[taskName] = ad_list_docId
                    with open(already_download_files, 'w', encoding='utf-8') as fw:
                        json.dump(ad_dict, fw, ensure_ascii=False, indent=4)  # 操作文件
                    return False
            else:
                ad_list_docId.append(df)
                ad_dict[taskName] = ad_list_docId
                with open(already_download_files, 'w', encoding='utf-8') as fw:
                    json.dump(ad_dict, fw, ensure_ascii=False, indent=4)  # 操作文件
                return False

    def downloadFile(self,url,fileName):
        response = requests.get(url)
        response.status_code
        with open(fileName, "wb") as code:
            code.write(response.content)

if __name__ == '__main__':
    d = DownLoad()
    d.downloadTask('pdf2txt','../../data/unsupervised_data/',1)