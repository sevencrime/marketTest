# -*- coding:utf-8 -*-
# @Filename : ed_log.py
# @Author : Lizi
# @Time : 2020/5/9 13:33 
# @Software: PyCharm

import sys
import logging
import logging.config

from common.test_log import SafeFileHandler
from test_config import *

global test_logger
test_logger = None

# 普通配置文件方法
def get_log(loggerName=None):
    global test_logger
    if test_logger and not loggerName:
        return test_logger
    logFileFolder = SETUP_DIR + "/common/test_log/log_file/"
    if not os.path.exists(logFileFolder):
        os.makedirs(logFileFolder)

    logging.log_file = logFileFolder + "MarkerTest.log"  # 设置log文件输出地址
    logging.err_file = logFileFolder + "MarkerTest_Error.log"  # 设置log文件输出地址
    logging.TimerTask = logFileFolder + "TimerTask.log"  # 设置log文件输出地址

    logging.Safe = SETUP_DIR + "/common/test_log/Safe.log"  # 设置log文件输出地址
    if sys.platform == 'win32':
        logging.config.fileConfig(log_path + 'windows_logging.conf')
    else:
        logging.config.fileConfig(log_path + 'linux_logging.conf')

    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("http_request").setLevel(logging.WARNING)
    if loggerName:
        test_logger = logging.getLogger(loggerName)
    else:
        test_logger = logging.getLogger('getlog')       # 默认使用getlog

    return test_logger


    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format='%(asctime)s %(name)s %(levelname)-8s  %(message)s',
    #     datefmt='(%H:%M:%S)')
    #
    # logging.getLogger("websockets").setLevel(logging.DEBUG)
    #
    # logging.getLogger('asyncio').setLevel(logging.DEBUG)
    # logging.getLogger('asyncio.coroutines').setLevel(logging.DEBUG)
    # logging.getLogger('websockets.server').setLevel(logging.DEBUG)
    # logging.getLogger('websockets.protocol').setLevel(logging.DEBUG)
    # logging.getLogger("requests").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("http_request").setLevel(logging.WARNING)
    #
    # test_logger = logging.getLogger()
    # return test_logger



if __name__ == '__main__':
    log = get_log()
    log = get_log("timerTask")
    # log.debug("sss")
    # log.error("222")
    log.debug(111)
    log.debug(b"x86")
