# coding=UTF-8
import time
def caltime(func):
    def wrapper(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        endTime = time.time()
        secs = endTime - startTime
        print("耗时 %d s" %secs)
    return wrapper