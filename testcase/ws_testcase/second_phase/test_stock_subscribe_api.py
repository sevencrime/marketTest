# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/9/1
# @Software: PyCharm

import unittest
import pytest
import allure
from parameterized import parameterized, param

from common.get_basic.get_InstrCode import get_all_instrCode
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from testcase.zmq_testcase.zmq_stock_record_testcase import CheckZMQ as CheckStockZMQ
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient


class Test_Subscribe(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        # self.logger = get_log()
        # self.http = MarketHttpClient()
        # self.market_token = self.http.get_market_token(
        #     self.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

    @classmethod
    def setUpClass(cls):
        cls.common = Common()
        cls.logger = get_log()
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
        self.new_loop.close()

    def inner_stock_zmq_test_case(self, case_name, check_json_list, is_before_data=False, start_sub_time=None,
                            start_time=None, exchange=None, instr_code=None, peroid_type=None, is_delay=None):
        suite = unittest.TestSuite()
        suite.addTest(CheckStockZMQ(case_name))
        suite._tests[0].check_json_list = check_json_list
        suite._tests[0].is_before_data = is_before_data
        suite._tests[0].sub_time = start_sub_time
        suite._tests[0].start_time = start_time
        suite._tests[0].exchange = exchange
        suite._tests[0].instr_code = instr_code
        suite._tests[0].peroid_type = peroid_type
        suite._tests[0].is_delay = is_delay
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



    # --------------------------------------------------订阅分时数据-------------------------------------------------------
    # 1: 分时订阅一个股票
    # 2: 分时订阅2个股票
    # 3: 分时订阅一个股票, code=xxxx
    # 4: 分时订阅一个股票, exchange='UNKNOWN'
    # 5: 分时订阅一个股票, code=NASDAQ_code1
    # 6: 分时订阅一个股票, code=None
    # 7: 分时订阅一个股票, exchange=None
    # 8: 分时订阅美股股票和指数其他产品
    # 9: 分时订阅2个股票, 其中一个美股, 一个港股
    # 10: 分时订阅暗盘

    @pytest.mark.testAPI
    def test_stock_SubscribeKlineMinReqApi_001(self):
        """分时订阅一个股票"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查回结果')
        _start = time.time()
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp, recv_num=1))
        self.logger.error("时间 : {}".format(time.time() - _start))
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100, recv_timeout_sec=20))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_stock_SubscribeKlineMinReqApi_002(self):
        """分时订阅2个股票"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅第一个股票')
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

        self.logger.debug(u'分时订阅第二个股票')
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
        if not self.common.check_trade_status(exchange) or not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'code'))

            self.assertTrue(set(recv_code_list) == {code1, code2})
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_stock_SubscribeKlineMinReqApi_003(self):
        """分时订阅一个股票, code=xxxx"""
        frequence = 100
        exchange = SEHK_exchange
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKlineMinReqApi_004(self):
        """分时订阅一个股票, exchange='UNKNOWN'"""
        frequence = 100
        exchange = 'UNKNOWN'
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKlineMinReqApi_005(self):
        """分时订阅一个股票, code=NASDAQ_code1"""
        frequence = 100
        exchange = SEHK_exchange
        code = NASDAQ_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKlineMinReqApi_006(self):
        """分时订阅一个股票, code=None"""
        frequence = 100
        exchange = SEHK_exchange
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKlineMinReqApi_007(self):
        """分时订阅一个股票, exchange=None"""
        frequence = 100
        exchange = None
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))

        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_SubscribeK1lineMinReqApi_008(self, exchange, code):
        """分时订阅美股股票"""
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
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_stock_SubscribeKlineMinReqApi_009(self):
        """分时订阅2个股票, 其中一个美股, 一个港股"""
        frequence = 100
        exchange = SEHK_exchange
        exchange2 = NASDAQ_exchange
        code1 = SEHK_code1
        code2 = NASDAQ_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅第一个股票')
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

        self.logger.debug(u'分时订阅第二个股票')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange) and not self.common.check_trade_status(exchange2):
            self.assertTrue(info_list.__len__() == 0)
        else:
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'code'))
            if self.common.check_trade_status(exchange) and self.common.check_trade_status(exchange2):
                self.assertTrue(set(recv_code_list) == {code1, code2})
            else:
                assert set(recv_code_list) == {code1} or set(recv_code_list) == {code2}

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    @pytest.mark.Grey
    def test_stock_SubscribeKlineMinReqApi_010(self):
        """分时订阅暗盘"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=200))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)





    # --------------------------------------------------取消订阅分时数据-------------------------------------------------------
    # 1: 分时订阅一个股票,取消订阅
    # 2: 分时订阅2个股票,取消订阅其中一个
    # 3: 分时订阅2个股票,取消订阅2个
    # 4: 查询分时时顺便订阅了分时，再取消分时订阅
    # 5: 查询5日分时时顺便订阅了分时，再取消分时订阅
    # 6: 分时订阅一个股票,取消订阅一个未订阅的股票
    # 7: 分时订阅一个股票,取消订阅入参exchange=UNKNOWN
    # 8: 分时订阅一个股票,取消订阅一个不存在的股票
    # 9: 分时订阅一个美股股票,取消订阅
    # 10: 分时订阅一个全部股票,再取消订阅
    # 11: 分时订阅暗盘,取消订阅暗盘

    @pytest.mark.testAPI
    def test_stock_UnsubscribeKlineMinReqApi_001(self):
        """分时订阅一个股票,取消订阅"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeKlineMinReqApi_002(self):
        """分时订阅2个股票,取消订阅其中一个"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))

        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            self.assertTrue(info_list.__len__() > 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code2)

    def test_stock_UnsubscribeKlineMinReqApi_003(self):
        """分时订阅2个股票,取消订阅2个"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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

        self.logger.debug(u'订阅两个分时数据后, 接收数据, 校验是否接收到两个股票的数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeKlineMinReqApi_004(self):
        """查询分时时顺便订阅了分时，再取消分时订阅"""
        frequence = 100
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeKlineMinReqApi_005(self):
        """查询5日分时时顺便订阅了分时，再取消分时订阅"""
        frequence = 100
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeKlineMinReqApi_006(self):
        """分时订阅一个股票,取消订阅一个未订阅的股票"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
        code2 = SEHK_code8
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_stock_UnsubscribeKlineMinReqApi_007(self):
        """分时订阅一个股票,取消订阅入参exchange=UNKNOWN"""
        frequence = 100
        exchange = SEHK_exchange
        exchange2 = 'UNKNOWN'
        code = SEHK_code1
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

    def test_stock_UnsubscribeKlineMinReqApi_008(self):
        """分时订阅一个股票,取消订阅一个不存在的股票"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_UnsubscribeKlineMinReqApi_009(self):
        """分时订阅一个美股股票,取消订阅"""
        frequence = 100
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
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
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_UnsubscribeKlineMinReqApi_010(self, exchange, code):
        """分时订阅一个美股股票,取消订阅"""
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


    @pytest.mark.Grey
    def test_stock_UnsubscribeKlineMinReqApi_011(self):
        """分时订阅一个股票,取消订阅暗盘"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        self.assertTrue(info_list.__len__() == 0)




    # --------------------------------------------------K线订阅----------------------------------------------
    # 1: 港股 - K线订阅-订阅单个股票的K线
    # 2: 港股 - K线订阅-订阅两个股票的K线
    # 3: 港股 - K线订阅-订阅K线数据时, 使用错误的股票代码
    # 4: 港股 - K线订阅-订阅K线数据时, 使用错误的交易所
    # 5: 港股 - 订阅港股K线, 遍历K线频率
    # 6: 港股 - K线周期定义为 UNKNOWN_PERIOD
    # 7: 港股 - 订阅K线数据, code=None
    # 8: 美股 - 订阅K线
    # 9: 美股 - 遍历美股K线频率
    # 10: 订阅所有股票的K线
    # 11: 订阅暗盘K线

    @pytest.mark.testAPI
    def test_stock_SubscribeKLineMsgReqApi_001(self):
        """K线订阅-订阅单个股票的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))

    def test_stock_SubscribeKLineMsgReqApi_002(self):
        """K线订阅-: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug("订阅第一个股票的K线数据")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug("订阅第二个股票的K线数据")
        start_time_stamp2 = int(time.time() * 1000)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp2))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp2)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))

        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            self.logger.debug(u"校验接收的数据中包含两个股票的数据")
            codeinfo = [info.get("code") for info in info_list]
            self.assertTrue(set(codeinfo) == {code1, code2})
            self.assertTrue(exchange in [info.get("exchange") for info in info_list])
            self.assertTrue(KLinePeriodType.Name(peroid_type) in [info.get("peroidType") for info in info_list])
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_stock_SubscribeKLineMsgReqApi_003(self):
        """K线订阅-订阅K线数据时, 使用错误的股票代码: code="xxx" peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = SEHK_exchange
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKLineMsgReqApi_004(self):
        """K线订阅-订阅K线数据时, 使用错误的交易所: exchange="UNKNOWN" peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = "UNKNOWN"
        code = SEHK_code1
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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
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
    def test_stock_SubscribeKLineMsgReqApi_005(self, peroid_type):
        """
        订阅港股K线, 遍历K线数据
        """
        self.logger.debug("订阅K线数据 -- 订阅频率 : {}".format(KLinePeriodType.Name(peroid_type)))
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))

        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))

    def test_stock_SubscribeKLineMsgReqApi_006(self):
        """
        K线订阅-订阅K线数据, K线周期定义为 UNKNOWN_PERIOD
        """
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKLineMsgReqApi_007(self):
        """
        K线订阅-订阅K线数据, code=None

        """
        frequence = 100
        exchange = SEHK_exchange
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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeKLineMsgReqApi_008(self):
        """K线订阅-订阅美股K线"""
        frequence = 100
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))

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
    def test_stock_SubscribeKLineMsgReqApi_009(self, peroid_type):
        """
        订阅美股K线, 遍历美股K线数据
        """
        self.logger.debug("订阅K线数据 -- 订阅频率 : {}".format(KLinePeriodType.Name(peroid_type)))
        frequence = 100
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=150))

        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))


    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        # (NYSE_exchange, NYSE_code1), 
        # (NASDAQ_exchange, NASDAQ_code1), 
        # (SEHK_exchange, SEHK_indexCode1),       # 指数
        # (SEHK_exchange, SEHK_TrstCode1),        # 信托
        # (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        # (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        # (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_SubscribeKLineMsgReqApi_010(self, exchange, code):
        """K线订阅-- 遍历所有K线"""
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))

    @pytest.mark.Grey
    def test_stock_SubscribeKLineMsgReqApi_011(self):
        """K线订阅-订阅暗盘"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        # 订阅频率
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list, exchange="Grey")
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                # 校验频率
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == KLinePeriodType.Name(peroid_type))




    # --------------------------------------------------取消K线订阅-------------------------------------------
    # 1: 取消K线订阅 - 取消单个股票
    # 2: 取消K线订阅 - 订阅两个股票, 取消其中一个
    # 3: 取消K线订阅 - 订阅两个股票, 取消两个
    # 4: 取消K线订阅 - 取消订阅K线时, code=xxx
    # 5: 取消K线订阅 - 取消订阅K线时, K线频率与订阅不一致
    # 6: 取消K线订阅 - 取消订阅K线时, exchange=UNKNOWN
    # 7: 取消K线订阅 - 订阅A股票后, 取消订阅B股票
    # 8: 取消K线订阅 - 查询K线数据时顺便订阅K线数据, 订阅成功后再取消K线订阅
    # 9: 取消K线订阅 - 取消订阅所有股票类型
    # 10: 取消K线订阅 - 取消订阅暗盘K线

    @pytest.mark.testAPI
    def test_stock_UnsubscribeKLineMsgReqApi_001(self):
        """取消K线订阅-取消订阅单个股票的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeKLineMsgReqApi_002(self):
        """
        取消K线订阅-订阅两个股票的K线数据, 再取消订阅其中一个
        peroid_type = KLinePeriodType.MINUTE
        """
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u"订阅第一个股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"订阅第二个股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"取消订阅第一个股票的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u"接收k线数据")
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            self.logger.debug(u"校验接收不到第一个股票的数据")
            self.assertTrue(info_list.__len__() > 0)
            self.assertTrue(set([info.get("code") for info in info_list]) == {code2})
            # 校验交易所
            self.assertTrue(exchange in [info.get("exchange") for info in info_list])
            # 校验频率
            self.assertTrue(KLinePeriodType.Name(peroid_type) in [info.get("peroidType") for info in info_list])
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_stock_UnsubscribeKLineMsgReqApi_003(self):
        """
        取消K线订阅-订阅两个股票的K线数据, 再取消订阅两个股票
        peroid_type = KLinePeriodType.MINUTE
        """
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u"订阅第一个股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"订阅第二个股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u"取消订阅第一个股票的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u"取消订阅第二个股票的K线数据")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
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

    def test_stock_UnsubscribeKLineMsgReqApi_004(self):
        """取消K线订阅-取消订阅不存在的股票: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_UnsubscribeKLineMsgReqApi_005(self):     # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-497
        """
        取消K线订阅-取消订阅时, K线周期不一致
        """
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug("取消订阅-K线周期不一致")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=un_peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)

    def test_stock_UnsubscribeKLineMsgReqApi_006(self):     # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-499    
        """
        取消K线订阅-取消订阅时, 交易所exchange=UNKNOWN
        """
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        base_info1 = [{'exchange': "UNKNOWN", 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        self.logger.debug("订阅股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        if not self.common.check_trade_status(exchange, code):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange,code):
            assert info_list.__len__() == 0
        else:
            assert info_list.__len__() > 0

    def test_stock_UnsubscribeKLineMsgReqApi_007(self):
        """
        取消K线订阅-订阅A股票后, 取消订阅B股票
        """
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
        code2 = SEHK_code8
        base_info = [{'exchange': exchange, 'code': code}]
        base_info1 = [{'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        un_peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        self.logger.debug("订阅股票")
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug("取消订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=un_peroid_type, base_info=base_info1,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 接收K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

    def test_stock_UnsubscribeKLineMsgReqApi_008(self):
        """
        取消K线订阅-查询K线数据时顺便订阅K线数据, 订阅成功后再取消K线订阅
        """
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)

        self.logger.debug(u"取消K线订阅")
        un_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(un_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(un_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(un_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅后, 无法接收到K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_UnsubscribeKLineMsgReqApi_009(self, exchange, code):
        """取消K线订阅-取消订阅单个股票的K线: peroid_type = KLinePeriodType.MINUTE"""
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

    @pytest.mark.Grey
    def test_stock_UnsubscribeKLineMsgReqApi_010(self):
        """取消K线订阅-取消订阅K线暗盘"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
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




    # --------------------------------------------------订阅逐笔成交数据---------------------------------------
    # 1: 港股, 订阅一个股票的逐笔
    # 2: 美股, 订阅一个股票的逐笔
    # 3: 港股, 订阅2个股票的逐笔
    # 4: 订阅一个股票的逐笔: exchange=UNKNOWN
    # 5: 订阅一个股票的逐笔: code=xxxx
    # 6: 美股, 订阅两个美股的逐笔 
    # 7: 美股, 订阅一个股票的逐笔: exchange=UNKNOWN
    # 8: 订阅逐笔数据, 遍历所有股票
    # 9: 订阅暗盘逐笔

    @pytest.mark.testAPI
    def test_stock_SubscribeTradeTickReqApi_001(self):
        """订阅一个股票的逐笔: frequence=None"""
        frequence = None
        exchange = SEHK_exchange
        code = "00700"
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

        if not self.common.check_trade_status(exchange):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            self.assertTrue(info_list.__len__() == 0)
        else:
            # 开市中, 持续接收5分钟数据, 直到info_list有数据
            start = time.time()
            while time.time() - start < 300:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence)) # 逐笔不限制频率
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_SubscribeTradeTickReqApi_002(self):
        """订阅一个股票的逐笔: frequence=4"""
        frequence = 4
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence)) # 逐笔不限制频率
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeTradeTickReqApi_003(self):
        """订阅2个股票的逐笔: frequence=100"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code3
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp, recv_num=50))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))
        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence)) # 逐笔不限制频率
            recv_code_list = []
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                recv_code_list.append(self.common.searchDicKV(info, 'instrCode'))
            self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeTradeTickReqApi_004(self):
        """订阅一个股票的逐笔: frequence=100, exchange=UNKNOWN"""
        frequence = 100
        exchange = 'UNKNOWN'
        code = SEHK_code8
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_SubscribeTradeTickReqApi_005(self):
        """订阅一个股票的逐笔: frequence=100, code=xxxx"""
        frequence = 100
        exchange = SEHK_exchange
        code = 'xxxx'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr code [{}] error'.format(code))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
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

    def test_stock_SubscribeTradeTickReqApi_006(self):
        """ 订阅两个股票的逐笔, 校验是否正确 """
        frequence = None
        exchange = NASDAQ_exchange
        code1 = NASDAQ_code1
        code2 = NASDAQ_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个股票的逐笔数据')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'订阅第二个股票的逐笔数据')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence)) # 逐笔不限制频率
            self.assertTrue(set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange})
            # 接收到两个股票的逐笔
            self.assertTrue(set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2})

    def test_stock_SubscribeTradeTickReqApi_007(self):
        """订阅一个股票的逐笔: frequence=100, exchange=UNKNOWN"""
        frequence = 100
        exchange = NASDAQ_exchange
        code = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        # self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr [ {}_{} ] error'.format(exchange, code))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_SubscribeTradeTickReqApi_008(self, exchange, code):
        """订阅一个股票的逐笔: frequence=None"""
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence)) # 逐笔不限制频率
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验订阅逐笔不会接收到快照数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'校验订阅逐笔不会接收到盘口数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @pytest.mark.Grey
    def test_stock_SubscribeTradeTickReqApi_009(self):
        """订阅暗盘逐笔"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        if not self.common.check_trade_status("Grey"):
            info_list = asyncio.get_event_loop().run_until_complete(
                future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
            assert info_list.__len__() == 0
        else:
            _start = time.time()
            while time.time() - _start < 300:
                info_list = asyncio.get_event_loop().run_until_complete(
                    future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
                self.logger.debug("循环内打印, 循环时间为 : {}".format(_start))
                if info_list.__len__() > 0:
                    break

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)



    # --------------------------------------------------取消订阅逐笔成交数据-------------------------------------------------------
    # 1: 港股 - 取消订阅一个股票的逐笔
    # 2: 港股 - 订阅两个股票的逐笔，再取消其中一个的股票的逐笔
    # 3: 港股 - 订阅两个股票的逐笔，再取消2个的股票的逐笔
    # 4: 港股 - 查询并订阅逐笔数据, 再取消逐笔数据
    # 5: 港股 - 订阅股票A的逐笔数据，取消订阅股票B的逐笔数据，取消失败
    # 6: 港股 - 订阅股票A的逐笔数据，取消订阅 exchange传入UNKNOWN
    # 7: 美股 - 取消订阅一个股票的逐笔
    # 8: 取消订阅暗盘逐笔

    @pytest.mark.testAPI
    def test_stock_UnsubscribeTradeTickReqApi_001(self):
        """取消订阅一个股票的逐笔"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_UnsubscribeTradeTickReqApi_002(self):
        """订阅两个股票的逐笔，再取消其中一个的股票的逐笔"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个股票的逐笔')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        self.logger.debug(u'订阅第二个股票的逐笔')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.logger.debug(u'取消订阅股票一的逐笔')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_stock_UnsubscribeTradeTickReqApi_003(self):
        """订阅两个股票的逐笔，再取消2个的股票的逐笔"""
        frequence = 100
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.logger.debug(u'取消订阅逐笔数据，并检查返回结果')
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code1)

        self.assertTrue(int(self.common.searchDicKV(
            rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_UnsubscribeTradeTickReqApi_004(self):
        """通过逐笔成交查询一个股票且订阅其逐笔，通过取消逐笔订阅取消,取消成功"""
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_UnsubscribeTradeTickReqApi_005(self):
        """订阅股票A的逐笔数据，取消订阅股票B的逐笔数据，取消失败"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_code1
        code2 = SEHK_code8
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert self.info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_UnsubscribeTradeTickReqApi_006(self):
        """订阅股票A的逐笔数据，取消订阅 exchange传入UNKNOWN"""
        frequence = 100
        exchange = SEHK_exchange
        exchange2 = 'UNKNOWN'
        code = SEHK_code8
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
            future=self.api.UnsubscribeTradeTickReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        if not self.common.check_trade_status(exchange):
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
            assert info_list.__len__() == 0
        else:
            start = time.time()
            while time.time() - start < 100:
                self.logger.debug("循环内打印 : 循环时间 {} 秒".format(str(time.time() - start)))
                info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
                if info_list.__len__() > 0:
                    break
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_UnsubscribeTradeTickReqApi_007(self, exchange, code):
        """取消订阅一个股票的逐笔"""
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

    @pytest.mark.Grey
    def test_stock_UnsubscribeTradeTickReqApi_008(self):
        """取消订阅暗盘逐笔"""
        frequence = 100
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
    # 1: 订阅手机图表数据(手机专用)--订阅一个港股
    # 2: 订阅手机图表数据(手机专用)--订阅两个港股
    # 3: 订阅手机图表数据(手机专用)--订阅一个美股
    # 4: 订阅手机图表数据(手机专用)--遍历全部股票产品
    # 5: 订阅手机图表数据(手机专用)--订阅港股指数
    # 6: 订阅手机图表数据(手机专用)--订阅暗盘
    # 7: 订阅手机图表数据(手机专用)--exchange为空
    # 8: 订阅手机图表数据(手机专用)--code 为 xxx

    @pytest.mark.testAPI
    def test_stock_StartChartDataReq_001(self):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        exchange = SEHK_exchange
        code = "00700"

        # exchange = "NASDAQ"
        # code = "AAPL"

        # exchange = "HKFE"
        # code = "HSImain"

        # exchange = "NYMEX"
        # code = "CLmain"

        # exchange = "SGX"
        # code = "CNmain"

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))

        instrName = self.common.searchDicKV(app_rsp_list, "instrName")

        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        # self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        # if self.common.searchDicKV(before_snapshot_json_list, "dataType") != "EX_INDEX" or sub_quote_type != "DELAY_QUOTE_MSG":
        if not sub_quote_type == "DELAY_QUOTE_MSG" and self.common.searchDicKV(before_snapshot_json_list, "dataType") != "EX_INDEX":
            before_orderbook_json_list = [app_rsp['orderbook']]  # 盘口
            is_before_orderbook = True
        else:
            is_before_orderbook = False

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        if is_before_orderbook:
            self.logger.debug(u'校验前盘口数据')
            self.assertTrue(before_orderbook_json_list.__len__() == 1)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=rspTimeStamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in before_orderbook_json_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            is_delay = True if sub_quote_type == "DELAY_QUOTE_MSG" else False
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp, is_delay=is_delay)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_stock_StartChartDataReq_002(self):
        """订阅手机图表数据(手机专用)--订阅一个股票，frequence=100,再订阅第二个股票"""
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅第一个股票')
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
        self.assertTrue(app_rsp['exchange'] == exchange)

        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'订阅第二个股票')
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
        self.assertTrue(app_rsp['exchange'] == exchange)

        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]

        self.logger.debug(u'校验静态数据值2')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

        self.logger.debug(u'校验前快照数据2')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)


        self.logger.debug(u'校验前盘口数据2')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)


        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            recv_code_list = []
            for info in info_list:
                recv_code_list.append(self.common.searchDicKV(info, 'instrCode'))
            self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
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

    def test_stock_StartChartDataReq_003(self):
        """订阅手机图表数据(手机专用)--订阅一个美股，frequence=null"""
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
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
        before_orderbook_json_list = [app_rsp['orderbook']]  # 盘口

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
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

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_StartChartDataReq_004(self, exchange, code):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        exchange = exchange
        code = code

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
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

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        before_orderbook_json_list = [app_rsp['orderbook']]  # 盘口

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_orderbook_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)



    @pytest.mark.allStock
    def test_stock_StartChartDataReq_005(self):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        exchange = SEHK_exchange
        code = SEHK_indexCode1

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
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

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]                # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]       # 快照数据
        assert app_rsp.get("orderbook") is None                 # 盘口

        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for info in basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=rspTimeStamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
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

    @pytest.mark.Grey
    def test_stock_StartChartDataReq_006(self):
        """订阅手机图表数据(手机专用)--订阅暗盘"""
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
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

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]  # 静态数据
        before_snapshot_json_list = [app_rsp['snapshot']]  # 快照数据
        before_orderbook_json_list = [app_rsp['orderbook']]  # 盘口

        # self.logger.debug(u'校验静态数据值')
        # self.assertTrue(basic_json_list.__len__() == 1)
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', basic_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for info in basic_json_list:
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # self.logger.debug(u'校验前快照数据')
        # self.assertTrue(before_snapshot_json_list.__len__() == 1)
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
        #                                              is_before_data=True, start_sub_time=rspTimeStamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        # for info in before_snapshot_json_list:
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # self.logger.debug(u'校验前盘口数据')
        # self.assertTrue(before_orderbook_json_list.__len__() == 1)
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
        #                                              is_before_data=True, start_sub_time=start_time_stamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        # for info in before_orderbook_json_list:
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收暗盘快照数据的接口，筛选出快照数据,并校验暗盘数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_StartChartDataReq_007(self):
        """订阅手机图表数据(手机专用)--exchange为空"""
        exchange = "UNKNOWN"
        code = SEHK_code1

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        assert info_list.__len__() == 0

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_stock_StartChartDataReq_008(self):
        """订阅手机图表数据(手机专用)--exchange为空"""
        exchange = SEHK_exchange
        code = "xxx"

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))

        rspTimeStamp = int(self.common.searchDicKV(app_rsp, 'rspTimeStamp'))    # 接口执行完成的时间
        self.assertTrue(app_rsp['code'] == code)
        assert app_rsp["exchange"] == exchange

        self.logger.debug(u'校验收不到逐笔数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'校验收不到分时数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        assert info_list.__len__() == 0

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        assert info_list.__len__() == 0



    # --------------------------------------------------取消订阅手机图表数据(手机专用)-------------------------------
    # 1:取消订阅手机图片-订阅港股,再取消订阅 
    # 2:取消订阅手机图片-订阅2个港股,取消订阅其中一个 
    # 3:取消订阅手机图片-订阅2个港股,再取消订阅两个
    # 4:取消订阅手机图片-订阅一个美股,再取消订阅 
    # 5:取消订阅手机图片-取消订阅所有股票 
    # 6:取消订阅手机图片-取消订阅暗盘 

    @pytest.mark.testAPI
    def test_stock_StopChartDataReqApi_001(self):
        """订阅一个手机图表数据,再取消订阅 """
        exchange = SEHK_exchange
        code = SEHK_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_StopChartDataReqApi_002(self):
        """订阅2个合约,取消订阅其中一个 """
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_stock_StopChartDataReqApi_003(self):
        """订阅2个合约,再取消订阅两个"""
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        self.assertTrue(app_rsp['exchange'] == exchange)

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
        self.assertTrue(app_rsp['exchange'] == exchange)

        self.logger.debug(u'通过接收所有数据的返回,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_StopChartDataReqApi_004(self):
        """美股订阅一个手机图表数据,再取消订阅 """
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @parameterized.expand([
        (ASE_exchange, ASE_code1), 
        (NYSE_exchange, NYSE_code1), 
        (NASDAQ_exchange, NASDAQ_code1), 
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_StopChartDataReqApi_005(self, exchange, code):
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    @pytest.mark.Grey
    def test_stock_StopChartDataReqApi_006(self):
        """订阅一个手机图表数据,取消暗盘订阅 """
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        frequence = None
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.AppQuoteAllApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)





    # --------------------------------------------------查询当日分时数据-------------------------------------------------------
    # 1 : 分时查询--查询并订阅港股的分时数据： isSubKLineMin = True
    # 2 : 分时查询--查询不订阅分时： isSubKLineMin = False
    # 3 : 分时查询--查询并订阅两个股票： isSubKLineMin = True
    # 4 : 分时查询--查询并订阅美股的分时数据： isSubKLineMin = True
    # 5 : 分时查询--遍历所有股票 isSubKLineMin = True
    # 6 : 分时查询--查询暗盘的当日分时
    # 7 : 分时查询--休市时, 查询并订阅, 校验订阅成功后返回的前快照数据与查询数据的最后一条一致
    # 8 : 分时查询--休市时, 查询不订阅, 校验不会返回前数据

    @pytest.mark.testAPI
    def test_stock_QueryKLineMinMsgReqApi_001(self):
        """分时查询--查询并订阅港股的分时数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = "00700"

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
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))
        self.logger.error("时间 : {}".format(time.time() - _start))

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
        query_rspTimeStamp = int(self.common.searchDicKV(query_kline_min_rsp_list[0], 'rspTimeStamp'))

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=query_rspTimeStamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_stock_QueryKLineMinMsgReqApi_002(self):
        """分时查询--查询不订阅分时： isSubKLineMin = False"""
        frequence = 100
        isSubKLineMin = False
        exchange = SEHK_exchange
        code = SEHK_code1
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

        self.assertTrue(sub_kline_min_rsp_list.__len__() == 0)

        self.logger.debug(u'检查查询返回的当日分时数据')
        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryKLineMinMsgReqApi_003(self):
        """分时查询--查询并订阅两个股票： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个股票数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code1, query_type, direct, start, end,
                                                   vol, start_time_stamp))
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code1)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'查询第二个股票数据')
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code2)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(set([self.common.searchDicKV(info, 'code') for info in info_list]) == {code1, code2})

    def test_stock_QueryKLineMinMsgReqApi_004(self):
        """分时查询--查询并订阅美股的分时数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = NASDAQ_exchange
        code = NASDAQ_code2
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    # 查询所有股票类型的数据
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_QueryKLineMinMsgReqApi_005(self, exchange, code):
        """分时查询--查询并订阅港股的分时数据： isSubKLineMin = True"""
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    @pytest.mark.Grey
    def test_stock_QueryKLineMinMsgReqApi_006(self):
        """分时查询--查询暗盘的当日分时"""
        frequence = 100
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryKLineMinMsgReqApi_007(self):
        """分时查询--查询并订阅, 校验订阅成功后返回的前快照数据与查询数据的最后一条一致"""
        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = 100
        isSubKLineMin = True
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
        before_kline_min_list = final_rsp.get("before_kline_min_list")

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

        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        self.logger.debug("校验前数据与查询的最后一个数据一致")
        assert before_kline_min_list[0]["exchange"] == exchange
        assert before_kline_min_list[0]["code"] == code
        assert info_list[-1] == before_kline_min_list[0].get("data")[0]    # 校验查询的最后一个数据与订阅返回的前数据一致

        self.logger.debug(u'检查查询返回的当日分时数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryKLineMinMsgReqApi_008(self):
        """分时查询--休市时, 查询不订阅, 校验不会返回前数据"""
        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = 100
        isSubKLineMin = False
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
        before_kline_min_list = final_rsp.get("before_kline_min_list")

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
        assert before_kline_min_list is None

        info_list = self.common.searchDicKV(query_kline_min_rsp_list[0], 'data')
        self.logger.debug(u'检查查询返回的当日分时数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=start_time_stamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)



    # --------------------------------------------------查询五日分时数据-------------------------------------------------------
    #  1: 港股, 五日分时查询, 查询并订阅数据： isSubKLineMin = True
    #  2: 港股, 五日分时查询, 查询不订阅数据： isSubKLineMin = False
    #  3: 港股, 五日分时查询： 查询两个股票的五日分时
    #  4: 美股, 五日分时查询, 查询美股： isSubKLineMin = True
    #  5: 五日分时查询, 查询并订阅数据, 遍历所有股票
    #  6: 休市时, 查询五日分时, 并订阅五日分时, 校验订阅后不会返回前数据
    #  7: 休市时, 查询五日分时, 不订阅, 校验不会返回前数据

    @pytest.mark.testAPI
    def test_stock_QueryFiveDaysKLineMinReqApi_001(self):
        """五日分时查询, 查询并订阅数据： isSubKLineMin = True"""
        frequence = None
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = SEHK_code1
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'五日分时数据查询，检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        self.logger.error("时间 : {}".format(time.time() - _start))
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

        query_rspTimeStamp = int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp'))
        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=query_rspTimeStamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_stock_QueryFiveDaysKLineMinReqApi_002(self):
        """五日分时查询, 查询不订阅数据： isSubKLineMin = False"""
        frequence = 100
        isSubKLineMin = False
        exchange = SEHK_exchange
        code = SEHK_code1
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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryFiveDaysKLineMinReqApi_003(self):
        """五日分时查询： 查询两个股票的五日分时 """
        frequence = 100
        isSubKLineMin = False
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code2
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询第一个股票的五日分时')
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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code1)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'查询第二个股票的五日分时')
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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code2)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))

        assert info_list.__len__() == 0

    def test_stock_QueryFiveDaysKLineMinReqApi_004(self):
        """五日分时查询, 查询美股： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = NYSE_exchange
        code = NYSE_code1
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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    # 查询所有类型
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_QueryFiveDaysKLineMinReqApi_005(self, exchange, code):
        """五日分时查询, 查询并订阅数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryFiveDaysKLineMinReqApi_006(self):
        """休市时, 查询五日分时, 并订阅五日分时, 校验订阅后不会返回前数据"""

        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = None
        isSubKLineMin = True
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
        before_kline_min_list = final_rsp.get("before_kline_min_list")
        self.logger.debug("校验五日分时不会返回前数据")
        # assert before_kline_min_list is None

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
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryFiveDaysKLineMinReqApi_007(self):
        """休市时, 查询五日分时, 并订阅五日分时, 校验订阅后不会返回前数据"""

        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = None
        isSubKLineMin = False
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
        before_kline_min_list = final_rsp.get("before_kline_min_list")
        self.logger.debug("校验五日分时不会返回前数据")
        assert before_kline_min_list is None
        assert sub_kline_min_rsp_list.__len__() == 0

        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'code') == code)
        self.assertTrue(
            int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'检查查询返回的五日分时数据')
        day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        # 获取五个交易日
        fiveDateList = self.common.get_fiveDays(exchange)
        self.logger.debug("五个交易日时间 : {}".format(fiveDateList))
        for i in range(len(day_data_list)):
            # 校验五日date依次递增, 遇到节假日无法校验
            assert day_data_list[i].get("date") == fiveDateList[i]
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            if info_list.__len__() > 0:
                assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                         start_sub_time=start_time_stamp, start_time=0,
                                                         exchange=exchange, instr_code=code)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        assert info_list.__len__() == 0







    # --------------------------------------------------查询历史K线-------------------------------------------------------
    #  1: 港股, K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据
    #  2: 港股, K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 不订阅K线数据
    #  3: 美股, K线查询美股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据
    #  4: 港股, K线查询港股: 按BY_DATE_TIME方式查询, 遍历所有K线频率, 不订阅K线数据
    #  5: 美股, K线查询美股: 按BY_DATE_TIME方式查询, 遍历所有K线频率, 不订阅K线数据
    #  6: 港股, K线查询港股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100
    #  7: 美股, K线查询美股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100
    #  8: 港股, K线查询港股: BY_VOL, 1分钟K，向后查询100根K线, isSubKLine = True, frequence=100
    #  9: 美股, K线查询美股: BY_VOL, 1分钟K，向后查询100根K线, isSubKLine = True, frequence=100
    #  10: K线查询港股: BY_VOL，向后查询100根K线, 遍历所有K线频率, 并订阅K线
    #  11: K线查询美股: BY_VOL, 向前查询100根K线, 遍历所有K线频率, 并订阅K线
    #  12: K线查询: 查询0根 1分钟K线, 不订阅, 提示vol错误
    #  13: K线查询: 查询两个合约的K线, 并订阅
    #  14: 查询所有种类的K线: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据
    #  15: 暗盘, K线查询: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100
    #  16: 暗盘, K线查询: 遍历所有K线频率
    #  17: 休市时, 查询最近100条K线, 并订阅K线数据, 校验订阅返回的前数据与查询的最后一条数据一致
    #  18: 休市时, 查询最近100条K线, 不订阅K线, 校验不会返回前数据

    @pytest.mark.testAPI
    def test_stock_QueryKLineMsgReqApi_001(self):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = "00700"
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        # start = start_time_stamp - 60 * 60 * 1000 * 24 * 2
        start = 1612195200000
        end = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        self.logger.debug("时间 : {}".format(time.time() - _start))
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
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    def test_stock_QueryKLineMsgReqApi_002(self):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 不订阅K线数据"""
        frequence = 100
        isSubKLine = False
        exchange = SEHK_exchange
        code = SEHK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 24
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

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0


    def test_stock_QueryKLineMsgReqApi_003(self):
        """K线查询美股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = 100
        isSubKLine = True
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 24 *2
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
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)

            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


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
    def test_stock_QueryKLineMsgReqApi_004(self, peroid_type):
        """K线查询港股: 按BY_DATE_TIME方式查询, 遍历所有K线频率, 不订阅K线数据"""
        frequence = 100
        isSubKLine = False
        exchange = SEHK_exchange
        code = "01351"
        peroid_type = peroid_type
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 24 * 60 * 60 * 1000 * 2  # 默认查询7天的K线数据
        # if peroid_type > 18:
        #     start = start_time_stamp - 24 * 60 * 60 * 1000 * 30    # 周K以上, 查询一年的数据

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

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0


    @parameterized.expand([
        (KLinePeriodType.MINUTE,),
        (KLinePeriodType.THREE_MIN,),
        (KLinePeriodType.FIVE_MIN,),
        (KLinePeriodType.FIFTEEN_MIN,),
        (KLinePeriodType.THIRTY_MIN,),
        (KLinePeriodType.HOUR,),
        (KLinePeriodType.TWO_HOUR,),
        (KLinePeriodType.FOUR_HOUR,),
        (KLinePeriodType.DAY,),     # BUG : http://jira.eddid.com.cn:18080/browse/HQZX-526
        (KLinePeriodType.WEEK,),    # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-527
        (KLinePeriodType.MONTH,),
        (KLinePeriodType.SEASON,),
        (KLinePeriodType.YEAR,)
    ])
    @pytest.mark.allStock
    def test_stock_QueryKLineMsgReqApi_005(self, peroid_type):
        """K线查询美股: 按BY_DATE_TIME方式查询, 遍历所有K线频率, 不订阅K线数据"""
        frequence = 100
        isSubKLine = False
        exchange = ASE_exchange
        code = ASE_code1
        peroid_type = peroid_type
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 24 * 60 * 60 * 1000 * 2  # 默认查询7天的K线数据
        # if peroid_type >= 18:
        #     # start = start_time_stamp - 24 * 60 * 60 * 1000 * 365    # 周K以上, 查询一年的数据
        #     start = start_time_stamp - 24 * 60 * 60 * 1000 * 30    # 周K以上, 查询一年的数据

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

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0


    def test_stock_QueryKLineMsgReqApi_006(self):
        """K线查询港股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 400
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        self.logger.debug("时间 : {}".format(time.time() - _start))
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    def test_stock_QueryKLineMsgReqApi_007(self):
        """K线查询美股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 400
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    def test_stock_QueryKLineMsgReqApi_008(self):
        """K线查询港股: BY_VOL, 1分钟K，向后查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 400
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp, is_before_data=True,
                                                     start_time=start, exchange=exchange, instr_code=code,
                                                     peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    def test_stock_QueryKLineMsgReqApi_009(self):
        """K线查询美股: BY_VOL, 1分钟K，向后查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 5 * 24 * 60 * 60 * 1000
        end = None
        vol = 400
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp, is_before_data=True,
                                                     start_time=start, exchange=exchange, instr_code=code,
                                                     peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


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
    def test_stock_QueryKLineMsgReqApi_010(self, peroid_type):
        """K线查询港股: BY_VOL，向后查询100根K线, 遍历所有K线频率"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_code1
        peroid_type = peroid_type
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 7 * 24 * 60 * 60 * 1000      # 默认7天
        # if peroid_type > 18:
        #     start = start_time_stamp - 365 * 24 * 60 * 60 * 1000      # 周K以上, 开始查询时间为一年前
        end = start_time_stamp
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
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)

        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        curTime = str(datetime.datetime.now())
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


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
    def test_stock_QueryKLineMsgReqApi_011(self, peroid_type):
        """K线查询美股: BY_VOL, 向前查询100根K线, 遍历所有K线频率, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        peroid_type = peroid_type
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    def test_stock_QueryKLineMsgReqApi_012(self):
        """K线查询: 查询0根 1分钟K线, 不订阅, 提示vol错误"""
        frequence = 100
        isSubKLine = False
        exchange = SEHK_exchange
        code = SEHK_code1
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


    def test_stock_QueryKLineMsgReqApi_013(self):
        """K线查询: 查询两个合约的K线, 并订阅"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        self.logger.debug(u'查询第一个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code1, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code1, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'查询第二个合约的K线数据')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code2, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code2)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list,
                                                     start_sub_time=start_time_stamp,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code2, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

            assert set([self.common.searchDicKV(info, 'code') for info in info_list]) == {code1, code2}


    # 查询所有类型
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_QueryKLineMsgReqApi_014(self, exchange, code):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = 100
        isSubKLine = True
        exchange = exchange
        code = code
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000 * 24 * 5  * 5
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
        peroidType = self.common.searchDicKV(query_kline_rsp_list[0], 'peroidType')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')


    @pytest.mark.Grey
    def test_stock_QueryKLineMsgReqApi_015(self):
        """K线查询港股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = None
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        peroid_type = KLinePeriodType.MINUTE
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
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange="Grey",
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list, exchange="Grey")
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

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
    @pytest.mark.Grey
    def test_stock_QueryKLineMsgReqApi_016(self, peroid_type):
        """K线查询港股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = None
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        peroid_type = peroid_type
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=start, start_time=0, exchange="Grey",
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list, exchange="Grey")
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == peroid_type)


    @pytest.mark.subBeforeData
    def test_stock_QueryKLineMsgReqApi_017(self):
        """休市时, 查询最近100条K线, 并订阅K线数据, 校验订阅返回的前数据与查询的最后一条数据一致"""

        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = N
        isSubKLine = True
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
        before_kline_list = final_rsp.get("before_kline_list")

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMzsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.logger.debug("校验订阅返回的前数据与查询结果最后一个数据一致")
        assert before_kline_list.__len__() == 1
        assert k_data_list[-1] == before_kline_list[0].get("kData")

        self.logger.debug(u'校验回包里的历史k线数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')

    @pytest.mark.subBeforeData
    def test_stock_QueryKLineMsgReqApi_018(self):
        """休市时, 查询最近100条K线, 不订阅K线, 校验不会返回前数据"""

        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = N
        isSubKLine = False
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
        before_kline_list = final_rsp.get("before_kline_list")

        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMzsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        assert sub_kline_rsp_list.__len__() == 0
        assert before_kline_list is None

        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.logger.debug(u'校验回包里的历史k线数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            self.assertTrue(info_list.__len__() == 0)
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'code') == code)
                self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')






    # --------------------------------------------------逐笔成交查询-------------------------------------------------------
    # 1, 查询逐笔成交--按日期查询, 查询5分钟的逐笔成交数据, 并订阅逐笔成交
    # 2, 查询逐笔成交--按日期查询, 查询10分钟的逐笔成交数据, 不订阅逐笔成交
    # 3, 查询逐笔成交--按日期查询--开始时间==结束时间
    # 4, 查询逐笔成交--按日期查询--开始时间大于结束时间
    # 5, 查询逐笔成交--按日期查询--开始时间为None
    # 6, 查询逐笔成交--按日期查询--结束时间为None
    # 7, 按量查询100条-向前查询-开始时间为当前时间, 结束时间为None
    # 8, 按量查询100条-向前查询-开始时间为10分钟前
    # 9, 按量查询100条-向前查询-开始时间为未来时间, 可以查询成功
    # 10, 按量查询100条-向前查询-开始时间None, 结束时间为当前时间, 可以查询成功
    # 11, 按量查询100条-向后查询-开始时间为当前时间, 结束时间为None
    # 12, 按量查询1000条-向后查询-开始时间为1分钟前, 校验不够条数时处理正常
    # 13, 按量查询100条-向后查询-开始时间为10分钟前
    # 14, 按量查询100条-向后查询-开始时间为未来时间
    # 15, 按量查询100条-向后查询-开始时间None, 结束时间为当前时间
    # 16, 按日期查询, 开始时间和结束时间都为空
    # 17, 按量查询-查询一万条数据
    # 18, 按量查询-查询数量为0
    # 19, 查询两个合约--顺便订阅
    # 20, 查询两个合约--不订阅
    # 21, 逐笔成交-不同查询方式查询两个合约, 并订阅
    # 22, 查询逐笔成交--未定义的交易所
    # 23, 查询逐笔成交--不存在的合约代码
    # 24, 查询逐笔成交--合约代码为None
    # 25, 查询逐笔成交--获取K线的方式为UNKNOWN_QUERY_KLINE
    # 26, 查询逐笔成交--获取K线的方向为UNKNOWN_QUERY_DIRECT
    # 27, 查询逐笔数据--frequence=0, 数据更新频率为默认, (8月12号, 逐笔不做过滤, 防止丢数据)
    # 28, 遍历美股和港股不同类型, 按量查询100条-向前查询-开始时间为当前时间, 结束时间为None
    # 29, 暗盘, 查询暗盘的逐笔
    # 30, 暗盘, 按量查询100条-向前查询-开始时间为5分钟前
    # 31, 查询港股逐笔成交--按时间查询, 不限制当天req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
    # 32, 查询美股逐笔成交--按时间查询, 不限制当天req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
    # 33, 港股, 按量查询100条-向前查询查询-开始时间为当前时间, 结束时间为None, 不限制当天req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
    # 34, 美股, 按量查询100条-向前查询查询-开始时间为当前时间, 结束时间为None, 不限制当天 req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
    # 35, 休市时, 查询最近100条逐笔数据, 并订阅逐笔数据, 校验订阅返回的前数据与查询的最后一条数据一致
    # 36, 休市时, 查询最近100条逐笔数据, 不订阅逐笔数据, 校验不会返回前数据

    @pytest.mark.testAPI
    def test_stock_QueryTradeTickMsgReqApi_001(self):
        """
        查询逐笔成交--查询5分钟的逐笔成交数据, 并订阅逐笔成交
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = "00700"

        # exchange = NASDAQ_exchange
        # code = NASDAQ_code1

        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按时间查询, 方向没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000 * 24
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        self.logger.debug("时间 : {}".format(time.time() - _start))
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_002(self):
        """
        查询逐笔成交--查询10分钟的逐笔成交数据, 不订阅逐笔成交
        """
        frequence = 100
        isSubTrade = False
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按日期查询, 此字段没有意义
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


        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_003(self):
        """
        查询逐笔成交--按日期查询--开始时间==结束时间
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_QueryTradeTickMsgReqApi_004(self):
        """
        查询逐笔成交--按日期查询--开始时间大于结束时间
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 5 * 60 * 1000
        end_time = start_time_stamp - 60 * 60 * 1000
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

    def test_stock_QueryTradeTickMsgReqApi_005(self):
        """
        查询逐笔成交--按日期查询--开始时间为None
        """
        frequence = 100
        isSubTrade = False
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_QueryTradeTickMsgReqApi_006(self):
        """
        查询逐笔成交--按日期查询--结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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

    def test_stock_QueryTradeTickMsgReqApi_007(self):
        """
        按量查询100条-向前查询-开始时间为当前时间, 结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        self.logger.debug("时间 : {}".format(time.time() - _start))
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_008(self):
        """
        按量查询100条-向前-开始时间为10分钟前
        """
        frequence = None
        isSubTrade = True
        exchange = NYSE_exchange
        code = "X"
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000 * 12
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

        # self.assertTrue(tick_data_list.__len__() == vol)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_009(self):
        """
        按量查询100条-向前-开始时间为未来时间, 可以查询成功
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + 60 * 60 * 1000
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_010(self):
        """
        按量查询100条-向前-开始时间None, 结束时间为当前时间, 可以查询成功
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        # code = SEHK_code1
        code = "01721"
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

        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        self.assertTrue(tick_data_list.__len__() == vol)
        rspTimeStamp = int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp'))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=rspTimeStamp, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_011(self):
        """
        按量查询100条-向后-开始时间为当前时间, 结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_012(self):
        """
        按量查询1000条-向后-开始时间为1分钟前, 校验不够条数时处理正常
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code1 = SEHK_code1
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_stock_QueryTradeTickMsgReqApi_013(self):
        """
        按量查询100条-向后-开始时间为10分钟前
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_014(self):
        """
        按量查询100条-向后-开始时间为未来时间
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + 60 * 60 * 1000
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_015(self):
        """
        按量查询100条-向后-开始时间None, 结束时间为当前时间
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_016(self):
        """
        按日期查询, 开始时间和结束时间都为空
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_017(self):
        """
        按量查询-查询一万条数据
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_stock_QueryTradeTickMsgReqApi_018(self):
        """
        按量查询-查询数量为0
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_019(self):
        """
        查询两个合约--顺便订阅
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            assert set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2}
            assert set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange}

    def test_stock_QueryTradeTickMsgReqApi_020(self):
        """
        查询两个合约--不订阅
        """
        frequence = 100
        isSubTrade = False
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_021(self):
        """
        逐笔成交-不同查询方式查询两个合约, 并订阅
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code8
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time1, start_time=0, exchange=exchange)
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time2, start_time=start_time2, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.assertTrue(self.common.checkFrequence(info_list, frequence))

        assert set([self.common.searchDicKV(info, "instrCode") for info in info_list]) == {code1, code2}
        assert set([self.common.searchDicKV(info, "exchange") for info in info_list]) == {exchange}

    def test_stock_QueryTradeTickMsgReqApi_022(self):
        """
        查询逐笔成交--未定义的交易所
        """
        frequence = 100
        isSubTrade = True
        exchange = "UNKNOWN"
        code = SEHK_code1
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_023(self):
        """
        查询逐笔成交--不存在的合约代码
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_024(self):
        """
        查询逐笔成交--合约代码为None
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_025(self):
        """
        查询逐笔成交--获取K线的方式为UNKNOWN_QUERY_KLINE
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_026(self):     # BUG : 查询失败, 订阅成功了
        """
        查询逐笔成交--获取K线的方向为UNKNOWN_QUERY_DIRECT
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
            future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryTradeTickMsgReqApi_027(self):
        """
        查询逐笔数据--frequence=0, 数据更新频率为默认 (8月12号, 逐笔不做过滤, 防止丢数据)
        """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        if not selc.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    # 查询所有类型
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数不支持交易, 没有逐笔数据
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_QueryTradeTickMsgReqApi_028(self, exchange, code):
        """
        遍历美股和港股不同类型, 按量查询100条-向前查询-开始时间为当前时间, 结束时间为None
        """
        frequence = 100
        isSubTrade = True
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
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

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    @pytest.mark.Grey
    def test_stock_QueryTradeTickMsgReqApi_029(self):
        """
        查询暗盘的逐笔
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
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

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))
        if not self.common.check_trade_status("Grey"):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @pytest.mark.Grey
    def test_stock_QueryTradeTickMsgReqApi_030(self):
        """
        按量查询100条-向前-开始时间为5分钟前, 查询暗盘

        """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteTradeDataApi(recv_num=100, recv_timeout_sec=19))
        if not self.common.check_trade_status("Grey"):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_stock_QueryTradeTickMsgReqApi_031(self):
        """
        查询港股逐笔成交--按时间查询, 不限制当天
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按时间查询, 方向没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000 * 48
        end_time = start_time_stamp
        vol = None
        req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp, req_hisdata_type=req_hisdata_type))
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_stock_QueryTradeTickMsgReqApi_032(self):
        """
        查询美股逐笔成交--按时间查询, 不限制当天
        """
        frequence = 100
        isSubTrade = True
        exchange = ASE_exchange
        code = ASE_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = None  # 按时间查询, 方向没有意义
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 60 * 60 * 1000 * 48
        end_time = start_time_stamp
        vol = None
        req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp, req_hisdata_type=req_hisdata_type))
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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=end_time, start_time=start_time)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_stock_QueryTradeTickMsgReqApi_033(self):
        """
        港股, 按量查询100条-向前查询-开始时间为当前时间, 结束时间为None, 不限制当天
        """
        frequence = 100
        isSubTrade = True
        exchange = SEHK_exchange
        code = SEHK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 1000
        req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp, req_hisdata_type=req_hisdata_type))
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

        self.assertTrue(tick_data_list.__len__() > 0)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


    def test_stock_QueryTradeTickMsgReqApi_034(self):
        """
        美股, 按量查询100条-向前查询-开始时间为当前时间, 结束时间为None, 不限制当天
        """
        frequence = 100
        isSubTrade = True
        exchange = ASE_exchange
        code = ASE_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 1000
        req_hisdata_type = "NOT_CUR_TRADEDATE_DATA"
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp, req_hisdata_type=req_hisdata_type))
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

        self.assertTrue(tick_data_list.__len__() > 0)
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryTradeTickMsgReqApi_035(self):
        """
        休市时, 查询最近100条逐笔数据, 并订阅逐笔数据, 校验订阅返回的前数据与查询的最后一条数据一致
        """
        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = None
        isSubTrade = True
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
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
        before_tickdata_list = final_rsp.get("before_tickdata_list")    # 前数据

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

        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)
        self.logger.debug("休市时, 校验前数据与查询结果的最后一个数据一致")
        assert tick_data_list[-1] == before_tickdata_list[0].get("tradeTick")

        self.logger.debug(u'校验回包里的历史逐笔数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    @pytest.mark.subBeforeData
    def test_stock_QueryTradeTickMsgReqApi_036(self):
        """
        休市时, 查询最近100条逐笔数据, 不订阅逐笔数据, 校验不会返回前数据
        """
        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code3

        if not self.common.check_trade_status(exchange1):
            exchange = exchange1
            code = code1
        elif not self.common.check_trade_status(exchange2):
            exchange = exchange2
            code = code2
        else:
            raise Exception("交易时间有问题了")

        frequence = None
        isSubTrade = False
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
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
        before_tickdata_list = final_rsp.get("before_tickdata_list")    # 前数据

        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        assert sub_trade_tick_rsp_list.__len__() == 0
        assert before_tickdata_list is None

        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_APP_BeforeQuoteTradeData', tick_data_list,
                                                     start_sub_time=start_time, start_time=0, exchange=exchange)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        curTime = str(datetime.datetime.now())
        self.logger.debug("接收数据的时间为 : {}".format(curTime))

        if not self.common.check_trade_status(exchange):
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

            inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            for info in info_list:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)






    # --------------------------------------------------查询股票交易状态------------------------------------------------
    # 1: 查询股票交易状态--港股product_list为空，查询全部港股的交易状态
    # 2: 查询股票交易状态--港股, 查询两个股票的状态
    # 3: 查询股票交易状态--exchange为UNKNOWN
    # 4: 查询股票交易状态--product_list包含一个错误产品代码
    # 5: 查询股票交易状态--美股ASE  product_list为空，则返回所有数据
    # 6: 查询股票交易状态--美股NYSE  product_list为空，则返回所有数据
    # 7: 查询股票交易状态--美股NASDAQ product_list为空，则返回所有数据
    # 8: 查询股票交易状态--美股BATS product_list为空，则返回所有数据
    # 9: 查询股票交易状态--美股IEX product_list为空，则返回所有数据
    # 10: 查询股票交易状态-- 查询两个美股的交易状态
    # 11: 查询股票交易状态--遍历所有股票
    # 12: 查询股票交易状态--查询暗盘

    @pytest.mark.testAPI
    def test_stock_QueryTradeStatusMsgReqApi_001(self):
        """港股product_list为空，查询全部港股的交易状态"""
        start_time_stamp = int(time.time() * 1000)
        exchange = SEHK_exchange
        product_list = ["00700"]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        datas = first_rsp_list[0]['data']
        # self.assertTrue(datas.__len__() > 10000)
        for data in datas:
            self.logger.debug(data)
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_002(self):
        """港股, 查询两个股票的状态"""
        start_time_stamp = int(time.time() * 1000)
        exchange = SEHK_exchange
        product_list = ['00700', '00001']
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
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_003(self):
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

    def test_stock_QueryTradeStatusMsgReqApi_004(self):
        """product_list包含一个错误产品代码"""
        start_time_stamp = int(time.time() * 1000)
        exchange = SEHK_exchange
        product_list = ['00700', '00001', 'xxx']
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
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_005(self):
        """美股ASE  product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = ASE_exchange
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
        self.assertTrue(datas.__len__() > 100)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_006(self):
        """美股NYSE  product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = NYSE_exchange
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
        self.assertTrue(datas.__len__() > 100)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_007(self):
        """美股NASDAQ product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = NASDAQ_exchange
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
        self.assertTrue(datas.__len__() > 100)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_008(self):
        """美股BATS product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = BATS_exchange
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
        self.assertTrue(datas.__len__() > 100)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_009(self):
        """美股IEX product_list为空，则返回所有数据"""
        start_time_stamp = int(time.time() * 1000)
        exchange = IEX_exchange
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
        self.assertTrue(datas.__len__() > 100)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    def test_stock_QueryTradeStatusMsgReqApi_010(self):
        """查询两个美股的交易状态"""
        start_time_stamp = int(time.time() * 1000)
        exchange = NASDAQ_exchange
        product_list = ['AAPL', 'BABA']
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
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    # 查询所有类型
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    @pytest.mark.allStock
    def test_stock_QueryTradeStatusMsgReqApi_011(self, exchange, code):
        """遍历所有股票"""
        start_time_stamp = int(time.time() * 1000)
        exchange = exchange
        product_list = [code]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        datas = first_rsp_list[0]['data']
        # self.assertTrue(datas.__len__() > 10000)
        for data in datas:
            self.logger.debug(data)
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if self.common.check_trade_status(exchange):
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"

    @pytest.mark.Grey
    def test_stock_QueryTradeStatusMsgReqApi_012(self):
        """查询暗盘"""
        start_time_stamp = int(time.time() * 1000)
        exchange = SEHK_exchange
        product_list = [SEHK_greyMarketCode1]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list))

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        datas = first_rsp_list[0]['data']
        # self.assertTrue(datas.__len__() > 10000)
        self.logger.info(int(time.strftime("%H%M%S")))
        for data in datas:
            self.logger.debug(data)
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']
            # 判断在交易中
            if 161500 <= int(time.strftime("%H%M%S")) <= 183000:
                assert status == "TRADE_TRADING"
            else:
                assert status == "TRADE_SUSPEND"





    # --------------------------------------------------查询板块接口(证券专用)------------------------------------------------
    # 1: 查询港股主板, 降序查询, 并订阅快照数据
    # 2: 查询港股主板, 降序查询, 不订阅快照数据
    # 3: 查询港股主板, 升序, 并订阅快照数据
    # 4: 查询港股所有版块, 降序查询, 不订阅快照数据
    # 5: 查询美股中概股板(CHINA_CONCEPT_STOCK), 降序查询, 并订阅快照数据
    # 6: 查询美股明星版(START_STOCK), 降序查询, 并订阅快照数据
    # 7: 查询港股主板, 降序查询, 查询1000条数据
    # 8: 查询港股主板, 降序查询, 其中zone字段为空
    # 9: 查询港股主板, 降序查询, 其中版块plate_type为空
    # 10: 查询版块信息, 其中zone和plate_type 不匹配
    # 11: 查询港股主板, 降序查询, 其中查询方向为空
    # 12: 查询港股主板, 降序查询, 其中count 为0

    @pytest.mark.testAPI
    def test_stock_QueryPlateSortMsgReq_001(self):
        """查询港股主板, 升序查询, 并订阅快照数据 """
        frequence = None
        isSubTrade = True
        zone = "HK"
        plate_type = "MAIN"
        sort_direct = "DESCENDING_ORDER"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            self.logger.debug(rsp["info"][i])
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=count))
        if not self.common.check_trade_status(SEHK_exchange if zone=="HK" else NASDAQ_exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    def test_stock_QueryPlateSortMsgReq_002(self):
        """查询港股主板, 升序查询, 不订阅快照数据 """
        frequence = None
        isSubTrade = False
        zone = "HK"
        plate_type = "MAIN"
        sort_direct = "DESCENDING_ORDER"
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_stock_QueryPlateSortMsgReq_003(self):
        """查询港股主板, 降序, 并订阅快照数据 """
        frequence = None
        isSubTrade = True
        zone = "HK"
        plate_type = "MAIN"
        sort_direct = "ASCENDING_ORDER"
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        # self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        # self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        # self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        # self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == PlateType.Name(plate_type))    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(SEHK_exchange if zone=="HK" else NASDAQ_exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    @parameterized.expand([
        ("LISTED_NEW_SHARES",) ,    # 已上市新股
        ("RED_SHIPS",) ,            # 红筹股
        ("ETF",) ,      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-466
        ("GME",) ,                  # 创业板
    ])
    @pytest.mark.allStock
    def test_stock_QueryPlateSortMsgReq_004(self, plate_type):
        """查询港股所有版块, 升序查询, 不订阅快照数据 """
        frequence = None
        isSubTrade = False
        zone = "HK"
        plate_type = plate_type
        sort_direct = "DESCENDING_ORDER"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        # assert rsp["info"].__len__() == count
        # assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(rsp["info"].__len__()):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            # assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(rsp["info"].__len__()):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', rsp['snapshotData'],
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)


    def test_stock_QueryPlateSortMsgReq_005(self):
        """查询美股中概股板(CHINA_CONCEPT_STOCK), 升序查询, 并订阅快照数据 """
        frequence = None
        isSubTrade = True
        zone = "US"
        plate_type = "CHINA_CONCEPT_STOCK"
        sort_direct = "DESCENDING_ORDER"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(rsp["info"].__len__()):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(rsp["info"].__len__()):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(SEHK_exchange if zone=="HK" else NASDAQ_exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryPlateSortMsgReq_006(self):
        """查询美股明星板(START_STOCK), 升序查询, 并订阅快照数据 """
        frequence = None
        isSubTrade = True
        zone = "US"
        plate_type = "START_STOCK"
        sort_direct = "DESCENDING_ORDER"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(rsp["info"].__len__()):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(rsp["info"].__len__()):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(SEHK_exchange if zone=="HK" else NASDAQ_exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            # self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

    @parameterized.expand([
        ("HK", "MAIN") ,                  # 主板
        ("HK", "LISTED_NEW_SHARES") ,    # 已上市新股
        ("HK", "RED_SHIPS") ,            # 红筹股
        ("HK", "ETF") ,      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-466
        ("HK", "GME") ,                  # 创业板
        ("US", "START_STOCK") ,          # 明星版
        ("US", "CHINA_CONCEPT_STOCK") ,     # 中概版
    ])
    @pytest.mark.allStock
    def test_stock_QueryPlateSortMsgReq_007(self, zone, plate_type):  # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-507
        """查询港股主板, 升序查询, 遍历所有版块, 查询100000条数据 """
        frequence = None
        isSubTrade = False
        zone = zone
        plate_type = plate_type
        sort_direct = "DESCENDING_ORDER"
        count = 100000
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465


        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(rsp["info"].__len__()):
            # self.logger.debug(rsp["info"][i])
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验版块信息根据涨跌排序")
        for i in range(rsp["info"].__len__()):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    def test_stock_QueryPlateSortMsgReq_008(self):
        """查询港股主板, 升序查询, 其中zone字段为空 """
        frequence = None
        isSubTrade = False
        zone = "UNKNOWN_ZONE"
        plate_type = "MAIN"
        sort_direct = "DESCENDING_ORDER"
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465


    def test_stock_QueryPlateSortMsgReq_009(self):
        """查询港股主板, 升序查询, 其中版块plate_type为空 """
        frequence = None
        isSubTrade = False
        zone = "HK"
        plate_type = "UNKNOWN_SUB_CHILD"
        sort_direct = "DESCENDING_ORDER"
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465


    def test_stock_QueryPlateSortMsgReq_010(self):
        """查询版块信息, 其中zone和plate_type 不匹配 """
        frequence = None
        isSubTrade = False
        zone = "US"
        plate_type = "MAIN"
        sort_direct = "DESCENDING_ORDER"
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465


    def test_stock_QueryPlateSortMsgReq_011(self):
        """查询港股主板, 升序查询, 其中查询方向为空 """
        frequence = None
        isSubTrade = False
        zone = "HK"
        plate_type = "MAIN"
        sort_direct = 0
        count = 10
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465


    def test_stock_QueryPlateSortMsgReq_012(self):
        """查询港股主板, 升序查询, 其中count 为0 """
        frequence = None
        isSubTrade = False
        zone = "HK"
        plate_type = "MAIN"
        sort_direct = "DESCENDING_ORDER"
        count = 0
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone, plate_type=plate_type,
                                                    sort_direct=sort_direct, count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验板块股票查询的回包')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'zone') == zone)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465
        self.assertTrue(self.common.searchDicKV(rsp, 'plateType') == plate_type)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-465





    # ---------------------------------------查询交易所股票排序查询接口(证券专用)------------------------------------------------
    # 1: 查询交易所股票排序, 按PE_RATIO 市盈率(静)排列, 并订阅快照
    # 2: 查询交易所股票排序, 按PE_RATIO 市盈率(静)排列, 不订阅快照
    # 3: 查询交易所股票排序, 港股, 遍历排序方式, 并订阅快照
    # 4: 查询美股的股票排序, 按涨跌排序(美股只支持涨跌排序), 并订阅数据
    # 5: 查询交易所股票排序,  交易所为空
    # 6: 查询交易所股票排序,  排序字段为空
    # 7: 查询交易所股票排序,  其中count为0

    @pytest.mark.testAPI
    def test_stock_QueryExchangeSortMsgReq_001(self):
        """查询交易所股票排序, 按PE_RATIO 市盈率(静)排列, isSubTrade=True """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        sortFiled = "PE_RATIO"
        count = 40
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(self.common.searchDicKV(rsp, 'sortFiled') == sortFiled)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            # assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验交易所股票排序顺序--降序排序")
        for i in range(rsp["snapshotData"].__len__()):
            self.logger.debug(rsp["snapshotData"][i])
            pass
            if i == 0:
                continue
            _first = int(self.common.searchDicKV(rsp["snapshotData"][i-1], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            _second = int(self.common.searchDicKV(rsp["snapshotData"][i], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            assert _first >= _second

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=count))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryExchangeSortMsgReq_002(self):
        """查询交易所股票排序, 按PE_RATIO 市盈率(静)排列, isSubTrade=True """
        frequence = None
        isSubTrade = False
        exchange = SEHK_exchange
        sortFiled = "PE_RATIO"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(self.common.searchDicKV(rsp, 'sortFiled') == sortFiled)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验交易所股票排序顺序--降序排序")
        for i in range(rsp["snapshotData"].__len__()):
            pass
            if i == 0:
                continue
            _first = int(self.common.searchDicKV(rsp["snapshotData"][i-1], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            _second = int(self.common.searchDicKV(rsp["snapshotData"][i], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            assert _first >= _second

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)


    @parameterized.expand([
        ("PE_RATIO",) ,               # 市盈率(静)=静态市盈率
        ("PE_TTM_RATIO",) ,           # 市盈率(TTM)=滚动市盈率
        ("PB_RATIO",) ,               # 市净率, BUG, 没有返回字段
        ("DIVIDEND_RATIO_TTM",) ,     # 股息率(TTM)
        ("DIVIDEND_RATIO_LFY",) ,     # 股息率(LFY)
        ("R_F_RATIO",) ,              # 涨跌幅, 港股不支持涨跌排序
        ("RISE_FALL", ),              # 涨跌额
        ("TURNOVER", ),               # 成交金额, BUG
        ("TURNOVER_RATE", ),          # 换手率
        ("QUANTITY_RATIO", ),         # 量比
        ("AMPLITUDE", ),              # 振幅
        ("COMMITTEE", ),              # 委比
        ("LAST_PRICE", ),             # 最新价
    ])
    @pytest.mark.allStock
    def test_stock_QueryExchangeSortMsgReq_003(self, sortFiled):
        """查询交易所股票排序, 港股, 遍历排序方式, 不订阅快照 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        sortFiled = sortFiled
        count = 200
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(self.common.searchDicKV(rsp, 'sortFiled') == sortFiled)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            self.logger.debug(rsp["info"][i])
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验交易所股票排序顺序--降序排序")
        for i in range(rsp["snapshotData"].__len__()):
            pass
            if i == 0:
                continue
            _first = int(self.common.searchDicKV(rsp["snapshotData"][i-1], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            _second = int(self.common.searchDicKV(rsp["snapshotData"][i], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            assert _first >= _second

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, 
                                                                start_sub_time=int(time.time() * 1000), is_before_data=True)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    @parameterized.expand([
        (ASE_exchange, ),
        (NYSE_exchange, ),
        (NASDAQ_exchange, ),
    ])
    @pytest.mark.allStock
    def test_stock_QueryExchangeSortMsgReq_004(self, us_exchange):
        """查询美股的股票排序, 美股只支持涨跌排序, 并订阅数据 """
        frequence = None
        isSubTrade = True
        exchange = us_exchange
        sortFiled = "R_F_RATIO"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(self.common.searchDicKV(rsp, 'sortFiled') == sortFiled)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")
            # assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            # assert  rsp["info"][i].get("cnFullName")        # BUG
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            # assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验交易所股票排序顺序--降序排序")
        for i in range(rsp["snapshotData"].__len__()):
            self.logger.debug(rsp["snapshotData"][i])
            pass
            if i == 0:
                continue
            _first = int(self.common.searchDicKV(rsp["snapshotData"][i-1], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            _second = int(self.common.searchDicKV(rsp["snapshotData"][i], self.common.to_LowerCamelcase(sortFiled.lower())) or 0)
            assert _first >= _second

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            self.assertTrue(info_list.__len__() > 0)
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryExchangeSortMsgReq_005(self):
        """查询交易所股票排序,  交易所为空"""
        frequence = None
        isSubTrade = True
        exchange = "UNKNOWN"
        sortFiled = "PE_RATIO"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))



    def test_stock_QueryExchangeSortMsgReq_006(self):
        """查询交易所股票排序,  排序字段为空 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        sortFiled = "UNKNOWN_QUERY_FILED"
        count = 100
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474


    def test_stock_QueryExchangeSortMsgReq_007(self):
        """查询交易所股票排序,  其中count为0 """
        frequence = None
        isSubTrade = False
        exchange = SEHK_exchange
        sortFiled = "PE_RATIO"
        count = 0
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled=sortFiled,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验交易所股票排序查询接口信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474
        self.assertTrue(self.common.searchDicKV(rsp, 'sortFiled') == sortFiled)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-474





    # -------------------------------------- 查询指数成份股接口(证券专用)------------------------------------------------
    # 1: 查询港股指数成分股, 降序排序, 并订阅快照
    # 2: 查询港股指数成分股, 不订阅快照
    # 3: 查询港股指数成分股, 升序排序, 并订阅快照
    # 4: 查询 恒生中国企业指数成分股, 升序排序, 并订阅快照
    # 5: 查询港股指数成分股, 输入非指数
    # 6: 查询港股指数成分股, 输入美股数据
    # 7, 查询1000个指数成分股

    @pytest.mark.testAPI
    def test_stock_QueryIndexShareMsgReq_001(self): # 指数成分股只支持港股
        """查询港股指数成分股, 升序排序, 并订阅快照 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        indexCode = SEHK_indexCode2
        sort_direct = "DESCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验指数成分股按涨跌排序")
        for i in range(count):                              # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-592
            self.logger.info(rsp["snapshotData"][i])
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryIndexShareMsgReq_002(self): # 指数成分股只支持港股
        """查询港股指数成分股, 不订阅快照 """
        frequence = None
        isSubTrade = False
        exchange = SEHK_exchange
        indexCode = SEHK_indexCode1
        sort_direct = "DESCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验指数成分股按涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryIndexShareMsgReq_003(self): # 指数成分股只支持港股
        """查询港股指数成分股, 降序排序, 并订阅快照 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        indexCode = SEHK_indexCode1
        sort_direct = "ASCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验指数成分股按涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))

        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryIndexShareMsgReq_004(self): # 指数成分股只支持港股
        """查询 恒生中国企业指数 成分股, 升序排序, 并订阅快照 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        indexCode = SEHK_indexCode1
        sort_direct = "DESCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476

        assert rsp["info"].__len__() == count
        assert rsp["snapshotData"].__len__() == count

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(count):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验指数成分股按涨跌排序")
        for i in range(count):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))

        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


    def test_stock_QueryIndexShareMsgReq_005(self): # 指数成分股只支持港股
        """查询港股指数成分股, 输入非指数 """
        frequence = None
        isSubTrade = False
        exchange = SEHK_exchange
        indexCode = SEHK_code1
        sort_direct = "DESCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476


    def test_stock_QueryIndexShareMsgReq_006(self): # 指数成分股只支持港股
        """查询港股指数成分股, 输入美股数据 """
        frequence = None
        isSubTrade = False
        exchange = NASDAQ_exchange
        indexCode = NASDAQ_code1
        sort_direct = "DESCENDING_ORDER"
        count = 20
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'FAILURE')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476


    def test_stock_QueryIndexShareMsgReq_007(self): # 指数成分股只支持港股
        """查询港股指数成分股, 升序排序, 并订阅快照 """
        frequence = None
        isSubTrade = True
        exchange = SEHK_exchange
        indexCode = SEHK_indexCode1
        sort_direct = "DESCENDING_ORDER"
        count = 1000
        start_time_stamp = int(time.time() * 1000)

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct=sort_direct, indexCode=indexCode,
                                                    count=count, start_time_stamp=start_time_stamp, recv_num=2 + count*3))

        self.logger.debug(u'校验指数成分股信息')
        self.assertTrue(rsp_list.__len__() == 1)
        rsp = rsp_list[0]
        self.assertTrue(self.common.searchDicKV(rsp, 'retCode') == 'SUCCESS')   # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(int(self.common.searchDicKV(rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp, 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp, 'exchange') == exchange)   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476
        self.assertTrue(self.common.searchDicKV(rsp, 'indexCode') == indexCode)    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-476

        assert rsp["info"].__len__() == rsp["snapshotData"].__len__()

        self.logger.info("校验info和snapshotData的数据排序一致")
        for i in range(rsp["info"].__len__()):
            assert rsp["info"][i].get("instrCode") == self.common.searchDicKV(rsp["snapshotData"][i], "instrCode")
            assert rsp["info"][i].get("exchange") == self.common.searchDicKV(rsp["snapshotData"][i], "exchange")

            assert  rsp["info"][i].get("cnSimpleName")
            # assert  rsp["info"][i].get("tcSimpleName")    # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enSimpleName")
            assert  rsp["info"][i].get("cnFullName")
            # assert  rsp["info"][i].get("tcFullName")      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-477
            assert  rsp["info"][i].get("enFullName")
            assert  rsp["info"][i].get("settleCurrency")
            assert  rsp["info"][i].get("tradeCurrency")

        self.logger.info("校验指数成分股按涨跌排序")
        for i in range(rsp["snapshotData"].__len__()):
            if i == 0:
                continue
            if sort_direct == "ASCENDING_ORDER":    # 升序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) <= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

            if sort_direct == "DESCENDING_ORDER":   # 降序
                pass
                assert int(self.common.searchDicKV(rsp["snapshotData"][i-1], "rFRatio") or 0) >= int(self.common.searchDicKV(rsp["snapshotData"][i], "rFRatio") or 0)

        self.logger.info("ZMQ 校验快照数据")
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot',
                                                            rsp['snapshotData'],
                                                            is_before_data=True,
                                                            start_sub_time=int(self.common.searchDicKV(rsp, 'rspTimeStamp')))
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'接收并校验实时快照')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        if not self.common.check_trade_status(exchange):
            assert info_list.__len__() == 0
        else:
            inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(self.common.checkFrequence(info_list, frequence))
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)






    # -------------------------------------- 查询BMP-分时数据 ------------------------------------------------
    # 1: 查询BMP分时, 不订阅 -- 可以查询到最新数据, 不会推送消息
    # 2: 查询BMP分时, 并订阅行情 -- 可以查询到最新数据, 不会推送数据
    # 3: 

    def test_stock_BMP_QueryKLineMinMsgReqApi_001(self):
        """查询BMP分时, 不订阅 -- 可以查询到最新数据, 不会推送消息"""
        frequence = None
        isSubKLineMin = False
        exchange = SEHK_exchange
        code = SEHK_code1


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
            assert self.common.searchDicKV(info_list[-1], "updateDateTime")[:-2] == self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=query_rspTimeStamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        assert info_list.__len__() == 0


    def test_stock_BMP_QueryKLineMinMsgReqApi_002(self):
        """查询BMP分时, 并订阅行情 -- 可以查询到最新数据, 不会推送数据"""
        frequence = None
        isSubKLineMin = True
        exchange = SEHK_exchange
        code = SEHK_code1

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
            assert self.common.searchDicKV(info_list[-1], "updateDateTime")[:-2] == self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=query_rspTimeStamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        assert info_list.__len__() == 0

    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    def test_stock_BMP_QueryKLineMinMsgReqApi_003(self, exchange, code):
        """查询BMP分时, 不订阅 -- 可以查询到最新数据, 不会推送消息"""
        frequence = None
        isSubKLineMin = False
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
            assert self.common.searchDicKV(info_list[-1], "updateDateTime")[:-2] == self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_06_PushKLineMinData', info_list, is_before_data=True,
                                                     start_sub_time=query_rspTimeStamp, start_time=0,
                                                     exchange=exchange, instr_code=code)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)


        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        assert info_list.__len__() == 0








    # -------------------------------------- 查询BMP-K线 ------------------------------------------------
    # 1: 查询BMP-K线数据, 不订阅, 可以查询到最新数据, 没有推送数据
    # 2: 查询BMP-按时间查询--K线数据, 并订阅K线, 可以查询到最新数据, 没有推送数据
    # 3: 查询BMP-按数量查询--K线数据, 并订阅K线, 可以查询到最新数据, 没有推送数据
    @parameterized.expand([
        (ASE_exchange, ASE_code1),
        (NYSE_exchange, NYSE_code1),
        (NASDAQ_exchange, NASDAQ_code1),
        (SEHK_exchange, SEHK_indexCode1),       # 指数
        (SEHK_exchange, SEHK_TrstCode1),        # 信托
        (SEHK_exchange, SEHK_WarrantCode1),     # 涡轮
        (SEHK_exchange, SEHK_CbbcCode1),        # 牛熊
        (SEHK_exchange, SEHK_InnerCode1),       # 界内
    ])
    def test_stock_BMP_QueryKLineMsgReqApi_001(self, exchange, code):
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

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_stock_BMP_QueryKLineMsgReqApi_002(self):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = 100
        isSubKLine = True
        exchange = SEHK_exchange
        code = SEHK_code1
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
            assert self.common.searchDicKV(k_data_list[-1], "KLineKey")[:-2] == self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, is_before_data=True,
                                                     start_sub_time=end, start_time=start, exchange=exchange,
                                                     instr_code=code, peroid_type=peroidType)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0

    def test_stock_BMP_QueryKLineMsgReqApi_003(self):
        """K线查询港股: BY_VOL, 1分钟K，向前查询100根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = False
        exchange = SEHK_exchange
        code = SEHK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp
        end = None
        vol = 80
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        _start = time.time()
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        self.logger.debug("时间 : {}".format(time.time() - _start))
        query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        sub_kline_rsp_list = final_rsp['sub_kline_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        # self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        assert sub_kline_rsp_list.__len__() == 0

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')

        if self.common.check_trade_status(exchange, code):
            assert self.common.searchDicKV(k_data_list[-1], "KLineKey")[:-2] == self.common.formatStamp(start_time_stamp, fmt="%Y%m%d%H%M")

        inner_test_result = self.inner_stock_zmq_test_case('test_stock_07_PushKLineData', k_data_list, start_sub_time=start,
                                                     is_before_data=True, start_time=0, exchange=exchange,
                                                     instr_code=code, peroid_type=peroid_type)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
        assert info_list.__len__() == 0















    # ------------------------------------------- 下面是调试接口, 可以忽略 ----------------------------------------
    # 临时校验快照数据
    # @parameterized.expand(get_all_instrCode())
    def test_all_stock_preclose(self, exchange, code):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        # exchange = "HKFE"
        # code = "MHImain"

        exchange = exchange
        code = code

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        basic = app_rsp['basicData']  # 静态数据
        snapshot = app_rsp['snapshot']  # 快照数据
        orderbook = app_rsp.get("orderbook")  # 盘口

        if orderbook:
            bid_vol = int(orderbook["orderBook"].get("bidVol") or 0)     # 盘口买盘数量
            ask_vol = int(orderbook["orderBook"].get("askVol") or 0)     # 盘口卖盘数量

        searchDicKV = lambda dic, keys: int(self.common.searchDicKV(dic, keys) or 0)

        try:
            self.logger.warning(searchDicKV(basic, "preClose"))
            self.logger.warning(searchDicKV(snapshot, "preclose"))
            assert searchDicKV(basic, "preClose") == searchDicKV(snapshot, "preclose")      # 校验静态数据的昨收价等于快照数据的昨收价
        except Exception as e:
            self.logger.error("昨收价不一致, exchange: {}, code: {}, basic --> {}, snapshot --> {}, 快照时间: {}".format(
                exchange, code, searchDicKV(basic, "preClose"), searchDicKV(snapshot, "preclose"), 
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(searchDicKV(snapshot, "sourceUpdateTime")) / pow(10, 9) )) ))

            raise e


        # if snapshot.get("dataType") == "EX_STOCK":
        #     # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
        #     assert searchDicKV(snapshot, 'amplitude') == round((int(snapshot["high"]) - int(snapshot["low"])) / searchDicKV(snapshot, 'preclose') * 100 * pow(10, 2))

        #     # 委比=(委买手数-委卖手数)/(委买手数+委卖手数)*100% 
        #     # assert searchDicKV(snapshot, 'committee') - round((bid_vol - ask_vol) / (bid_vol + ask_vol) * 100 * pow(10, 2))
        #     # 判断误差不超过30, 因为委托实时变化
        #     assert abs(searchDicKV(snapshot, 'committee') - round((bid_vol - ask_vol) / (bid_vol + ask_vol) * 100 * pow(10, 2))) < 30

        #     # 量比=(现成交总手数/现累计开市时间(分))/过去5日平均每分钟成交量 (过去5日平均每分钟成交量 无法计算)
        #     pass

        #     # 总市值=总股本*最新价
        #     # assert searchDicKV(snapshot, 'totalMarketVal') == searchDicKV(basic, 'issuedShares') * searchDicKV(snapshot, 'last') / pow(10, 3)
        #     # 判断误差不超过1
        #     assert abs(searchDicKV(snapshot, 'totalMarketVal') - searchDicKV(basic, 'issuedShares') * searchDicKV(snapshot, 'last') / pow(10, 3)) < 1

        #     # 港股市值=香港普通股股本*最新价
        #     # assert searchDicKV(snapshot, 'circularMarketVal') == searchDicKV(basic, 'outstandingShares') * searchDicKV(snapshot, 'last') / pow(10, 3)
        #     # 判断误差不超过1
        #     assert abs(searchDicKV(snapshot, 'circularMarketVal') - searchDicKV(basic, 'outstandingShares') * searchDicKV(snapshot, 'last') / pow(10, 3)) < 1

        #     # 换手率=成交量/已发行总股数×100%
        #     assert searchDicKV(snapshot, 'turnoverRate') == round(searchDicKV(snapshot, 'volume') / searchDicKV(basic, 'issuedShares') * 100 * pow(10, 2))

        #     # 溢价--认购证&牛证的溢价＝（最新价×换股比率＋行使价－相关资产最新价）/相关资产最新价×100％
        #     pass

        #     # 溢价--认沽证&熊证的溢价＝（最新价×换股比率－行使价＋相关资产最新价）/相关资产最新价×100％
        #     pass

        # if snapshot.get("dataType") == "EX_INNER":
        #     # 杠杆比率 = 1 / 最新价
        #     assert searchDicKV(snapshot, "leverageRatio")/pow(10, 4) == round(1 / (searchDicKV(snapshot, 'last') / pow(10, 3)), 4)

        #     # 界内证-潜在回报 =（1-最新价）/最新价*100%
        #     assert searchDicKV(snapshot, 'potentialProfit') == round((1 * pow(10, 3) - searchDicKV(snapshot, 'last')) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2))

        #     # 界内证-潜在亏损 =（最新价-0.25）/最新价*100%
        #     # assert searchDicKV(snapshot, 'potentialLoss') == round((searchDicKV(snapshot, 'last') - 0.25*pow(10, 3)) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2) )
        #     # 误差不超过1
        #     assert searchDicKV(snapshot, 'potentialLoss') - round((searchDicKV(snapshot, 'last') - 0.25*pow(10, 3)) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2) ) <= 1

        # 有效杠杆 = 杠杆比率 * 对冲值

        # 换股价 = 最新价*换股比率


    def test_stock_checkSnapshotData(self):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        exchange = "SEHK"
        code = "48297"

        frequence = None
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'订阅手机图表数据，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=10))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        basic = app_rsp['basicData']  # 静态数据
        snapshot = app_rsp['snapshot']  # 快照数据
        orderbook = app_rsp.get("orderbook")  # 盘口

        if orderbook:
            bid_vol = int(orderbook["orderBook"].get("bidVol") or 0)     # 盘口买盘数量
            ask_vol = int(orderbook["orderBook"].get("askVol") or 0)     # 盘口卖盘数量

        searchDicKV = lambda dic, keys: int(self.common.searchDicKV(dic, keys) or 0)

        try:
            assert searchDicKV(basic, "preClose") == searchDicKV(snapshot, "preclose")      # 校验静态数据的昨收价等于快照数据的昨收价
        except Exception as e:
            # self.logger.error("昨收价不一致")
            # self.logger.error(code)
            self.logger.error("昨收价不一致, exchange: {}, code: {}, basic --> {}, snapshot --> {}".format(
                exchange, code, searchDicKV(basic, "preClose"), searchDicKV(snapshot, "preclose")))
            raise e

        # 均价 == 成交额 / 成交量, 判断误差小于1, fiu给的, 无需判断
        # average = searchDicKV(snapshot, "average")
        # calc_average = searchDicKV(snapshot, "turnover") / searchDicKV(snapshot, "volume")
        # self.logger.debug("均价: {}, 成交额/成交量 : {}".format(average, calc_average))
        # assert abs(average - calc_average) < 1

        if snapshot.get("dataType") == "EX_STOCK":
            # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
            assert searchDicKV(snapshot, 'amplitude') == round((int(snapshot["high"]) - int(snapshot["low"])) / searchDicKV(snapshot, 'preclose') * 100 * pow(10, 2))

            # 委比=(委买手数-委卖手数)/(委买手数+委卖手数)*100% 
            # assert searchDicKV(snapshot, 'committee') - round((bid_vol - ask_vol) / (bid_vol + ask_vol) * 100 * pow(10, 2))
            # 判断误差不超过30, 因为委托实时变化
            assert abs(searchDicKV(snapshot, 'committee') - round((bid_vol - ask_vol) / (bid_vol + ask_vol) * 100 * pow(10, 2))) < 30

            # 量比=(现成交总手数/现累计开市时间(分))/过去5日平均每分钟成交量 (过去5日平均每分钟成交量 无法计算)
            pass

            # 总市值=总股本*最新价
            # assert searchDicKV(snapshot, 'totalMarketVal') == searchDicKV(basic, 'issuedShares') * searchDicKV(snapshot, 'last') / pow(10, 3)
            # 判断误差不超过1
            assert abs(searchDicKV(snapshot, 'totalMarketVal') - searchDicKV(basic, 'issuedShares') * searchDicKV(snapshot, 'last') / pow(10, 3)) < 1

            # 港股市值=香港普通股股本*最新价
            # assert searchDicKV(snapshot, 'circularMarketVal') == searchDicKV(basic, 'outstandingShares') * searchDicKV(snapshot, 'last') / pow(10, 3)
            # 判断误差不超过1
            assert abs(searchDicKV(snapshot, 'circularMarketVal') - searchDicKV(basic, 'outstandingShares') * searchDicKV(snapshot, 'last') / pow(10, 3)) < 1

            # 换手率=成交量/已发行总股数×100%
            assert searchDicKV(snapshot, 'turnoverRate') == round(searchDicKV(snapshot, 'volume') / searchDicKV(basic, 'issuedShares') * 100 * pow(10, 2))

            # 溢价--认购证&牛证的溢价＝（最新价×换股比率＋行使价－相关资产最新价）/相关资产最新价×100％
            pass

            # 溢价--认沽证&熊证的溢价＝（最新价×换股比率－行使价＋相关资产最新价）/相关资产最新价×100％
            pass

        if snapshot.get("dataType") == "EX_INNER":
            # 杠杆比率 = 1 / 最新价
            assert searchDicKV(snapshot, "leverageRatio")/pow(10, 4) == round(1 / (searchDicKV(snapshot, 'last') / pow(10, 3)), 4)

            # 界内证-潜在回报 =（1-最新价）/最新价*100%
            assert searchDicKV(snapshot, 'potentialProfit') == round((1 * pow(10, 3) - searchDicKV(snapshot, 'last')) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2))

            # 界内证-潜在亏损 =（最新价-0.25）/最新价*100%
            # assert searchDicKV(snapshot, 'potentialLoss') == round((searchDicKV(snapshot, 'last') - 0.25*pow(10, 3)) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2) )
            # 误差不超过1
            assert searchDicKV(snapshot, 'potentialLoss') - round((searchDicKV(snapshot, 'last') - 0.25*pow(10, 3)) / searchDicKV(snapshot, 'last') * 100 * pow(10, 2) ) <= 1

        # 有效杠杆 = 杠杆比率 * 对冲值

        # 换股价 = 最新价*换股比率


    def test_H5_SubscribeNewsharesQuoteSnapshot001(self):
        """订阅单个合约的已上市新股行情快照"""
        frequence = None

        exchange = SEHK_exchange
        base_info = [
            {'exchange': exchange, 'code': "01379"},
            {'exchange': exchange, 'code': "01945"},
            {'exchange': exchange, 'code': "02127"},
            {'exchange': exchange, 'code': "01940"},
            {'exchange': exchange, 'code': "02135"},
            {'exchange': exchange, 'code': "01167"}, 
            {'exchange': exchange, 'code': "02148"},
            {'exchange': exchange, 'code': "06677"}, 
            {'exchange': exchange, 'code': "02131"}, 
            {'exchange': exchange, 'code': "06993"},
            {'exchange': exchange, 'code': "09992"},
            {'exchange': exchange, 'code': "02117"},
            {'exchange': exchange, 'code': "06999"},
            {'exchange': exchange, 'code': "02117"},
            {'exchange': exchange, 'code': "06999"},
            {'exchange': exchange, 'code': "02142"},
            {'exchange': exchange, 'code': "01209"},
            {'exchange': exchange, 'code': "06618"},
            {'exchange': exchange, 'code': "02110"},
            {'exchange': exchange, 'code': "06666"},
            {'exchange': exchange, 'code': "06996"},
            {'exchange': exchange, 'code': "01516"},
            {'exchange': exchange, 'code': "02599"},
            {'exchange': exchange, 'code': "01795"},
            {'exchange': exchange, 'code': "06900"},
            ]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp, recv_num=1))


        self.logger.debug(u'接收数据')
        while True:
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=1))
            rsp = info_list[0]
            print("code : {}, last : {}".format(
                self.common.searchDicKV(rsp, "instrCode"),
                self.common.searchDicKV(rsp, "last")
            ))


    def test_Sub_Quote(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        base_info = [
                {'exchange': "NYSE", 'code': "HIG"},
            ]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info, is_delay=True,
                                                    start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'接收数据')
        while True:
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=1))

        # grep "h5_32c04822863f39a88f2861ca197063fb" 20210105_16* | grep -E "NASDAQ|NYSE"



    def test_stock_TradeTick(self):
        """订阅一个股票的逐笔: frequence=None"""
        frequence = None
        exchange = SEHK_exchange
        code = "01490"
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
        _start = time.time()
        while time.time() - _start < 60:
            info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1))


    @parameterized.expand([(1, ) for i in range(1000)])
    def test_push_status(self, a):
        """港股product_list为空，查询全部港股的交易状态"""
        resp = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=None, start_time_stamp=123, frequence=None))
        assert resp


    def test_SubscribeBrokerSnapshotReq001(self):
        """订阅单个合约的经纪席位快照"""
        self.logger.debug(u'****************test_SubscribeBrokerSnapshotReq001 测试开始********************')
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_code5
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange, code=code,
                                                    start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_broker_snapshot_json_list = quote_rsp['before_broker_snapshot_json_list']
        self.logger.debug(u'校验订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前经纪席位快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_10_PushBrokerSnapshot', 
                                                           before_broker_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_broker_snapshot_json_list.__len__()):
            info = before_broker_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_10_PushBrokerSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
        self.logger.debug(u'****************test_SubscribeBrokerSnapshotReq001 测试结束********************')






if __name__ == "__main__":
    # suite = unittest.TestSuite()
    # suite.addTest(Test_Subscribe("test_stock_SubscribeTradeTickReqApi_006"))
    # runner = unittest.TextTestRunner(verbosity=2)
    # inner_test_result = runner.run(suite)

    pytest.main(["-v", "-s",
                 "test_stock_subscribe_api.py",
                 "-k test_stock_QueryPlateSortMsgReq_001",
                 # "-m=Grey",
                 "--show-capture=stderr",
                 "--disable-warnings",
                 ])



