# coding=UTF-8
import os

from common.rabbitmq.messageconsumer import MessageConsumer


def execute_engine(obj,args):
    print("进程execute_engine开始执行>>> pid={},className={}".format(os.getpid(), 'execute_engine'))
    import argparse
    P = argparse.ArgumentParser(description=__doc__)
    #consumer配置参数
    P.add_argument("-cqn", "--consumer_queue_name", type=str, default="",help="consumer_queue_name")
    P.add_argument("-cqd", "--consumer_queue_durable", default=True, action="store_true", help="consumer_queue_durable")
    P.add_argument("-cqno", "--consumer_queue_noack", default=False, action="store_true", help="consumer_queue_noack")
    P.add_argument("-cbrk", "--consumer_bind_routing_key",type=str,default="",help="consumer_bind_routing_key")
    P.add_argument("-cmch", "--consumer_mq_connection_host",type=str,default="59.111.104.10",help="consumer_mq_connection_host")
    P.add_argument("-cmcp", "--consumer_mq_connection_port",type=str,default="5672",help="consumer_mq_connection_port")
    P.add_argument("-cmu", "--consumer_mq_username",type=str,default="hdfs",help="consumer_mq_username")
    P.add_argument("-cmp", "--consumer_mq_password",type=str,default="hdfs",help="consumer_mq_password")
    P.add_argument("-cen", "--consumer_exchange_name",type=str,default="",help="consumer_exchange_name")
    # P.add_argument("-cen", "--consumer_exchange_name",type=str,required = True,help="consumer_exchange_name")
    P.add_argument("-cet", "--consumer_exchange_type",type=str,default = 'direct',help="consumer_exchange_type")
    P.add_argument("-ced", "--consumer_exhcange_durable", default=True, action="store_true", help="consumer_exhcange_durable")
    #producer配置参数
    P.add_argument("-pqn", "--producer_queue_name", type=str,default="", help="producer_queue_name")
    P.add_argument("-pqd", "--producer_queue_durable", default=True, action="store_true", help="producer_queue_durable")
    P.add_argument("-pbrk", "--producer_bind_routing_key",type=str,default="",help="producer_bind_routing_key")
    P.add_argument("-pmch", "--producer_mq_connection_host",type=str,default="59.111.104.10",help="producer_mq_connection_host")
    P.add_argument("-pmcp", "--producer_mq_connection_port",type=str,default="5672",help="producer_mq_connection_port")
    P.add_argument("-pmu", "--producer_mq_username",type=str,default="hdfs",help="producer_mq_username")
    P.add_argument("-pmp", "--producer_mq_password",type=str,default="hdfs",help="producer_mq_password")
    P.add_argument("-pen", "--producer_exchange_name",type=str,default="",help="producer_exchange_name")
    P.add_argument("-pet", "--producer_exchange_type",type=str,default = 'direct',help="producer_exchange_type")
    P.add_argument("-ped", "--producer_exhcange_durable", default=True, action="store_true", help="producer_exhcange_durable")
    P.add_argument("-mf", "--message_from", type=str, help="message_from")
    P.add_argument("-selfName", "--selfName", type=str, help="message_to")
    #obj参数设置
    P.add_argument("-jobId", "--jobId", type=str, default = '00000', help="jobId")
    P.add_argument("-taskName", "--taskName", type=str, default = '00000', help="taskName")
    P.add_argument("-basePath", "--basePath", type=str, help="basePath")
    P.add_argument("-env", "--env", type=str, help="env")
    P.add_argument("-load_db_env", "--load_db_env", type=str, help="load_db_env")
    P.add_argument("-change", "--change", type=str, help="change")
    P.add_argument("-need_download", "--need_download", type=str, help="need_download")
    P.add_argument("-threshold", "--threshold", type=str, help="threshold")
    P.add_argument("-model_path", "--model_path", type=str, help="model_path")
    P.add_argument("-run_type", "--run_type", type=str, help="type")
    P.add_argument("-new_trainData", "--new_trainData", type=str, help="new_trainData")
    P.add_argument("-user_id", "--user_id", type=str, help="user_id")

    conf_consumer = {}
    conf_producer = {}
    params = P.parse_args(args=args)
    params_dict = params.__dict__
    mf = params_dict['message_from']
    selfName = params_dict['selfName']

    obj.jobId = params_dict['jobId']
    obj.basePath = params_dict['basePath']
    obj.taskName = params_dict['taskName']

    obj_params = obj.getObj_params()
    obj_params.env = params_dict['env']
    obj_params.load_db_env = params_dict['load_db_env']
    obj_params.change = params_dict['change']
    obj_params.need_download = params_dict['need_download']
    obj_params.threshold = params_dict['threshold']
    obj_params.model_path = params_dict['model_path']
    obj_params.run_type = params_dict['run_type']
    obj_params.new_trainData = params_dict['new_trainData']
    obj_params.user_id = params_dict['user_id']

    for name in params_dict:
        if name.startswith('consumer'):
            conf_consumer[name[9:]] = params_dict[name]
            conf_consumer['exchange_name'] = mf+'.ex'
            conf_consumer['bind_routing_key'] = mf+'.brk'
            conf_consumer['queue_name'] = selfName+'.qn'
        if name.startswith('producer'):
            conf_producer[name[9:]] = params_dict[name]
            conf_producer['exchange_name'] = selfName+'.ex'
            conf_producer['bind_routing_key'] = selfName+'.brk'
            # conf_producer['queue_name'] = selfName+'.qn'

    mc = MessageConsumer(conf_consumer,conf_producer)
    mc.reciveObject(obj).consume()