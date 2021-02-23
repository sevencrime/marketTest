# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/6/2
# @Software: PyCharm

import sys
import os
import unittest
import datetime
import math

import pytest
import allure
from parameterized import parameterized, param

from pb_files.common_type_def_pb2 import *
# from websocket_py3.ws_api.subscribe_api_for_first_phase import *
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from testcase.zmq_testcase.zmq_record_testcase import CheckZMQ
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from common.basic_info import *


def appFuturesCode(isKLine=False, isHKFE=False):
    # 返回所有品种列表, isKLine=True时, 返回所有品种的不同K线频率列表
    appFutures = []

    appFutures += [[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)]
    if not isHKFE:
        appFutures += [[NYMEX_exchange, eval("NYMEX_code{}".format(n + 1))] for n in range(4)]
        appFutures += [[COMEX_exchange, eval("COMEX_code{}".format(n + 1))] for n in range(6)]
        appFutures += [[CBOT_exchange, eval("CBOT_code{}".format(n + 1))] for n in range(10)]
        appFutures += [[CME_exchange, eval("CME_code{}".format(n + 1))] for n in range(14)]
        appFutures += [[SGX_exchange, eval("SGX_code{}".format(n + 1))] for n in range(3)]

    KLinePeriod = [
        ["MINUTE"],
        ["THREE_MIN"],
        ["FIVE_MIN"],
        ["FIFTEEN_MIN"],
        ["THIRTY_MIN"],
        ["HOUR"],
        ["TWO_HOUR"],
        ["FOUR_HOUR"],
        ["DAY"],
        ["WEEK"],
        ["MONTH"],
        ["SEASON"],
        ["YEAR"],
    ]

    paramlist = []
    if isKLine:     # K线所有频率
        for fu in appFutures:
            for KLine in KLinePeriod:
                paramlist.append(tuple(fu + KLine))
    else:
        paramlist = [tuple(f) for f in appFutures]

    return paramlist


