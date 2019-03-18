#encoding:utf-8
import logging
import pika
import time
import configparser
from sys import argv

from common.taskManager import TaskManager


class MessageProducer:
    def __init__(self,conf_producer,hasQueue = False):
        self.logger = logging.getLogger('root.MessageProducer')
        self.conf_producer = conf_producer
        self.username = self.conf_producer['mq_username']   #指定远程rabbitmq的用户名密码
        self.pwd = self.conf_producer['mq_password']
        self.host = self.conf_producer['mq_connection_host']
        self.port = self.conf_producer['mq_connection_port']
        self.__setChannel(hasQueue)

    def __setChannel(self,hasQueue):
        user_pwd = pika.PlainCredentials(self.username, self.pwd)
        self.s_conn = pika.BlockingConnection(pika.ConnectionParameters(self.host,self.port,credentials=user_pwd))#创建连接
        self.chan = self.s_conn.channel()  #在连接上创建一个频道
        self.chan.exchange_declare(self.conf_producer['exchange_name'],#声明一个交换机
                                   self.conf_producer['exchange_type'],durable=self.conf_producer['exhcange_durable'])
        if hasQueue:
            self.chan.queue_declare(queue=self.conf_producer['queue_name'],durable=self.conf_producer['queue_durable']) #声明一个队列，生产者和消费者都要声明一个相同的队列，用来防止万一某一方挂了，另一方能正常运行

            self.chan.queue_bind(queue=self.conf_producer['queue_name'],exchange=self.conf_producer['exchange_name'],
                                 routing_key=self.conf_producer['bind_routing_key'])


    def produce(self,message):
        self.chan.basic_publish(exchange=self.conf_producer['exchange_name'],  #交换机
                           routing_key=self.conf_producer['bind_routing_key'],#路由键，写明将消息发往哪个队列
                           properties=pika.BasicProperties(
                               delivery_mode=2,  # make message persistent
                           ),
                           body=message)#生产者要发送的消息
        self.logger.info("[生产者] send:"+message+'\n')
        print("[生产者] send:",message+'\n')
        time.sleep(1)

    def close(self):
        self.s_conn.close()#当生产者发送完消息后，可选择关闭连接
