import json
import os
import platform

import logging
import requests

from common.database.mysql_utils import MyPymysqlPool


class DownLoad():
    def __init__(self):
        self.logger = logging.getLogger('root.'+self.__class__.__name__)
        self.baseUrl = 'http://tfstatic.hipland.net/'
        self.bashPath = '/home/pubdisk/'
        self.urls_true = set()
        self.urls_false = set()

    def queryTask(self,sql):
        result = self.mp.getAll(sql)
        return result

    def downloadTask(self,outputPath,doc_id,need_download,conf_name):
        if need_download == 'yes':
            outputFile = self.checkFile(doc_id)
            if outputFile:            #存储文件不存在返回False，存储文件存在且已经下载则返回文件
                return outputFile
        self.mp = MyPymysqlPool.instance(conf_path=r"../conf/mysql1.ini",conf_name=conf_name)

        result = self.getTaskFilefc(outputPath,'_tree.json',doc_id,need_download)
        return result

    #从爬虫表里面查询
    def getTaskFilefc(self,outputPath,type,doc_id,need_download):
        sql = """select file_path from tb_crawler_result where id = '"""+str(doc_id)+"'"
        result = self.queryTask(sql)
        if not result:            #在正常生产阶段，result应该都有返回值
            self.logger.error('查询tb_crawler_result 无返回值')
            return  False
        for row in result:
            filePath = row['file_path']
            fileName = os.path.split(filePath)[1].split('.')[0]
            dirName = 'tree'
            treePath = os.path.splitext(filePath)[0]+'/tree'+'/'+fileName+type
            treePath = treePath.replace('bhpdf','ahpdf1')
            outDirName = os.path.join(outputPath, os.path.join(fileName, dirName))
            outFilePath = os.path.join(outDirName, fileName + type)

            url = self.baseUrl + treePath.replace(self.bashPath, '')
            if need_download == 'no':
                linux_treePath = os.path.join(self.bashPath,treePath)
                if not os.path.exists(linux_treePath):
                    self.logger.info(linux_treePath+'不存在')
                    return False
                else:
                    return linux_treePath

            if url in self.urls_true:
                return outFilePath
            elif url in self.urls_false:
                return False
            self.logger.info('下载：'+url)
            status_code = self.downloadFile(url, outFilePath)
            if status_code==200:
                self.logger.info('下载成功')
                self.urls_true.add(url)  #请求成功的url存入，避免重复请求
                self.storeMessage(doc_id,'tree',outFilePath)
                return outFilePath
            else:
                self.urls_false.add(url)
                self.logger.info('下载失败:{}'.format(url))
                return False
        self.mp.dispose()

    #检查状态文件是否存在，检查文件是否下载，可保存下载文件的信息同时可避免重复下载
    def checkFile(self,doc_id):
        already_download_files = '../data/already_download.json'
        if not os.path.exists(already_download_files):
            self.logger.info('存储文件{}不存在'.format(already_download_files))
            return False
        else:
            with open(already_download_files, "r", encoding='utf-8') as f:
                ad_dict = json.load(f)
            if 'tree' in ad_dict:
                ad_list_docId = ad_dict['tree']
                for i in ad_list_docId:
                    if i[0] == doc_id:
                        print('({},{})已经存在，跳过下载'.format('tree', i))
                        return i[1]             #返回已经下载过的文件路径
            else:
                return False

    def storeMessage(self,docId,taskName,outFilePath = None):
        """
        :param docId:
        :param taskName:
        :param outFilePath:
        :return:
        1.存储下载的文件信息

        """
        already_download_files = '../data/already_download.json'
        ad_dict = {}
        ad_list_docId = []
        df = (docId,outFilePath)
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
                ad_list_docId.append(df)
                ad_dict[taskName] = ad_list_docId
                with open(already_download_files, 'w', encoding='utf-8') as fw:
                    print('写入==============='+str(ad_dict))
                    json.dump(ad_dict, fw, ensure_ascii=False, indent=4)  # 操作文件
            else:
                ad_list_docId.append(df)
                ad_dict[taskName] = ad_list_docId
                with open(already_download_files, 'w', encoding='utf-8') as fw:
                    json.dump(ad_dict, fw, ensure_ascii=False, indent=4)  # 操作文件

    def downloadFile(self,url,fileName):
        # 设置重连次数
        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        # 设置连接活跃状态为False
        s.keep_alive = False
        response = requests.get(url)
        status_code = response.status_code
        if status_code==200:
            outDirName = os.path.split(fileName)[0]
            if not os.path.exists(outDirName):
                os.makedirs(outDirName)
            with open(fileName, "wb") as code:
                code.write(response.content)
        # 关闭请求  释放内存
        response.close()
        del (response)
        return status_code

if __name__ == '__main__':
    d = DownLoad()
    d.downloadTask('..\data',3910,'yes','MysqlDev')