class Test_Subscribe(unittest.TestCase):

    # def __init__(self, methodName='runTest'):
    #     super().__init__(methodName)

    @classmethod
    def setUpClass(cls):
        cls.logger = get_log()
        cls.common = Common()
        # cls.http = MarketHttpClient()
        # cls.market_token = cls.http.get_market_token(
        #     cls.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

        cls.market_token = None

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.new_loop = self.common.getNewLoop()
        asyncio.set_event_loop(self.new_loop)
        self.api = SubscribeApi(union_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())

    def tearDown(self):
        asyncio.set_event_loop(self.new_loop)
        self.api.client.disconnect()

    def inner_zmq_test_case(self, case_name, check_json_list, is_before_data=False, start_sub_time=None,
                            start_time=None, exchange=None, instr_code=None, peroid_type=None):
        suite = unittest.TestSuite()
        suite.addTest(CheckZMQ(case_name))
        suite._tests[0].check_json_list = check_json_list
        suite._tests[0].is_before_data = is_before_data
        suite._tests[0].sub_time = start_sub_time
        suite._tests[0].start_time = start_time
        suite._tests[0].exchange = exchange
        suite._tests[0].instr_code = instr_code
        suite._tests[0].peroid_type = peroid_type
        runner = unittest.TextTestRunner()
        inner_test_result = runner.run(suite)
        if inner_test_result.failures or inner_test_result.errors:
            self.logger.error("###### ZMQ 报错 ###########")
            if inner_test_result.failures:
                for fail in inner_test_result.failures[0]:
                    self.logger.error(fail)
            
            if inner_test_result.errors:
                for err in inner_test_result.errors[0]:
                    self.logger.error(err)
                
            self.logger.error("###########################")
        return inner_test_result

    # ------------------------------------------登录-----------------------------------------------------------
    def test_LoginReq01(self):
        """正常登陆"""
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))
        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq02(self):
        """错误code进行登陆"""
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token='errtoken', start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_FAILD))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq03(self):
        """等待token失效再登陆，登陆失败"""
        time.sleep(60 * 10 + 1)
        self.api = SubscribeApi(delay_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_FAILD))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq04(self):
        """等待token即将失效再登陆， 登陆成功"""
        time.sleep(60 * 10 - 1)
        self.api = SubscribeApi(delay_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))
        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq05(self):
        """异常登陆后请求行情数据，失败"""
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token='errtoken', start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_INVAILD))

        exchange = HK_exchange
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(rsp_list.__len__() == 0)

    #  ----------------------------------------退出---------------------------------------------------------
    def test_LogoutReq01(self):
        """登陆后退出"""
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LogoutReq02(self):
        """未登录时，退出登录"""
        start_time_stamp = int(time.time() * 1000)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'user is not login.')
        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LogoutReq03(self):
        """校验退出之后响应成功，且接不到订阅数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.get_event_loop().run_until_complete(future=self.api.SubsQutoMsgReqApi(
            sub_type=sub_type, child_type=None, base_info=base_info, start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp, recv_num=10))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_LogoutReq04(self):
        """退出登录后再次登录成功"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.get_event_loop().run_until_complete(future=self.api.SubsQutoMsgReqApi(
            sub_type=sub_type, child_type=None, base_info=base_info, start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp, recv_num=10))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.setUp()
        sec_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            sec_rsp[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))

    # ----------------------------------------心跳-----------------------------------------
    def test_HearbeatReqApi01(self):
        """登录成功后50秒内发送心跳"""
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token))
        time.sleep(3)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        # self.assertTrue(self.common.searchDicKV(
        #     first_rsp_list[0], 'connId') == '123')

    def test_HearbeatReqApi02(self):
        """登录成功后，在第一次心跳发送后的50秒内，发送第二次心跳"""
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token))
        time.sleep(49)
        first_rsp_list1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        # self.assertTrue(self.common.searchDicKV(
        #     first_rsp_list1[0], 'connId') == '123')
        time.sleep(49)
        first_rsp_list2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        # self.assertTrue(self.common.searchDicKV(
        #     first_rsp_list2[0], 'connId') == '123')

    # @unittest.skip('耗时较长，先跳过')
    def test_HearbeatReqApi03(self):
        """登录成功后超过50秒发送心跳"""
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token))
        time.sleep(51)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list.__len__() == 0)

    # @unittest.skip('耗时较长，先跳过')
    def test_HearbeatReqApi04(self):
        """登录成功后，在第一次心跳发送后的50秒外，发送第二次心跳"""
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token))
        time.sleep(49)
        first_rsp_list1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        # self.assertTrue(self.common.searchDicKV(
        #     first_rsp_list1[0], 'connId') == '123')
        time.sleep(51)
        first_rsp_list2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list2.__len__() == 0)

    # @unittest.skip('不测试')
    def test_HearbeatReqApi05(self):
        """未登录时发送心跳，则无响应"""
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list.__len__() == 0)

    # -------------------------------------------------------测速-------------------------------------------------------
    def test_VelocityReqApi01(self):
        start_time_stamp = int(time.time() * 1000)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.VelocityReqApi(start_time=start_time_stamp))

        self.assertTrue(int(self.common.searchDicKV(
            first_rsp_list[0], 'startTime')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'sendTime')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvTime')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTime')))

    # --------------------------------------------------订阅start-------------------------------------------------------

    # --------------------------------------------------订阅分时数据-------------------------------------------------------
    @pytest.mark.testAPI
    def test_SubscribeKlineMinReqApi_001(self):
        """分时订阅一个合约"""
        frequence = 100
        exchange = HK_exchange
        code = "MHImain"

        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_SubscribeKlineMinReqApi_002(self):
        """分时订阅2个合约"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅第一个合约')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'分时订阅第二个合约')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code1) or not self.common.check_trade_status(exchange, code2):
            self.assertTrue(info_list.__len__() == 0)
        else:
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'code'))

            self.assertTrue(set(recv_code_list) == {code1, code2})
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_SubscribeKlineMinReqApi_003(self):
        """分时订阅一个合约, code=xxxx"""
        frequence = 100
        exchange = HK_exchange
        code = 'xxxx'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKlineMinReqApi_004(self):
        """分时订阅一个合约, exchange='UNKNOWN'"""
        frequence = 100
        exchange = 'UNKNOWN'
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKlineMinReqApi_005(self):
        """分时订阅一个合约, code=TNmain"""
        frequence = 100
        exchange = HK_exchange
        code = 'TNmain'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKlineMinReqApi_006(self):
        """分时订阅一个合约, code=None"""
        frequence = 100
        exchange = HK_exchange
        code = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKlineMinReqApi_007(self):
        """分时订阅一个合约, exchange=None"""
        frequence = 100
        exchange = None
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_SubscribeKlineMinReqApi_008(self, exchange, code):
        """分时订阅 订阅所有合约, 包含港期外期"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        if not self.common.check_trade_status(exchange, code): 
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 200:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))

                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_SubscribeKlineMinReqApi_009(self):
        """分时订阅2个合约, 其中一个外期合约, 一个港期合约"""
        frequence = 100
        exchange = HK_exchange
        exchange2 = CBOT_exchange
        code1 = HK_code1
        code2 = CBOT_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅第一个合约')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'分时订阅第二个合约')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange2, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange2)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=300))
        if not self.common.check_trade_status(exchange, code1) or not self.common.check_trade_status(exchange2, code2):
            self.assertTrue(info_list.__len__() == 0)
        else:
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'code'))
            if self.common.check_trade_status(exchange, code1) and self.common.check_trade_status(exchange2,code2):
                self.assertTrue(set(recv_code_list) == {code1, code2})
            else:
                assert set(recv_code_list) == {code1} or set(recv_code_list) == {code2}

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_SubscribeKlineMinReqApi_010(self, exchange, code):
        """分时订阅一个合约"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)





    # --------------------------------------------------取消订阅分时数据-------------------------------------------------------
    @pytest.mark.testAPI
    def test_UnsubscribeKlineMinReqApi_001(self):
        """分时订阅一个合约,取消订阅"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            self.assertTrue(info_list.__len__() > 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKlineMinReqApi_002(self):
        """分时订阅2个合约,取消订阅其中一个"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'分时订阅，检查返回结果2')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅一个,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)

    def test_UnsubscribeKlineMinReqApi_003(self):
        """分时订阅2个合约,取消订阅2个"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'分时订阅，检查返回结果2')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'订阅两个分时数据后, 接收数据, 校验是否接收到两个合约的数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        push_code = [info.get("code") for info in info_list]
        self.assertTrue(set(push_code) == {code1, code2})

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅,并校验2')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKlineMinReqApi_004(self):
        """查询分时时顺便订阅了分时，再取消分时订阅"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = HK_code1
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKlineMinReqApi_005(self):
        """查询5日分时时顺便订阅了分时，再取消分时订阅"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = HK_code1
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKlineMinReqApi_006(self):
        """分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKlineMinReqApi_007(self):
        """分时订阅一个合约,取消订阅入参exchange=UNKNOWN"""
        frequence = 100
        exchange = HK_exchange
        exchange2 = 'UNKNOWN'
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKlineMinReqApi_008(self):
        """分时订阅一个合约,取消订阅一个不存在的合约"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = 'xxxx'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKlineMinReqApi_009(self):
        """分时订阅一个合约,取消订阅一个外期合约"""
        frequence = 100
        exchange = COMEX_exchange
        code = COMEX_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_UnsubscribeKlineMinReqApi_010(self, exchange, code):
        """分时订阅一个外期合约, 再取消订阅外期合约"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100, recv_timeout_sec=30))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            if info_list.__len__() == 0:
                _start = time.time()
                while time.time() - _start < 300:
                    pass
                    info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100, recv_timeout_sec=30))
                    if info_list:
                        break
                    self.logger.debug("循环内打印循环内打印, 已循环时间 : {}".format(time.time() - _start))
            self.assertTrue(info_list.__len__() > 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_UnsubscribeKlineMinReqApi_011(self, exchange, code):
        """分时订阅一个合约,取消订阅"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            self.assertTrue(info_list.__len__() > 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'取消订阅,并校验')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)



    # --------------------------------------------------K线订阅----------------------------------------------
    @pytest.mark.testAPI
    def test_SubscribeKLineMsgReqApi_001(self):
        """K线订阅-订阅单个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = "HKFE"
        code = "MHImain"
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))

    def test_SubscribeKLineMsgReqApi_002(self):
        """K线订阅-订阅两个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug("订阅第一个合约的K线数据")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug("订阅第二个合约的K线数据")
        start_time_stamp2 = int(time.time() * 1000)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp2))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp2)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))

        if not self.common.check_trade_status(exchange, code1):
            assert info_list.__len__() == 0
        else:
            self.logger.debug(u"校验接收的数据中包含两个合约的数据")
            codeinfo = [info.get("code") for info in info_list]
            self.assertTrue(set(codeinfo) == {code1, code2})
            self.assertTrue(exchange in [info.get("exchange")
                                         for info in info_list])
            self.assertTrue(KLinePeriodType.Name(peroid_type) in [info.get("peroidType") for info in info_list])
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_SubscribeKLineMsgReqApi_003(self):
        """K线订阅-订阅K线数据时, 使用错误的合约代码: code="xxx" peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code = "xxx"
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKLineMsgReqApi_004(self):
        """K线订阅-订阅K线数据时, 使用错误的交易所: exchange="UNKNOWN" peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = "UNKNOWN"
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKLineMsgReqApi_005(self):
        """
        K线订阅-交易所和合约代码不匹配
        {
            perodi_tyoe : "MINUTE",
            base_info : {
                exchange : "交易所",
                product_code : "品种代码"
            },
            start_time_stamp : now()
        }

        """
        frequence = 100
        exchange = HK_exchange
        code = "GCmain"
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([
        (KLinePeriodType.MINUTE,),
        (KLinePeriodType.THREE_MIN,),
        (KLinePeriodType.FIVE_MIN,),
        (KLinePeriodType.FIFTEEN_MIN,),
        (KLinePeriodType.THIRTY_MIN,),
        (KLinePeriodType.HOUR,),
        (KLinePeriodType.TWO_HOUR,),
        (KLinePeriodType.FOUR_HOUR,),
        (KLinePeriodType.DAY,),
        (KLinePeriodType.WEEK,),
        (KLinePeriodType.MONTH,),
        (KLinePeriodType.SEASON,),
        (KLinePeriodType.YEAR,)
    ])
    @pytest.mark.allStock
    def test_SubscribeKLineMsgReqApi_006(self, peroid_type):
        """
        K线订阅-订阅日K线数据, 遍历K线周期
        """
        self.logger.debug(
            "订阅K线数据 -- 订阅频率 : {}".format(KLinePeriodType.Name(peroid_type)))
        frequence = 100
        # exchange = HK_exchange
        # code = "MHImain"

        exchange = "CBOT"
        code = "ZTmain"

        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        # peroid_type = KLinePeriodType.DAY
        peroid_type = peroid_type
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=150))

        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(
                    info, 'peroidType') == KLinePeriodType.Name(peroid_type))

    def test_SubscribeKLineMsgReqApi_007(self):
        """
        K线订阅-订阅K线数据, K线周期定义为 UNKNOWN_PERIOD
        {
            perodi_tyoe : "ONE_SECONDS",
            base_info : {
                exchange : "交易所",
                code : "合约代码"
            },
            start_time_stamp : now()
        }

        """
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.UNKNOWN_PERIOD
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeKLineMsgReqApi_008(self):
        """
        K线订阅-订阅K线数据, code=None

        """
        frequence = 100
        exchange = HK_exchange
        code = None
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode(isKLine=True))
    @pytest.mark.allStock
    def test_SubscribeKLineMsgReqApi_009(self, exchange, code, peroidType):
        """K线订阅-订阅所有外期品种的K线"""
        frequence = 100
        exchange = exchange
        code = code
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = peroidType
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'接收K线数据')

        if not self.common.check_trade_status(exchange, code):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))

                if info_list.__len__() > 0:
                    break


            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_SubscribeKLineMsgReqApi_010(self, exchange, code):
        """K线订阅-订阅单个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = exchange
        code = code
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))



    # --------------------------------------------------取消K线订阅-------------------------------------------
    @pytest.mark.testAPI
    def test_UnsubscribeKLineMsgReqApi_001(self):
        """取消K线订阅-取消订阅单个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code = "MHImain"
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKLineMsgReqApi_002(self):
        """
        取消K线订阅-订阅两个合约的K线数据, 再取消订阅其中一个
        peroid_type = KLinePeriodType.MINUTE
        """
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u"订阅第一个合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"订阅第二个合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"取消订阅第一个合约的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u"接收k线数据")
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        if not self.common.check_trade_status(exchange, code1):
            assert info_list.__len__() == 0
        else:
            self.logger.debug(u"校验接收不到第一个合约的数据")
            self.assertTrue(info_list.__len__() > 0)
            self.assertTrue(set([info.get("code") for info in info_list]) == {code2})
            # 校验交易所
            self.assertTrue(exchange in [info.get("exchange") for info in info_list])
            # 校验频率
            self.assertTrue(KLinePeriodType.Name(peroid_type) in [info.get("peroidType") for info in info_list])
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_UnsubscribeKLineMsgReqApi_003(self):
        """
        取消K线订阅-订阅两个合约的K线数据, 再取消订阅两个合约
        peroid_type = KLinePeriodType.MINUTE
        """
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u"订阅第一个合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"订阅第二个合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"取消订阅第一个合约的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u"取消订阅第二个合约的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u"接收k线数据, 校验接收不到数据")
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKLineMsgReqApi_004(self):
        """取消K线订阅-取消订阅不存在的合约: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code6
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug("直接取消订阅")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKLineMsgReqApi_005(self):
        """
        取消K线订阅-取消订阅时, K线周期不一致
        """
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        un_peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug("取消订阅-K线周期不一致")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=un_peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKLineMsgReqApi_006(self):
        """
        取消K线订阅-取消订阅时, 交易所exchange=UNKNOWN
        """
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        base_info1 = [{'exchange': "UNKNOWN", 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        un_peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        self.logger.debug("订阅合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=un_peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKLineMsgReqApi_007(self):
        """
        取消K线订阅-订阅A合约后, 取消订阅B合约
        """
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code}]
        base_info1 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        un_peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        self.logger.debug("订阅合约")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=un_peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_UnsubscribeKLineMsgReqApi_008(self):
        """
        取消K线订阅-查询K线数据时顺便订阅K线数据, 订阅成功后再取消K线订阅
        """
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 60 * 1000
        end = start_time_stamp
        vol = None

        base_info = [{'exchange': exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询并订阅K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']

        # 查询K线回包校验
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        # 订阅回包校验
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(
            sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'订阅成功后接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug(u"取消K线订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 无法接收到K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_UnsubscribeKLineMsgReqApi_009(self, exchange, code):
        """取消外期合约的K线数据"""
        frequence = 100
        exchange = exchange
        code = code
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_UnsubscribeKLineMsgReqApi_010(self, exchange, code):
        """取消K线订阅-取消订阅单个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = exchange
        code = code
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(
            un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)



    # --------------------------------------------------订阅逐笔成交数据---------------------------------------
    @pytest.mark.testAPI
    def test_SubscribeTradeTickReqApi_001(self):
        """订阅一个合约的逐笔: frequence=None"""
        frequence = None
        exchange = HK_exchange
        code = "MHImain"
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_SubscribeTradeTickReqApi_002(self):
        """订阅一个合约的逐笔: frequence=4"""
        frequence = 4
        exchange = HK_exchange
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(
                    info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeTradeTickReqApi_003(self):
        """订阅2个合约的逐笔: frequence=100"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code3
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp, recv_num=50))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))
        if not self.common.check_trade_status(exchange, code1, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            recv_code_list = []
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                recv_code_list.append(self.common.searchDicKV(info, 'instrCode'))
            self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeTradeTickReqApi_004(self):
        """订阅一个合约的逐笔: frequence=100, exchange=UNKNOWN"""
        frequence = 100
        exchange = 'UNKNOWN'
        code = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeTradeTickReqApi_005(self):
        """订阅一个合约的逐笔: frequence=100, code=xxxx"""
        frequence = 100
        exchange = HK_exchange
        code = 'xxxx'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr code [{}] error'.format(code))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeTradeTickReqApi_006(self):
        """ 订阅两个合约的逐笔, 校验是否正确 """
        frequence = None
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个合约的逐笔数据')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'订阅第二个合约的逐笔数据')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code1, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange})
            # 接收到两个合约的逐笔
            self.assertTrue(set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2})

    def test_SubscribeTradeTickReqApi_007(self):
        """订阅一个合约的逐笔: frequence=100, exchange=UNKNOWN"""
        frequence = 100
        exchange = HK_exchange
        code = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_SubscribeTradeTickReqApi_008(self, exchange, code):
        """订阅外期合约的逐笔数据"""
        frequence = None
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_SubscribeTradeTickReqApi_009(self, exchange, code):
        """订阅一个合约的逐笔: frequence=None"""
        frequence = None
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)



    # --------------------------------------------------取消订阅逐笔成交数据-------------------------------------------------------
    @pytest.mark.testAPI
    def test_UnsubscribeTradeTickReqApi_001(self):
        """取消订阅一个合约的逐笔"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeTradeTickReqApi_002(self):
        """订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_UnsubscribeTradeTickReqApi_003(self):
        """订阅两个合约的逐笔，再取消2个的合约的逐笔"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeTradeTickReqApi_004(self):
        """通过逐笔成交查询一个合约且订阅其逐笔，通过取消逐笔订阅取消,取消成功"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 5 * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() > 0)

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeTradeTickReqApi_005(self):
        """订阅合约A的逐笔数据，取消订阅合约B的逐笔数据，取消失败"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(
        #     self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr [{}_{}] have no subscribe'.format(exchange, code2))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert self.info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_UnsubscribeTradeTickReqApi_006(self):
        """订阅合约A的逐笔数据，取消订阅不存在的合约B的逐笔数据，取消失败"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = "xxx"
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if not self.common.check_trade_status(exchange, code):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
            assert info_list.__len__() == 0
        else:
            start = time.time()
            while time.time() - start < 100:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_UnsubscribeTradeTickReqApi_007(self):
        """订阅合约A的逐笔数据，取消订阅 exchange传入UNKNOWN"""
        frequence = 100
        exchange = HK_exchange
        exchange2 = 'UNKNOWN'
        code = HK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'exchange type error')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        if not self.common.check_trade_status(exchange, code):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
            assert info_list.__len__() == 0
        else:
            start = time.time()
            while time.time() - start < 100:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break
            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_UnsubscribeTradeTickReqApi_008(self, exchange, code):
        """取消订阅所有外期的逐笔"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_UnsubscribeTradeTickReqApi_008(self, exchange, code):
        """取消订阅一个合约的逐笔"""
        frequence = 100
        exchange = exchange
        code = code
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    # --------------------------------------------------订阅手机图表数据(手机专用)-------------------------------
    @pytest.mark.testAPI
    def test_StartChartDataReq_001(self):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=4"""
        exchange = "HKFE"
        code = "HSImain"

        frequence = 4
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        before_orderbook_json_list = [app_rsp.get("orderbook")]  # 盘口
        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=200))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_StartChartDataReq_002(self):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=0(当成1处理)"""
        exchange = HK_exchange
        code = HK_code1
        frequence = 0
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求手机图表数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(self.common.searchDicKV(app_rsp, 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(app_rsp, 'code') == code)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_003(self):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=None"""
        exchange = HK_exchange
        code = HK_code1
        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(self.common.searchDicKV(
            app_rsp, 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(app_rsp, 'code') == code)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_004(self):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=100"""
        exchange = HK_exchange
        code = HK_code1
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(self.common.searchDicKV(
            app_rsp, 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(app_rsp, 'code') == code)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_005(self):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=100,再订阅第二个合约"""
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个合约')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code1)
        self.assertTrue(app_rsp['exchange'] == 'HKFE')

        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'订阅第二个合约')
        start_time_stamp = int(time.time() * 1000)
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code2, start_time_stamp, recv_num=100))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code2)
        self.assertTrue(app_rsp['exchange'] == 'HKFE')

        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值2')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

        self.logger.debug(u'校验前快照数据2')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)


        self.logger.debug(u'校验前盘口数据2')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)


        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code1, curTime) and not self.common.check_trade_status(exchange, code2, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'instrCode'))
            self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code1, curTime) and not self.common.check_trade_status(exchange, code2, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'instrCode'))
            self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_006(self):
        """exchange传入Unknown"""
        exchange = 'UNKNOWN'
        code = HK_code1
        frequence = 100
        start_time_stamp = int(time.time() * 1000 - 100000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(self.common.searchDicKV(app_rsp, 'code') == code)
        self.assertTrue('basicData' not in app_rsp.keys())
        self.assertTrue('snapshot' not in app_rsp.keys())
        self.assertTrue('orderbook' not in app_rsp.keys())

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_007(self):
        """不传code"""
        exchange = HK_exchange
        code = None
        frequence = 100
        start_time_stamp = int(time.time() * 1000 - 100000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ {} ] error'.format(exchange))
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(self.common.searchDicKV(
            app_rsp, 'exchange') == exchange)
        self.assertTrue('basicData' not in app_rsp.keys())
        self.assertTrue('snapshot' not in app_rsp.keys())
        self.assertTrue('orderbook' not in app_rsp.keys())

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartChartDataReq_008(self):
        """传错误code"""
        exchange = HK_exchange
        code = 'HHI2005'  # HHI2005已下架
        frequence = 100
        start_time_stamp = int(time.time() * 1000 - 100000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(self.common.searchDicKV(app_rsp, 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(app_rsp, 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue('basicData' not in app_rsp.keys())
        self.assertTrue('snapshot' not in app_rsp.keys())
        self.assertTrue('orderbook' not in app_rsp.keys())

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_StartChartDataReq_009(self, exchange, code):
        """订阅手机图表数据(手机专用)--遍历外期合约"""
        exchange = exchange
        code = code
        frequence = 4
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        before_orderbook_json_list = [app_rsp['orderbook']]  # 盘口

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        if not self.common.check_trade_status(exchange, code):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                # 持续接收数据, 防止不活跃合约
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
                if info_list:
                    break

            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("请求时间为 : {}".format(curTime))
        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
                if info_list:
                    break

            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_StartChartDataReq_010(self, exchange, code):
        """订阅手机图表数据(手机专用)--订阅一个合约，frequence=4"""
        exchange = exchange
        code = code

        frequence = 4
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        before_orderbook_json_list = [app_rsp.get("orderbook")]  # 盘口
        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=200))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    # --------------------------------------------------取消订阅手机图表数据(手机专用)-------------------------------
    @pytest.mark.testAPI
    def test_StopChartDataReqApi_001(self):
        """订阅一个手机图表数据,再取消订阅 """
        exchange = HK_exchange
        code = HK_code1
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_StopChartDataReqApi_002(self):
        """订阅2个合约,取消订阅其中一个 """
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')

        self.logger.debug("订阅第二个手机图表数据")
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅第一个手机图表数据')
        start_time_stamp = int(time.time() * 1000)
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code1)
        self.assertTrue(app_rsp['exchange'] == exchange)

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_StopChartDataReqApi_003(self):
        """订阅2个合约,再取消订阅两个"""
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')

        self.logger.debug(u"订阅第二个图表数据")
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')

        self.logger.debug(u'取消订阅第一个图表数据')
        start_time_stamp = int(time.time() * 1000)
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code1)
        self.assertTrue(app_rsp['exchange'] == 'HKFE')

        self.logger.debug(u"取消订阅第二个图表数据")
        start_time_stamp = int(time.time() * 1000)
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code2)
        self.assertTrue(app_rsp['exchange'] == 'HKFE')

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)


    def test_StopChartDataReqApi_004(self):
        """订阅一个合约的图表数据, 再取消订阅, 取消订阅时, exchange传入UNKNOWN"""
        exchange = HK_exchange
        exchange2 = 'UNKNOWN'
        code = HK_code1
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ {}_{} ] error'.format(exchange2, code))
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_StopChartDataReqApi_005(self):
        """订阅一个合约的图表数据, 再取消订阅, 取消订阅时,exchange传入None"""
        exchange = HK_exchange
        exchange2 = None
        code = HK_code1
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅图表数据, 并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ UNKNOWN_{} ] error'.format(code))
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_StopChartDataReqApi_006(self):
        """订阅一个合约的图表数据, 再取消订阅, 取消订阅时, code传入'xxx' """
        exchange = HK_exchange
        code = HK_code1
        code2 = 'xxxx'
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        start_time = int(time.time() * 1000 - 5 * 60 * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅一个图表数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅分时页面数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code2))
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code2)
        self.assertTrue(app_rsp['exchange'] == 'HKFE')

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_StopChartDataReqApi_007(self):
        """订阅一个合约的图表数据, 再取消订阅, 取消订阅时, code传入None """
        exchange = HK_exchange
        code = HK_code1
        code2 = None
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        start_time = int(time.time() * 1000 - 5 * 60 * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅图表数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅分时页面数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(app_rsp, 'retMsg') == 'instr have no start')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp.get("code") == code2)
        self.assertTrue(app_rsp.get("exchange") == exchange)

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_StopChartDataReqApi_009(self, exchange, code):
        """取消订阅外期的手机图表数据 """
        exchange = exchange
        code = code
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_StopChartDataReqApi_010(self, exchange, code):
        """订阅一个手机图表数据,再取消订阅 """
        exchange = exchange
        code = code
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅手机图表数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.AppQuoteAllApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)



    # --------------------------------------------------查询当日分时数据-------------------------------------------------------
    @pytest.mark.testAPI
    def test_QueryKLineMinMsgReqApi_001(self):
        """分时查询--查询并订阅分时数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = "CUSmain"

        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))

        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')

        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_QueryKLineMinMsgReqApi_002(self):
        """分时查询--查询不订阅分时： isSubKLineMin = False"""
        frequence = 100
        isSubKLineMin = False
        exchange = HK_exchange
        code = HK_code1
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMinMsgReqApi_003(self):
        """分时查询--查询并订阅两个合约： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code1, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code1)

        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')

        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code1)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code2, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(
            query_kline_min_rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code2)

        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')

        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code2)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        if not self.common.check_trade_status(exchange, code1):
            assert info_list.__len__() == 0    
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(set([self.common.searchDicKV(info, 'code') for info in info_list]) == {code1, code2})

    def test_QueryKLineMinMsgReqApi_004(self):
        """分时查询： isSubKLineMin = True, exchange = UNKNOWN"""
        frequence = 100
        isSubKLineMin = True
        exchange = "UNKNOWN"
        code = HK_code1
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMinMsgReqApi_005(self):
        """分时查询： isSubKLineMin = True, code = xxx"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = 'xxx'
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMinMsgReqApi_006(self):
        """分时查询： isSubKLineMin = True, code = None"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = None
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(
            query_kline_min_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMinMsgReqApi_007(self):
        """分时查询： isSubKLineMin = True, 不登录, 查询当日分时, 返回的数据为空"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = HK_code1
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(query_kline_min_rsp_list.__len__() == 0)
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_QueryKLineMinMsgReqApi_008(self, exchange, code):
        """分时查询 并订阅--查询外期合约的分时数据"""
        frequence = 100
        isSubKLineMin = True
        exchange = exchange
        code = code
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end, vol, start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100, recv_timeout_sec=20))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_QueryKLineMinMsgReqApi_000(self, exchange, code):
        """分时查询--查询并订阅分时数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = "HSImain"
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))

        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code)

        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')

        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)




    # --------------------------------------------------查询五日分时数据-------------------------------------------------------
    @pytest.mark.testAPI
    def test_QueryFiveDaysKLineMinReqApi_001(self):
        """五日分时查询, 查询并订阅数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = "HSImain"
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)


    def test_QueryFiveDaysKLineMinReqApi_002(self):
        """五日分时查询, 查询不订阅数据： isSubKLineMin = False"""
        frequence = 100
        isSubKLineMin = False
        exchange = HK_exchange
        code = HK_code1
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryFiveDaysKLineMinReqApi_003(self):
        """五日分时查询： 查询两个合约的五日分时 """
        frequence = 100
        isSubKLineMin = False
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的五日分时')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code1, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code1)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code1)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code1)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'查询第二个合约的五日分时')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code2, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code2)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'检查查询返回的五日分时数据2')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code2)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code2)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        assert info_list.__len__() == 0

    def test_QueryFiveDaysKLineMinReqApi_004(self):
        """五日分时查询： exchange = UNKNOWN"""
        frequence = 100
        isSubKLineMin = True
        exchange = 'UNKNOWN'
        code = HK_code1
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryFiveDaysKLineMinReqApi_005(self):
        """五日分时查询： code = xxxx"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = 'xxxx'
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryFiveDaysKLineMinReqApi_006(self):
        """五日分时查询： code = UBmain"""
        frequence = 100
        isSubKLineMin = True
        exchange = 'HKFE'
        code = 'UBmain'
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryFiveDaysKLineMinReqApi_007(self):
        """五日分时查询： 不登录, 查询五日分时"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = HK_code1
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']

        self.assertTrue(query_5day_klinemin_rsp_list.__len__() == 0)
        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_QueryFiveDaysKLineMinReqApi_008(self, exchange, code):
        """查询所有合约 - 五日分时"""
        frequence = 100
        isSubKLineMin = False
        exchange = exchange
        code = code
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code)
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                if exchange == "HKFE":
                    assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]
                else:
                    assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]

            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_QueryFiveDaysKLineMinReqApi_009(self, exchange, code):
        """五日分时查询, 查询并订阅数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = HK_exchange
        code = "HSImain"
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_min_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange, code)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                if exchange == "HKFE":
                    assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]
                else:
                    assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
                    
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)



    # --------------------------------------------------查询历史K线-------------------------------------------------------
    @pytest.mark.testAPI
    def test_QueryKLineMsgReqApi_001(self):
        """K线查询: BY_DATE_TIME, 1分K, 前一小时的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = "MHImain"

        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 24 * 6
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        self.assertTrue(int(self.common.searchDicKV(sub_kline_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_kline_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=200))
        if not self.common.check_trade_status(exchange, code):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    def test_QueryKLineMsgReqApi_002(self):
        """K线查询: BY_DATE_TIME, 3分K, 前两个小时的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THREE_MIN
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 2
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')

    def test_QueryKLineMsgReqApi_003(self):
        """K线查询: BY_DATE_TIME, 5分K, 前40分钟的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIVE_MIN
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 2
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')

    def test_QueryKLineMsgReqApi_004(self):
        """K线查询: BY_DATE_TIME, 15分K, 前45分钟的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIFTEEN_MIN
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 2
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')

    def test_QueryKLineMsgReqApi_005(self):
        """K线查询: BY_DATE_TIME, 30分K, 前4小时的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THIRTY_MIN
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 4 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')

    def test_QueryKLineMsgReqApi_006(self):
        """K线查询: BY_DATE_TIME, 60分K, 前4小时的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.HOUR
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 4 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')

    def test_QueryKLineMsgReqApi_007(self):
        """K线查询: BY_DATE_TIME, 120分K, 前4小时的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.TWO_HOUR
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 4 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')

    def test_QueryKLineMsgReqApi_008(self):
        """K线查询: BY_DATE_TIME, 240分K, 前1天的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.FOUR_HOUR
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 24 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')

    def test_QueryKLineMsgReqApi_009(self):
        """K线查询: BY_DATE_TIME, 日K, 前5天的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 120 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')

    def test_QueryKLineMsgReqApi_010(self):
        """K线查询: BY_DATE_TIME, 周K, 前2周的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.WEEK
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 2 * 5 * 48 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')

    def test_QueryKLineMsgReqApi_011(self):
        """K线查询: BY_DATE_TIME, 月K, 前一个月的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MONTH
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 4 * 5 * 48 * 60 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')

    def test_QueryKLineMsgReqApi_012(self):
        """K线查询: BY_DATE_TIME, 1分K, 前5分钟的数据, isSubKLine = False(不订阅), frequence=100"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 3
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(sub_kline_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=end,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口,此时获取不到K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMsgReqApi_013(self):
        """K线查询: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    def test_QueryKLineMsgReqApi_014(self):
        """K线查询: BY_VOL, 3分K, 向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THREE_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')

    def test_QueryKLineMsgReqApi_015(self):
        """K线查询: BY_VOL, 5分K, 向前查询10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIVE_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')

    def test_QueryKLineMsgReqApi_016(self):
        """K线查询: BY_VOL, 15分K, 向前获取10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIFTEEN_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')

    def test_QueryKLineMsgReqApi_017(self):
        """K线查询: BY_VOL, 30分K, 向前查询10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THIRTY_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')

    def test_QueryKLineMsgReqApi_018(self):
        """K线查询: BY_VOL, 60分K, 向前获取4根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 4
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')

    def test_QueryKLineMsgReqApi_019(self):
        """K线查询: BY_VOL, 120分K, 向前获取5根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.TWO_HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')

    def test_QueryKLineMsgReqApi_020(self):
        """K线查询: BY_VOL, 240分K, 向前获取3根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.FOUR_HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 3
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')

    def test_QueryKLineMsgReqApi_021(self):
        """K线查询: BY_VOL, 日K, 向前获取5根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')

    def test_QueryKLineMsgReqApi_022(self):
        """K线查询: BY_VOL, 周K, 向前获取2根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.WEEK
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 2
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')

    def test_QueryKLineMsgReqApi_023(self):
        """K线查询: BY_VOL, 月K, 向前获取1根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MONTH
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')

    def test_QueryKLineMsgReqApi_024(self):
        """K线查询: BY_VOL, 1分钟K，向后查询50根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp, is_before_data=True,
                                                     start_time=start, exchange=exchange, instr_code=code,
                                                     peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    def test_QueryKLineMsgReqApi_025(self):
        """K线查询: BY_VOL, 3分K, 向后查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THREE_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')

    def test_QueryKLineMsgReqApi_026(self):
        """K线查询: BY_VOL, 5分K, 向后查询10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIVE_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')

    def test_QueryKLineMsgReqApi_027(self):
        """K线查询: BY_VOL, 15分K, 向后获取10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FIFTEEN_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')

    def test_QueryKLineMsgReqApi_028(self):
        """K线查询: BY_VOL, 30分K, 向后查询10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.THIRTY_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')

    def test_QueryKLineMsgReqApi_029(self):
        """K线查询: BY_VOL, 60分K, 向后获取5根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')

    def test_QueryKLineMsgReqApi_030(self):
        """K线查询: BY_VOL, 120分K, 向后获取5根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.TWO_HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')

    def test_QueryKLineMsgReqApi_031(self):
        """K线查询: BY_VOL, 240分K, 向后获取3根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.FOUR_HOUR
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 3
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')

    def test_QueryKLineMsgReqApi_032(self):
        """K线查询: BY_VOL, 日K, 向后获取5根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 5
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')

    def test_QueryKLineMsgReqApi_033(self):
        """K线查询: BY_DATE_TIME, 周K, 向后获取2根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.WEEK
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 20 * 24 * 60 * 60 * 1000
        end = None
        vol = 2
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')

    def test_QueryKLineMsgReqApi_034(self):
        """K线查询: BY_VOL, 月K, 向后获取2根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MONTH
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 24 * 60 * 60 * 1000
        end = None
        vol = 2
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')

    def test_QueryKLineMsgReqApi_035(self):
        """K线查询: 查询10000根 1分钟K线, 不订阅"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 10000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        self.assertTrue(sub_kline_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_036(self):
        """K线查询: 查询0根 1分钟K线, 不订阅, 提示vol错误"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 0
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(sub_kline_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_037(self):
        """K线查询: 查询两个合约的K线, 并订阅"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 10 * 60 * 60 * 1000
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code1, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code1, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code2, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code2)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code2, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code1, curTime=curTime):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

            assert set([self.common.searchDicKV(info, 'code') for info in info_list]) == {code1, code2}

    def test_QueryKLineMsgReqApi_038(self):
        """K线查询: 查询两个合约的K线, 并订阅"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 10 * 60 * 60 * 1000
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code1, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code1)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code1, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code2, peroid_type, query_type, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code2)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code2, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_039(self):
        """K线查询: 查询两个合约的K线数据, 其中合约A按时间查询, 合约B按数量查询"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        peroid_type = KLinePeriodType.MINUTE
        query_type1 = QueryKLineMsgType.BY_VOL
        query_type2 = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 10 * 60 * 60 * 1000
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的K线数据, 按数量查询')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code1, peroid_type, query_type1, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code1)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code1, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约的K线数据, 按数量查询')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code2, peroid_type, query_type2, direct, start,
                                                end,
                                                vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code2)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=start, exchange=exchange,
                                                     instr_code=code2, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_040(self):
        """
        K线查询: exchange="UNKNOWN"
        """
        frequence = 100
        isSubKLine = True
        exchange = "UNKNOWN"
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        assert sub_kline_rsp_list.__len__() == 0

        assert self.common.searchDicKV(query_kline_rsp_list[0], 'kData') == None


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_041(self):
        """
        K线查询: code="xxx"
        """
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = "xxx"
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        assert sub_kline_rsp_list.__len__() == 0

        assert self.common.searchDicKV(query_kline_rsp_list[0], 'kData') == None


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_042(self):
        """
        K线查询: code="xxx"
        """
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = None
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 60 * 1000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        assert sub_kline_rsp_list.__len__() == 0

        assert self.common.searchDicKV(query_kline_rsp_list[0], 'kData') == None

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_043(self):
        """K线查询: BY_VOL, 获取K线的方式为UNKNOWN_QUERY_KLINE"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')

        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg error. unKnown QueryKLineMsgType')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)


        assert sub_kline_rsp_list.__len__() == 0

        assert self.common.searchDicKV(query_kline_rsp_list[0], 'kData') == None

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_044(self):     # BUG : 查询失败时, 订阅成功了
        """K线查询: BY_VOL, 获取K线的方向为UNKNOWN_QUERY_DIRECT"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        assert sub_kline_rsp_list.__len__() == 0

        assert self.common.searchDicKV(query_kline_rsp_list[0], 'kData') == None

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_QueryKLineMsgReqApi_045(self):
        """
        K线查询: frequence = 2
        """
        frequence = 2
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp, is_before_data=True,
                                                     start_time=start, exchange=exchange, instr_code=code,
                                                     peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code) :
            assert info_list.__len__() == 0
        else:
            self.common.checkFrequence(info_list, frequence)
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    def test_QueryKLineMsgReqApi_046(self):
        """
        K线查询: frequence = 100
        """
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp, is_before_data=True,
                                                     start_time=start, exchange=exchange, instr_code=code,
                                                     peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            self.common.checkFrequence(info_list, frequence)
            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    def test_QueryKLineMsgReqApi_047(self):
        """
        K线查询: 不登录, 直接查询K线数据
        """
        frequence = 0
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 50
        self.logger.debug(u'不登录, 直接查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']

        assert query_kline_rsp_list.__len__() == 0
        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0


    @parameterized.expand(appFuturesCode(isKLine=True))
    @pytest.mark.allStock
    def test_QueryKLineMsgReqApi_049(self, exchange, code, peroidType):
        """ K线查询, 查询所有合约的K线频率, 按数量查询向前查询 """
        frequence = 100
        isSubKLine = True
        exchange = exchange
        code = code
        peroid_type = peroidType
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 200
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')
        self.assertTrue(int(self.common.searchDicKV(
            sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=int(time.time() * 1000), start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)

    @parameterized.expand(appFuturesCode(isKLine=True))
    @pytest.mark.allStock
    def test_QueryKLineMsgReqApi_050(self, exchange, code, peroidType):
        """ K线查询, 查询所有合约的K线频率, 按时间查询 """
        frequence = None
        isSubKLine = True
        exchange = exchange
        code = code
        peroid_type = peroidType
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        if peroidType in ["MONTH", "SEASON", "YEAR"]:
            start = start_time_stamp - 24 * 60 * 60 * 1000 * 365 * 2    # 2年的数据
        else:
            start = start_time_stamp - 24 * 60 * 60 * 1000 * 15     # 查询15天的数据
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')
        self.assertTrue(int(self.common.searchDicKV(
            sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)


    @parameterized.expand(appFuturesCode(isHKFE=True, isKLine=True))
    @pytest.mark.HFEK
    def test_QueryKLineMsgReqApi_051(self, exchange, code, peroidType):
        """ K线查询, 查询所有合约的K线频率, 按数量查询向前查询 """
        frequence = 100
        isSubKLine = True
        exchange = exchange
        code = code
        peroid_type = peroidType
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        if peroidType in ["MONTH", "SEASON", "YEAR"]:
            vol = 5
        else:
            vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')
        self.assertTrue(int(self.common.searchDicKV(
            sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=int(time.time() * 1000), start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)


    @parameterized.expand(appFuturesCode(isHKFE=True, isKLine=True))
    @pytest.mark.HFEK
    def test_QueryKLineMsgReqApi_052(self, exchange, code, peroidType):
        """ K线查询, 查询所有合约的K线频率, 按时间查询 """
        frequence = None
        isSubKLine = True
        exchange = exchange
        code = code
        peroid_type = peroidType
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        if peroidType in ["MONTH", "SEASON", "YEAR"]:
            start = start_time_stamp - 24 * 60 * 60 * 1000 * 365 * 2    # 2年的数据
        else:
            start = start_time_stamp - 24 * 60 * 60 * 1000 * 5     # 查询15天的数据
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')
        self.assertTrue(int(self.common.searchDicKV(
            sub_kline_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        if not self.common.check_trade_status(exchange, code, curTime=curTime):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
            self.assertTrue(info_list.__len__() == 0)
        else:
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)





    # --------------------------------------------------逐笔成交查询-------------------------------------------------------
    @pytest.mark.testAPI
    def test_QueryTradeTickMsgReqApi_001(self):
        """
        查询逐笔成交--查询5分钟的逐笔成交数据, 并订阅逐笔成交
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code2

        # exchange = "NYMEX"
        # code = "CLmain"
        
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按时间查询, 方向没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 120:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_002(self):
        """
        查询逐笔成交--查询10分钟的逐笔成交数据, 不订阅逐笔成交
        """
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 10 * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)


        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_003(self):
        """
        查询逐笔成交--查询1小时的逐笔成交数据
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_004(self):
        """
        查询逐笔成交--按日期查询--开始时间==结束时间
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0].keys())
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
        assert info_list.__len__() == 0

    def test_QueryTradeTickMsgReqApi_005(self):
        """
        查询逐笔成交--按日期查询--开始时间大于结束时间
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code2
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 5 * 60 * 1000
        end_time = start_time_stamp - 10 * 60 * 1000
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_006(self):
        """
        查询逐笔成交--按日期查询--开始时间为None
        """
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code = HK_code2
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None
        start_time_stamp = int(time.time() * 1000)
        start_time = None
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)


        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_008(self):
        """
        查询逐笔成交--按日期查询--结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code3
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_009(self):
        """
        按量查询100条-向前查询-开始时间为当前时间, 结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        # vol = 10
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_010(self):
        """
        按量查询100条-向前-开始时间为5分钟前

        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 5 * 60 * 1000
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_011(self):
        """
        按量查询100条-向前-开始时间为10分钟前
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 10 * 60 * 1000
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_012(self):
        """
        按量查询100条-向前-开始时间为未来时间, 可以查询成功
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + 10 * 60 * 1000
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_013(self):
        """
        按量查询100条-向前-开始时间None, 结束时间为当前时间, 可以查询成功
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = None
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time_stamp, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_014(self):
        """
        按量查询100条-向后-开始时间为当前时间, 结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        # self.logger.debug("校验收到的tickData为空")
        # assert "tickData" not in query_trade_tick_rsp_list[0].keys()

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_015(self):
        """
        按量查询1000条-向后-开始时间为1分钟前, 校验不够条数时处理正常
        """
        frequence = 100
        isSubTrade = True
        isSubTrade2 = False
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000
        end_time = start_time_stamp
        vol = 1000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_016(self):
        """
        按量查询100条-向后-开始时间为5分钟前
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        # self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_017(self):
        """
        按量查询100条-向后-开始时间为10分钟前
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_018(self):
        """
        按量查询100条-向后-开始时间为未来时间
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code2
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + 10 * 60 * 1000
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_019(self):
        """
        按量查询100条-向后-开始时间None, 结束时间为当前时间
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code2
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = None
        end_time = start_time_stamp
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_020(self):
        """
        按日期查询, 开始时间和结束时间都为空
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = None
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_021(self):
        """
        按量查询-查询一万条数据
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 10000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(query_trade_tick_rsp_list[0].get(
            "tickData").__len__() == vol)
        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_022(self):
        """
        按量查询-查询数量为0
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 0
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_023(self):
        """
        查询两个合约--顺便订阅
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的逐笔成交')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code1, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约的逐笔成交')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code2, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code1):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            assert set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2}
            assert set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange}

            # self.assertTrue(set([info.get("instrCode") for info in info_list]) == {code1, code2})
            # self.assertTrue(set([info.get("exchange") for info in info_list]) == {exchange})

    def test_QueryTradeTickMsgReqApi_024(self):
        """
        查询两个合约--不订阅
        """
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个合约的逐笔成交')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code1, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个合约的逐笔成交')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code2, type, direct, start_time, end_time,
                                                    vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_025(self):
        """
        逐笔成交-不同查询方式查询两个合约, 并订阅
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        type1 = QueryKLineMsgType.BY_VOL
        type2 = QueryKLineMsgType.BY_DATE_TIME
        direct1 = QueryKLineDirectType.WITH_FRONT
        direct2 = None
        start_time_stamp = int(time.time() * 1000)
        start_time1 = start_time_stamp
        end_time1 = None
        start_time2 = start_time_stamp - 60 * 60 * 1000
        end_time2 = start_time_stamp
        vol = 100

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'按数量查询第一个合约的逐笔数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code1, type1, direct1, start_time1, end_time1,
                                                    vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code1)
        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time1, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug("按时间查询第二个合约的逐笔数据")
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code2, type2, direct2, start_time2, end_time2,
                                                    vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time2, start_time=start_time2)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.assertTrue(self.common.checkFrequence(info_list, frequence))

        assert set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2}
        assert set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange}

    def test_QueryTradeTickMsgReqApi_026(self):
        """
        查询逐笔成交--未定义的交易所
        """
        frequence = 100
        isSubTrade = True
        exchange = "UNKNOWN"
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_027(self):
        """
        查询逐笔成交--不存在的合约代码
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = "xxx"
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(
            query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_028(self):
        """
        查询逐笔成交--合约代码为None
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = None
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(
            query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_029(self):
        """
        查询逐笔成交--获取K线的方式为UNKNOWN_QUERY_KLINE
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_030(self):     # BUG : 查询失败, 订阅成功了
        """
        查询逐笔成交--获取K线的方向为UNKNOWN_QUERY_DIRECT
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_031(self):
        """
        查询逐笔数据--frequence=0, 数据更新频率为默认
        """
        frequence = None
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 1000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(query_trade_tick_rsp_list[0].get("tickData").__len__() == vol)
        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_032(self):
        """
        查询逐笔数据--frequence=2, 数据更新频率为2 (8月12号, 逐笔不做过滤, 防止丢数据)
        """
        frequence = None   
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 1000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(query_trade_tick_rsp_list[0].get("tickData").__len__() == vol)
        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_QueryTradeTickMsgReqApi_033(self):
        """
        查询逐笔数据--frequence=10, 数据更新频率为10 ( (8月12号, 逐笔不做过滤, 防止丢数据))
        """
        frequence = None
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 1000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(query_trade_tick_rsp_list[0].get("tickData").__len__() == vol)
        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))
        if not self.common.check_trade_status(exchange, code, curTime):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_zmq_test_case('test_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_QueryTradeTickMsgReqApi_034(self):
        """
        查询逐笔成交--未登录, 查询逐笔
        """
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 50
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']

        self.assertTrue(query_trade_tick_rsp_list.__len__() == 0)
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_QueryTradeTickMsgReqApi_035(self, exchange, code):
        """
        查询逐笔成交--查询外期逐笔成交
        """
        frequence = None
        isSubTrade = False
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 24 * 60 * 60 * 1000  # 查询一天的数据, 不活跃外期合约可能没数据
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_QueryTradeTickMsgReqApi_036(self, exchange, code):
        """
        查询逐笔成交--查询所有合约, 当天的逐笔数据
        """
        frequence = None
        isSubTrade = False
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        _first_tradeTime = self.common.check_trade_status(exchange, code, isgetTime=True)[0]    # 获取交易开始时间
        self.logger.debug("请求的开始时间为 : {}".format(_first_tradeTime))
        _first_tradeTime = int(time.mktime(time.strptime(_first_tradeTime, "%Y%m%d%H%M%S")) * 1000)   # 转换成时间戳
        start_time = _first_tradeTime   # 转换成时间戳
        end_time = start_time_stamp     # 当前时间
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        assert int([tick["time"] for tick in tick_data_list][0]) >= int(_first_tradeTime)

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_QueryTradeTickMsgReqApi_037(self, exchange, code):
        """
        查询逐笔成交--查询外期逐笔成交
        """
        frequence = None
        isSubTrade = False
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 24 * 60 * 60 * 1000  # 查询一天的数据, 不活跃外期合约可能没数据
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand([[HK_exchange, eval("HK_main{}".format(n + 1))] for n in range(5)])
    @pytest.mark.HFEK
    def test_QueryTradeTickMsgReqApi_038(self, exchange, code):
        """
        查询逐笔成交--查询所有合约, 当天的逐笔数据
        """
        frequence = None
        isSubTrade = False
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
        start_time_stamp = int(time.time() * 1000)
        _first_tradeTime = self.common.check_trade_status(exchange, code, isgetTime=True)[0]    # 获取交易开始时间
        self.logger.debug("请求的开始时间为 : {}".format(_first_tradeTime))
        _first_tradeTime = int(time.mktime(time.strptime(_first_tradeTime, "%Y%m%d%H%M%S")) * 1000)   # 转换成时间戳
        start_time = _first_tradeTime   # 转换成时间戳
        end_time = start_time_stamp     # 当前时间
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        assert int([tick["time"] for tick in tick_data_list][0]) >= int(_first_tradeTime)

        inner_test_result = self.inner_zmq_test_case('test_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)





    # --------------------------------------------查询品种交易状态------------------------------------------------
    @pytest.mark.testAPI
    def test_QueryTradeStatusMsgReqApi_001(self):
        """product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = HK_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == 6)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000)) 
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert status == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_002(self):
        """product_list为 HSI、HHI、MHI"""
        start_time_stamp = int(time.time() * 1000)
        exchange = HK_exchange
        product_list = ['HSI', 'HHI', 'MHI']
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == product_list.__len__())
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            self.assertTrue(data['productCode'] in product_list)
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert status == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_003(self):
        """exchange为UNKNOWN"""
        start_time_stamp = int(time.time() * 1000)
        exchange = 'UNKNOWN'
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

    def test_QueryTradeStatusMsgReqApi_004(self):
        """product_list包含一个错误产品代码"""
        start_time_stamp = int(time.time() * 1000)
        exchange = HK_exchange
        product_list = ['MHI', 'HSI', 'xxx']
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'SUCCESS')
        datas = first_rsp_list[1]['data']
        self.assertTrue(datas.__len__() == 2)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert status == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_005(self):
        """外期NYMEX product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = NYMEX_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]["data"]
        assert datas.__len__() == 4
        for data in datas:
            assert data['exchange'] == exchange
            assert data['productCode']
            assert data['status']
            assert data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_006(self):
        """外期 COMEX, product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = COMEX_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]["data"]
        assert datas.__len__() == 6
        for data in datas:
            assert data['exchange'] == exchange
            assert data['productCode']
            assert data['status']
            assert data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_007(self):
        """外期 CBOT, product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = CBOT_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        datas = first_rsp_list[0]["data"]
        assert datas.__len__() == 10
        for data in datas:
            assert data['exchange'] == exchange
            assert data['productCode']
            assert data['status']
            assert data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_008(self):
        """外期 CME, product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = CME_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]["data"]
        assert datas.__len__() == 14
        for data in datas:
            assert data['exchange'] == exchange
            assert data['productCode']
            assert data['status']
            assert data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_009(self):
        """外期 SGX, product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = SGX_exchange
        product_list = []
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]["data"]
        assert datas.__len__() == 3
        for data in datas:
            assert data['exchange'] == exchange
            assert data['productCode']
            assert data['status']
            assert data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_010(self):
        """外期 CME: product_list为 ES、NQ、6A"""
        start_time_stamp = int(time.time() * 1000)
        exchange = CME_exchange
        product_list = ['ES', 'NQ', '6A']
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == product_list.__len__())
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            self.assertTrue(data['productCode'] in product_list)
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            curtime = time.strftime("%Y%m%d%H%M%S", time.localtime(int(data['timeStamp']) / 1000))
            if self.common.check_trade_status(exchange, data['productCode'], curtime):
                assert data['status'] == "TRADE_TRADING"

    def test_QueryTradeStatusMsgReqApi_011(self):
        """外期 CME: product_list为 HSI、HHI、MHI"""
        start_time_stamp = int(time.time() * 1000)
        exchange = CME_exchange
        product_list = ['HSI', 'HHI', 'MHI']
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))
        self.assertTrue(first_rsp_list.__len__() == 1)
        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')


    #########################  查询BMP  #######################
    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_BMP_QueryKLineMinMsgReqApi_001(self, exchange, code):
        """查询BMP分时, 不订阅 -- 可以查询到最新数据, 不会推送消息"""
        frequence = None
        isSubKLineMin = False
        exchange = exchange
        code = code

        # exchange = "NASDAQ"
        # code = "AAPL"

        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时数据查询，检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp, sub_quote_type="BMP_QUOTE_MSG"))

        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']

        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'startTimeStamp')))

        assert sub_kline_min_rsp_list.__len__() == 0

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        query_rspTimeStamp = int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp'))

        if self.common.check_trade_status(exchange, code):
            assert self.common.searchDicKV(info_list[-1], "updateDateTime")[:-2] <= self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_zmq_test_case('test_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=query_rspTimeStamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        assert info_list.__len__() == 0


    ####################BMQ k线####################
    @parameterized.expand(appFuturesCode())
    @pytest.mark.allStock
    def test_BMP_QueryKLineMsgReqApi_001(self, exchange, code):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = 100
        isSubKLine = False
        exchange = exchange
        code = code
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 24 * 2
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp, sub_quote_type="BMP_QUOTE_MSG"))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')

        if self.common.check_trade_status(exchange, code):
            assert self.common.searchDicKV(k_data_list[-1], "KLineKey")[:-2] <= self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_zmq_test_case('test_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0




    # ---------------------------------------- 以下是调试方法, 请忽略 --------------------------------------------

    def test_Snapshot_check_Vol(self):
        """
        校验分时数据的成交量
        订阅快照后接收一段时间的快照数据, 筛选出1分钟时间段的快照, 然后跟分时的成交量对比
        """
        exchange = "SEHK"
        code = "00700"
        frequence = 4
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅行情快照')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))

        self.logger.debug(u'接收200秒的实时快照')
        # 接收时间设置长一点, 防止查询分时时, 还未计算出分时线
        rspDict = asyncio.get_event_loop().run_until_complete(future=self.api.get_QuoteSnapshot())
        startMin = int((datetime.datetime.fromtimestamp(rspTimeStamp/1000) + datetime.timedelta(minutes=1)).replace(second=0,microsecond=0).timestamp() * 1000)
        stopMin = int((datetime.datetime.fromtimestamp(startMin/1000) + datetime.timedelta(minutes=1)).replace(second=0,microsecond=0).timestamp() * 1000)
        self.logger.info(startMin)
        self.logger.info(stopMin)
        vols = []
        _isbefoce = True
        for key in rspDict.keys():
            if int(key) >= startMin and int(key) <= stopMin:
                # 找到第一个时, 再拿前一个, 计算第一个快照的成交量
                # if _isbefoce:
                #     if list(rspDict.keys()).index(key) > 1:
                #         beforekey = list(rspDict.keys())[list(rspDict.keys()).index(key) -1]
                #         self.logger.debug(beforekey)
                #         self.logger.debug(rspDict[beforekey])
                #         vols.append(int(rspDtest_QueryKLineMsgReqApi_049ict[beforekey].get("volume") or 0))
                #     _isbefoce = False

                self.logger.debug(rspDict[key])
                vols.append(int(rspDict[key].get("volume") or 0))

        self.logger.debug([vols[i+1] - vols[i] for i in range(len(vols)-1)])
        self.logger.debug([vols[i+1] - vols[i] for i in range(len(vols)-1)].__len__())
        vol = sum([vols[i+1] - vols[i] for i in range(len(vols)-1)])
        self.logger.info("一分钟的成交量为 : {}".format(vol))

        # 查询分时, 找到这一分钟的分时数据, 递归查
        isSubKLineMin = False
        start_time_stamp = int(time.time() * 1000)
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin=isSubKLineMin, exchange=exchange, code=code, start_time_stamp=start_time_stamp))

        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list'][0].get("data")
        stopValue = time.strftime("%Y%m%d%H%M", time.localtime(stopMin / 1000)) + "00"
        self.logger.debug(stopValue)
        minDict = self.common.searchDict_By_Value(query_kline_min_rsp_list, stopValue)
        self.logger.info(minDict)
        assert int(minDict.get("vol")) == int(vol)


    def test_00001(self):
        """订阅一个合约的逐笔: frequence=None"""
        frequence = None
        exchange = "CME"
        code = "NQmain"
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        while True:
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1))


                
if __name__ == "__main__":
    # suite = unittest.TestSuite()
    # tests = [Test_Subscribe("test_QueryTradeStatusMsgReqApi_011")]
    # suite.addTests(tests)
    # runner = unittest.TextTestRunner(verbosity=2)
    # runner.run(suite)

    pytest.main(["-v", 
                 "-s",
                 "test_subscribe_api.py",
                 "-k test_QueryKLineMsgReqApi_001",
                 "--show-capture=stderr",     # 测试失败后, 只输出stderr信息
                 "--disable-warnings"
                 ])


    # appFuturesCode(isHKFE=True, isKLine=True)