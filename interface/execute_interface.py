# coding=UTF-8
from abc import abstractmethod, ABCMeta, abstractclassmethod


class ExecuteInterface(metaclass=ABCMeta):  # 抽象类/接口类

    #从消费者接受消息
    @abstractclassmethod
    def receiveMessage(self, message):pass

    #返回需要值给mq生产者发送
    @abstractclassmethod
    def process(self):pass