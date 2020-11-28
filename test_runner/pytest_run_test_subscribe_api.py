# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/26
# @Software: PyCharm


import sys
import os
import time
import shutil
import glob
from datetime import datetime

import pytest

from test_config import *


def get_time_stamp(timestamp):
    ct = timestamp
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp


def run_firstPhase_test():
    testcase_file = SETUP_DIR + "/testcase/ws_testcase/first_phase/test_subscribe_api.py"
    print(testcase_file)
    log_file = SETUP_DIR + "\\common\\test_log\\MarkerTest_Error.log"

    # if os.path.exists(log_file):
    #     os.remove(log_file)

    start = time.time()
    pytest.main([
                 "-v",
                 testcase_file,
                 # "--reruns=3",                                  # 失败重跑3次
                 # "-k test_SubscribeKLineMsgReqApi_009",       # -k, 模糊匹配testcase
                 # "-m=allStock",
                 "--show-capture=stderr",     # 测试失败后, 只输出stderr信息, 减少内存
                 "-n 60",  # 分布式运行用例, -n 进程数
                 "--alluredir",  # allure报告
                 allure_result_folder,  # allure报告XML文件目录
                 "--clean-alluredir",  # 每次执行清空上次执行的allure缓存
                 "--disable-warnings"
                 ])

    # allure报告不超过5个
    allure_report = glob.glob(allure_report_folder + "*")
    if allure_report.__len__() > 10:
        shutil.rmtree(allure_report[0])

    html_report_path = allure_report_folder + "time_{}".format(time.strftime("%Y%m%d%H%M%S", time.localtime(start)))
    # 生成allure html测试报告
    os.popen("allure generate {xml_report_path} -o {html_report_path} --clean".format(
        xml_report_path=allure_result_folder, html_report_path=html_report_path)).read()

    end = time.time()
    print(u"测试完成!!! \n本次测试开始时间 : {}, \n结束时间 : {}, \n总耗时 : {}".format(
        get_time_stamp(start), get_time_stamp(end), end - start))




def run_secondPhase_test():
    testcase_file = SETUP_DIR + "/testcase/ws_testcase/second_phase/test_stock_subscribe_api.py"
    print(testcase_file)
    log_file = SETUP_DIR + "\\common\\test_log\\MarkerTest_Error.log"
    # if os.path.exists(log_file):
    #     os.remove(log_file)
    

    start = time.time()
    pytest.main([
                 "-v",
                 testcase_file,
                 # "--reruns=3",                                  # 失败重跑3次
                 "-k test_stock_QueryExchangeSortMsgReq_003",       # -k, 模糊匹配testcase
                 # "-m=allStock",
                 "--show-capture=stderr",     # 测试失败后, 只输出stderr信息, 减少内存
                 "-n 20",  # 分布式运行用例, -n 进程数
                 "--alluredir",  # allure报告
                 allure_result_folder,  # allure报告XML文件目录
                 "--clean-alluredir",  # 每次执行清空上次执行的allure缓存
                 "--disable-warnings"   # 不显示pytest警告
                 ])

    # allure报告不超过5个
    allure_report = glob.glob(allure_report_folder + "*")
    if allure_report.__len__() >= 10:
        shutil.rmtree(allure_report[0])

    html_report_path = allure_report_folder + "time_{}".format(time.strftime("%Y%m%d%H%M%S", time.localtime(start)))
    # 生成allure html测试报告
    os.popen("allure generate {xml_report_path} -o {html_report_path} --clean".format(
        xml_report_path=allure_result_folder, html_report_path=html_report_path)).read()

    end = time.time()
    print(u"测试完成!!! \n本次测试开始时间 : {}, \n结束时间 : {}, \n总耗时 : {}".format(
        get_time_stamp(start), get_time_stamp(end), end - start))


if __name__ == '__main__':
    # run_firstPhase_test()
    # time.sleep(60 * 60 * 4)
    run_secondPhase_test()

# @pytest.mark.testAPI : 运行所有API, 校验API是否可用
# @pytest.mark.allStock : 遍历所有类型股票
# @pytest.mark.Grey : 暗盘
# @pytest.mark.subBeforeData : 订阅返回的前数据, 休市时查询