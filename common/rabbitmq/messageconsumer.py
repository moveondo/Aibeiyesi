#encoding:utf-8
import logging
import os
import threading
import traceback

import pika
import time

from common.rabbitmq.messageproudcer import MessageProducer
from common.taskManager import TaskManager


class MessageConsumer():

    def __init__(self,conf_consumer,conf_producer):
        self.logger = logging.getLogger('console.MessageConsumer')
        self.conf_consumer = conf_consumer
        self.conf_producer = conf_producer
        self.username = conf_consumer['mq_username']   #指定远程rabbitmq的用户名密码
        self.pwd = conf_consumer['mq_password']
        self.host = conf_consumer['mq_connection_host']
        self.port = conf_consumer['mq_connection_port']
        self.producer = None
        self.__setChannel()

    def __setChannel(self):
        user_pwd = pika.PlainCredentials(self.username, self.pwd)
        self.s_conn = pika.BlockingConnection(pika.ConnectionParameters(self.host,self.port,credentials=user_pwd))#创建连接
        self.chan = self.s_conn.channel()#在连接上创建一个频道
        self.chan.exchange_declare(self.conf_consumer['exchange_name'],#声明一个交换机
                              self.conf_consumer['exchange_type'],durable=self.conf_consumer['exhcange_durable'])
        self.chan.queue_declare(queue=self.conf_consumer['queue_name'],durable=self.conf_consumer['queue_durable'])#声明一个队列，生产者和消费者都要声明一个相同的队列，用来防止万一某一方挂了，另一方能正常运行
        self.chan.queue_bind(queue=self.conf_consumer['queue_name'],exchange=self.conf_consumer['exchange_name'],
                             routing_key=self.conf_consumer['bind_routing_key'])

    def sendDeadMessage(self,deadMessage):
        self.dead_conf = self.conf_producer.copy()
        self.dead_conf['exchange_name'] = 'dead.'+str(self.conf_consumer['queue_name']).split('.')[0]+'.ex'
        self.dead_conf['queue_name'] = 'dead.'+self.conf_consumer['queue_name']
        self.dead_conf['bind_routing_key'] = 'dead.'+str(self.conf_consumer['queue_name']).split('.')[0]+'.brk'
        self.producer = MessageProducer(self.dead_conf,True)
        self.produce(deadMessage)


    def callback(self,ch,method,properties,body): #定义一个回调函数，用来接收生产者发送的消息
        self.logger.info("[消费者] recv %s" % body.decode('utf-8'))
        print("[消费者] recv %s" % body.decode('utf-8'))
        message_consumer_json = body.decode('utf-8')
        message_thread = threading.Thread(target=self.process_message, args=(message_consumer_json,ch,method,))
        message_thread.start()
        while message_thread.is_alive():
            time.sleep(10)
            self.s_conn.process_data_events()
            # logger.info("waiting for message thread...")
        self.logger.info("message thread done")

    def process_message(self,message,ch,method):
        try:
            self.obj.receiveMessage(message)
            message_producer_json,close = self.obj.process()
            if message_producer_json:
                self.producer = MessageProducer(self.conf_producer)
                self.produce(message_producer_json)
                self.producer.close()
                ch.basic_ack(delivery_tag=method.delivery_tag)
                if close:
                    # 训练好模型后关闭进程
                    print('关闭进程')
                    pid = os.getpid()
                    os.system('kill -9 ' + str(pid))
            else:
                raise Exception('message_producer_json为空')
        except Exception as e:
            traceback.print_exc()
            self.logger.error(traceback.format_exc())
            self.logger.error('收到出现异常的消息,放入:'+'dead.'+str(self.conf_consumer['queue_name']))
            self.sendDeadMessage(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            TaskManager.updateTask('异常',str(e),0)

    def consume(self):
        self.chan.basic_consume(self.callback,  #调用回调函数，从队列里取消息
                           queue=self.conf_consumer['queue_name'],#指定取消息的队列名
                           no_ack=self.conf_consumer['queue_noack']) #取完一条消息后，是否给生产者发送确认消息，False是手动应答
        print('[消费者] waiting for msg .')
        self.logger.info("[消费者] waiting for msg .")
        self.chan.start_consuming()#开始循环取消息

    def str_to_bool(self,str):
        return True if str.lower() == 'true' else False

    def reciveObject(self,object):
        self.obj = object
        return self

    def produce(self,message):
        self.producer.produce(message)


