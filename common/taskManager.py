import json

import requests


class TaskManager():
    taskid = None
    error_count = 0

    @staticmethod
    def setId(id):
        TaskManager.taskid = id

    @staticmethod
    def addTask(mq_message,jobId,docId,type,taskName,stockCode,file_path,output_path):
        addTask_dict = {}
        TaskManager.error_count = 0
        addTask_dict['status'] = '执行中'
        addTask_dict['request'] = mq_message
        addTask_dict['jobPid'] = jobId
        addTask_dict['docId'] = docId
        addTask_dict['type'] = type
        addTask_dict['taskname'] = taskName
        addTask_dict['progress'] = 0
        addTask_dict['stockCode'] = stockCode
        addTask_dict['source'] = file_path
        addTask_dict['dest'] = output_path

        # 调用java restful接口，存储消息
        url = 'http://tfapi.hipland.net/jobmanage/taskService/addTask'
        body = json.dumps(addTask_dict)
        headers = {'content-type': "application/json"}
        response = requests.post(url, data=body, headers=headers)
        status_code = response.status_code
        if status_code == 200:
            result = response.text
            result_dict = json.loads(result)
            id = result_dict['data']['task']['id']
            return id



    @staticmethod
    def updateTask(status,response,progress,id = None):
        if status == '异常':
            TaskManager.error_count += 1
            if not TaskManager.error_count == 1 :#保证只有1次异常情况更新
                return 'error has been updated'
        updateTask_dict = {}
        if id:
            updateTask_dict['id'] = id
        else:
            updateTask_dict['id'] = TaskManager.taskid
        updateTask_dict['status'] = status
        updateTask_dict['response'] = response
        updateTask_dict['progress'] = progress

        # 调用java restful接口，更新消息
        url = 'http://tfapi.hipland.net/jobmanage/taskService/updateTask'
        body = json.dumps(updateTask_dict)
        headers = {'content-type': "application/json"}
        response = requests.post(url, data=body, headers=headers)
        status_code = response.status_code
        if status_code == 200:
            pass

    @staticmethod
    def updateData(data_dict,id = None):
        if id:
            data_dict['id'] = id
        else:
            data_dict['id'] = TaskManager.taskid
        url = 'http://tfapi.hipland.net/jobmanage/taskService/updateTask'
        body = json.dumps(data_dict)
        headers = {'content-type': "application/json"}
        response = requests.post(url, data=body, headers=headers)
        status_code = response.status_code
        if status_code == 200:
            pass