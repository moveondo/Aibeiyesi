# coding=UTF-8
import yaml
import logging.config
import os

def setup_logging(fileName = 'Demo',default_path = "../conf/log.yaml",default_level = logging.INFO,env_key = "LOG_CFG"):
    if not os.path.exists('../log/'):
        os.makedirs('../log/')
    path = default_path
    value = os.getenv(env_key,None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path,"r") as f:
            config = yaml.load(f)
            config['handlers']['file_handler']['filename'] = fileName
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(level = default_level)

