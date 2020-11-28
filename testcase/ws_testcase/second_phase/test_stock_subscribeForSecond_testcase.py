# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/9/1
# @Software: PyCharm

import pytest
import unittest
import allure
from parameterized import parameterized, param
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from testcase.zmq_testcase.zmq_stock_record_testcase import CheckZMQ as CheckStockZMQ
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from pb_files.common_type_def_pb2 import *
import sys, os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = curPath[:curPath.find("marketTest\\") + len("marketTest\\")]
sys.path.append(rootPath)


class Test_SubscribeForSecond(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.logger = get_log()
        self.http = MarketHttpClient()
        self.market_token = self.http.get_market_token(
            self.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

    @classmethod
    def setUpClass(cls):
        cls.common = Common()

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

    def inner_stock_zmq_test_case(self, case_name, check_json_list, is_before_data=False, start_sub_time=None,
                            start_time=None, exchange=None, instr_code=None, peroid_type=None):
        suite = unittest.TestSuite()
        suite.addTest(CheckStockZMQ(case_name))
        suite._tests[0].check_json_list = check_json_list
        suite._tests[0].is_before_data = is_before_data
        suite._tests[0].sub_time = start_sub_time
        suite._tests[0].start_time = start_time
        suite._tests[0].exchange = exchange
        suite._tests[0].instr_code = instr_code
        suite._tests[0].peroid_type = peroid_type
        runner = unittest.TextTestRunner()
        inner_test_result = runner.run(suite)
        return inner_test_result

    # def inner_future_zmq_test_case(self, case_name, check_json_list, is_before_data=False, start_sub_time=None,
    #                         start_time=None, exchange=None, instr_code=None, peroid_type=None):
    #     suite = unittest.TestSuite()
    #     suite.addTest(CheckFutureZMQ(case_name))
    #     suite._tests[0].check_json_list = check_json_list
    #     suite._tests[0].is_before_data = is_before_data
    #     suite._tests[0].sub_time = start_sub_time
    #     suite._tests[0].start_time = start_time
    #     suite._tests[0].exchange = exchange
    #     suite._tests[0].instr_code = instr_code
    #     suite._tests[0].peroid_type = peroid_type
    #     runner = unittest.TextTestRunner()
    #     inner_test_result = runner.run(suite)
    #     return inner_test_result

    # --------------------------------------------------订阅经纪席位快照------------------------------------------------
    def test_SubscribeBrokerSnapshotReq001(self):
        """订阅单个合约的经纪席位快照"""
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
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

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

    def test_SubscribeBrokerSnapshotReq002(self):
        """订阅单个合约的经纪席位快照，合约代码为空"""
        frequence = None
        exchange = SEHK_exchange
        code = ''
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
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub with instr failed, errmsg [req info is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前经纪席位快照')
        self.assertTrue(before_broker_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeBrokerSnapshotReq003(self):
        """订阅单个合约的经纪席位快照，合约代码错误"""
        frequence = None
        exchange = SEHK_exchange
        code = 'xxx'
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
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with instr failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前经纪席位快照')
        self.assertTrue(before_broker_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeBrokerSnapshotReq004(self):
        """订阅单个合约的经纪席位快照，exchange传入UNKNOWN"""
        frequence = None
        exchange = 'UNKNOWN'
        code = SEHK_code1
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
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前经纪席位快照')
        self.assertTrue(before_broker_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------取消订阅经纪席位快照------------------------------------------------
    def test_UnSubscribeBrokerSnapshotReq001(self):
        """订阅单个合约的经纪席位快照，取消订阅"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_code1
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
        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange, code=code,
                                                          start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        
    def test_UnSubscribeBrokerSnapshotReq002(self):
        """订阅单个合约的经纪席位快照，取消订阅, 合约代码与订阅合约代码不一致"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = SEHK_code2
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange, code=code1,
                                                          start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_broker_snapshot_json_list = quote_rsp['before_broker_snapshot_json_list']
        self.logger.debug(u'校验订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange, code=code2,
                                                          start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code1)
        
    def test_UnSubscribeBrokerSnapshotReq003(self):
        """订阅单个合约的经纪席位快照，取消订阅, 合约代码 错误"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = 'xxxx'
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange, code=code1,
                                                          start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_broker_snapshot_json_list = quote_rsp['before_broker_snapshot_json_list']
        self.logger.debug(u'校验订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange, code=code2,
                                                          start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code1)

    def test_UnSubscribeBrokerSnapshotReq004(self):
        """订阅单个合约的经纪席位快照，取消订阅, code为空"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = ''
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange, code=code1,
                                                          start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_broker_snapshot_json_list = quote_rsp['before_broker_snapshot_json_list']
        self.logger.debug(u'校验订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange, code=code2,
                                                            start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(
            code2) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code1)

    def test_UnSubscribeBrokerSnapshotReq005(self):
        """订阅单个合约的经纪席位快照，取消订阅, exchange为UNKONWN"""
        frequence = None
        exchange1 = SEHK_exchange
        exchange2 = ExchangeType.UNKNOWN
        code = SEHK_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code,
                                                          start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_broker_snapshot_json_list = quote_rsp['before_broker_snapshot_json_list']
        self.logger.debug(u'校验订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code,
                                                            start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(
            code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    # --------------------------------------------------普通方式 订阅已上市新股行情快照-------------------------------------------
    def test_SubscribeNewsharesQuoteSnapshot001(self):
        """订阅单个合约的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code = SEHK_newshares_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list,
                                                           is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_SubscribeNewsharesQuoteSnapshot002(self):
        """订阅多个合约的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
                                                           before_orderbook_json_list,
                                                           is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list,
                                                           is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_SubscribeNewsharesQuoteSnapshot003(self):
        """订阅单个合约的已上市新股行情快照，合约代码为空"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code = ''
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        self.logger.debug(u'校验前已上市新股行情快照')
        self.assertTrue(before_new_shares_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeNewsharesQuoteSnapshot004(self):
        """订阅单个合约的已上市新股行情快照，合约代码错误"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code = 'xxx'
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub with msg failed, errmsg [instr [ SEHK_xxx ] error].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        self.logger.debug(u'校验前已上市新股行情快照')
        self.assertTrue(before_new_shares_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeNewsharesQuoteSnapshot005(self):
        """订阅一个正确的合约代码，一个错误的合约代码的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = 'xxx'
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1],
                                                'retMsg') == 'sub with msg failed, errmsg [instr [ SEHK_{} ] error].'.format(code2))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
                                                           before_orderbook_json_list,
                                                           is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list,
                                                           is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instr_code') == code1)

    # --------------------------------------------------取消订阅已上市新股行情快照-------------------------------------------
    def test_UnSubscribeNewsharesQuoteSnapshot001(self):
        """取消订阅单个合约的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code = SEHK_newshares_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnSubscribeNewsharesQuoteSnapshot002(self):
        """订阅多个合约，取消订阅其中的一个合约的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, recv_num=2))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeNewsharesQuoteSnapshot003(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeNewsharesQuoteSnapshot004(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        code3 = SEHK_newshares_code3
        code4 = SEHK_newshares_code4
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code3},
                      {'exchange': exchange, 'code': code4}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, recv_num=2))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        if self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE':
            quote_rsp.reverse()

        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(quote_rsp[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(quote_rsp[1],
                                    'retMsg') == 'unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code4))
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_UnSubscribeNewsharesQuoteSnapshot005(self):
        """取消订阅单个合约，code为空的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = ''
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeNewsharesQuoteSnapshot006(self):
        """取消订阅单个合约，code为None的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeNewsharesQuoteSnapshot007(self):
        """取消订阅单个合约，exchange为UNKONWN的已上市新股行情快照"""
        frequence = None
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': ExchangeType.UNKNOWN, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    # --------------------------------------------------订阅已上市新股行情快照-------------------------------------------
    def test_H5_SubscribeNewsharesQuoteSnapshot001(self):
        """订阅单个合约的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_newshares_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list, 
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_H5_SubscribeNewsharesQuoteSnapshot002(self):
        """订阅单个合约的普通股行情快照，合约代码为空"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub new shares failed, errmsg [instr [ SEHK_{}} ] error].'.format(code))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前已上市新股行情快照')
        self.assertTrue(before_new_shares_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeNewsharesQuoteSnapshot003(self):
        """订阅多个合约的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        
    def test_H5_SubscribeNewsharesQuoteSnapshot004(self):
        """订阅单个合约的已上市新股行情快照，合约代码为空"""
        frequence = None
        exchange = SEHK_exchange
        code = ''
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub new shares failed, errmsg [req info is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前已上市新股行情快照')
        self.assertTrue(before_new_shares_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeNewsharesQuoteSnapshot005(self):
        """订阅单个合约的已上市新股行情快照，合约代码错误"""
        frequence = None
        exchange = SEHK_exchange
        code = 'xxx'
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info,
                                                             start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub new shares failed, errmsg [instr [ SEHK_xxx ] error].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前已上市新股行情快照')
        self.assertTrue(before_new_shares_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        
    def test_H5_SubscribeNewsharesQuoteSnapshot006(self):
        """订阅一个正确的合约代码，一个错误的合约代码的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = 'xxx'
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_new_shares_snapshot_json_list = quote_rsp['before_new_shares_snapshot_json_list']
        
        self.logger.debug(u'校验订阅已上市新股行情快照的回报')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1],
                                                'retMsg') == 'sub with instr failed, errmsg [req info is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))
        
        self.logger.debug(u'校验前已上市新股行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                           before_new_shares_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_new_shares_snapshot_json_list.__len__()):
            info = before_new_shares_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instr_code') == code1)
        
    # --------------------------------------------------取消订阅已上市新股行情快照-------------------------------------------
    def test_H5_UnSubscribeNewsharesQuoteSnapshot001(self):
        """取消订阅单个合约的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_newshares_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        
    def test_H5_UnSubscribeNewsharesQuoteSnapshot002(self):
        """订阅多个合约，取消订阅其中的一个合约的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_H5_UnSubscribeNewsharesQuoteSnapshot003(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            
    def test_H5_UnSubscribeNewsharesQuoteSnapshot004(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = SEHK_newshares_code2
        code3 = SEHK_newshares_code3
        code4 = SEHK_newshares_code4
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code3}, 
                      {'exchange': exchange, 'code': code4}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        if self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE':
            quote_rsp.reverse()
            
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(quote_rsp[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(quote_rsp[1],
                                    'retMsg') == 'unsub with instr failed,errmsg [instr [HKFE_{} ] error].'.format(
                code4))
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')))
        
        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            
    def test_H5_UnSubscribeNewsharesQuoteSnapshot005(self):
        """取消订阅单个合约，code为空的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = ''
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            
    def test_H5_UnSubscribeNewsharesQuoteSnapshot006(self):
        """取消订阅单个合约，code为None的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
    
    def test_H5_UnSubscribeNewsharesQuoteSnapshot007(self):
        """取消订阅单个合约，exchange为UNKONWN的已上市新股行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': ExchangeType.UNKNOWN, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅已上市新股行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    # --------------------------------------------------按合约订阅已上市新股行情-----------------------------------------------------
    def test_Instr_NewsharesQuote01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code = SEHK_newshares_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用已上市新股行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot',
                                                     before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收已上市新股快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_11_NewsharesQuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'通过接收已上市新股盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'通过接收已上市新股逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    # -------------------------------------------------按合约取消订阅已上市新股行情-----------------------------------------------------
    def test_UnInstr_NewsharesQuote01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_newshares_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------订阅暗盘行情快照-------------------------------------------
    def test_SubscribeGreyMarketQuoteSnapshot001(self):
        """订阅单个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        # 因缺太多字段，临时屏蔽
        # self.logger.debug(u'校验静态数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_basic_json_list.__len__()):
        #     info = before_basic_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # self.logger.debug(u'校验前盘口数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
        #                                              is_before_data=True, start_sub_time=start_time_stamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_orderbook_json_list.__len__()):
        #     info = before_orderbook_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            
    def test_SubscribeGreyMarketQuoteSnapshot002(self):
        """订阅多个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        # 因缺太多字段，临时屏蔽
        # self.logger.debug(u'校验静态数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_basic_json_list.__len__()):
        #     info = before_basic_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # self.logger.debug(u'校验前盘口数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
        #                                                    before_orderbook_json_list,
        #                                                    is_before_data=True, start_sub_time=start_time_stamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_orderbook_json_list.__len__()):
        #     info = before_orderbook_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            
    def test_SubscribeGreyMarketQuoteSnapshot003(self):
        """订阅单个合约的暗盘行情快照，合约代码为空"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = ''
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']
        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)
            
    def test_SubscribeGreyMarketQuoteSnapshot004(self):
        """订阅单个合约的暗盘行情快照，合约代码错误"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = 'xxx'
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
                                                           before_orderbook_json_list,
                                                           is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)
        
    def test_SubscribeGreyMarketQuoteSnapshot005(self):
        """订阅一个正确的合约代码，一个错误的合约代码的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = 'xxx'
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            "sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(code2) == self.common.searchDicKV(
                first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))
        
        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
                                                           before_orderbook_json_list,
                                                           is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            
    def test_SubscribeGreyMarketQuoteSnapshot006(self):
        """订阅单个合约的暗盘行情快照，exchange传入UNKNOWN"""
        frequence = None
        exchange = ExchangeType.UNKNOWN
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData',
                                                           before_orderbook_json_list,
                                                           is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------取消订阅暗盘行情快照-------------------------------------------
    def test_UnSubscribeGreyMarketQuoteSnapshot001(self):
        """取消订阅单个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnSubscribeGreyMarketQuoteSnapshot002(self):
        """订阅多个合约，取消订阅其中的一个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_UnSubscribeGreyMarketQuoteSnapshot003(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeGreyMarketQuoteSnapshot004(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        code3 = 'XXXX'
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code3}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        if self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE':
            quote_rsp.reverse()

        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(quote_rsp[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(quote_rsp[1],
                                    'retMsg') == 'unsub with msg failed,errmsg [instr [SEHK_{} ] error ].'.format(
                code3))
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_UnSubscribeGreyMarketQuoteSnapshot005(self):
        """取消订阅单个合约，code为空的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = ''
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeGreyMarketQuoteSnapshot006(self):
        """取消订阅单个合约，code为None的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_UnSubscribeGreyMarketQuoteSnapshot007(self):
        """取消订阅单个合约，exchange为UNKONWN的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_greyMarketCode1
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': ExchangeType.UNKNOWN, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_SubscribeBrokerSnapshotReq_GreyMarket(self):
        """订阅暗盘的经纪席位快照 """
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

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
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_10_PushBrokerSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)

    def test_UnSubscribeBrokerSnapshotReq_GreyMarket(self):
        """订阅暗盘的经纪席位快照，取消订阅"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
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
        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange, code=code,
                                                          start_time_stamp=start_time_stamp))
        self.logger.debug(u'校验取消订阅经纪席位快照的回报')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
# --------------------------------------------------按合约订阅暗盘行情-----------------------------------------------------
    def test_Instr_GreyMarketQuote01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用暗盘行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        # self.logger.debug(u'校验静态数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_basic_json_list.__len__()):
        #     info = before_basic_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                     before_grey_market_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # # 接收800条丢掉
        # info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=300))

        self.logger.debug(u'通过接收暗盘快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # self.logger.debug(u'通过接收暗盘盘口数据的接口，筛选出盘口数据,并校验')
        # info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
        #                                              start_sub_time=start_time_stamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(info_list.__len__()):
        #     info = info_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收暗盘逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    # -------------------------------------------------按合约取消订阅暗盘行情-----------------------------------------------------
    def test_UnInstr_GreyMarketQuote01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_newshares_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

        # --------------------------------------------------订阅暗盘行情快照-------------------------------------------

    def test_H5_SubscribeGreyMarketQuoteSnapshot001(self):
        """订阅单个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

    def test_H5_SubscribeGreyMarketQuoteSnapshot002(self):
        """订阅单个合约(普通股票)的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeGreyMarketQuoteSnapshot003(self):
        """订阅单个合约(昨天的暗盘)的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1_yesterday
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeGreyMarketQuoteSnapshot004(self):
        """订阅多个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_H5_SubscribeGreyMarketQuoteSnapshot005(self):
        """订阅单个合约的暗盘行情快照，合约代码为空"""
        frequence = None
        exchange = SEHK_exchange
        code = ''
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeGreyMarketQuoteSnapshot006(self):
        """订阅单个合约的暗盘行情快照，合约代码错误"""
        frequence = None
        exchange = SEHK_exchange
        code = 'xxx'
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_SubscribeGreyMarketQuoteSnapshot007(self):
        """订阅一个正确的合约代码，一个错误的合约代码的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = 'xxx'
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            "sub with instr failed, errmsg [instr [ HKFE_{} ] error].".format(code2) == self.common.searchDicKV(
                first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') is None)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot',
                                                           before_grey_market_snapshot_json_list, is_before_data=True,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_grey_market_snapshot_json_list.__len__()):
            info = before_grey_market_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_H5_SubscribeGreyMarketQuoteSnapshot008(self):
        """订阅单个合约的暗盘行情快照，exchange传入UNKNOWN"""
        frequence = None
        exchange = ExchangeType.UNKNOWN
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_grey_market_snapshot_json_list = quote_rsp['before_grey_market_snapshot_json_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前暗盘行情快照')
        self.assertTrue(before_grey_market_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() == 0)

        # --------------------------------------------------取消订阅暗盘行情快照-------------------------------------------

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot001(self):
        """取消订阅单个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code = SEHK_greyMarketCode1
        base_info = [{'exchange': exchange, 'code': code}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot002(self):
        """订阅多个合约，取消订阅其中的一个合约的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot003(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot004(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = SEHK_greyMarketCode2
        code3 = 'XXXX'
        base_info1 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        base_info2 = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code3}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        if self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE':
            quote_rsp.reverse()

        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(quote_rsp[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(quote_rsp[1],
                                    'retMsg') == 'unsub grey quote failed, errmsg [SEHK_{} ].'.format(
                code3))
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(quote_rsp[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot005(self):
        """取消订阅单个合约，code为空的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = ''
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot006(self):
        """取消订阅单个合约，code为None的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

    def test_H5_UnSubscribeGreyMarketQuoteSnapshot007(self):
        """取消订阅单个合约，exchange为UNKONWN的暗盘行情快照"""
        frequence = None
        exchange = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': ExchangeType.UNKNOWN, 'code': code1}]
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1, start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'校验订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'校验取消订阅暗盘行情快照的回报')
        self.assertTrue(self.common.searchDicKV(quote_rsp[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')) == start_time_stamp)
        #  响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(quote_rsp[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(quote_rsp[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=50))
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_12_GreyMarketQuoteSnapshot', info_list,
                                                           start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

# --------------------------------------------------按合约订阅--指数--------------------------------------------------
# 指数 有静态数据和快照数据，没盘口和逐笔
# -----------------------------------------------------------------------------------------------------------------
    def test_InstrIndex01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code1 = SEHK_indexCode1
        code2 = SEHK_indexCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用指数行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        # self.logger.debug(u'校验指数静态数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_basic_json_list.__len__()):
        #     info = before_basic_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # self.logger.debug(u'校验指数前快照数据')
        # inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
        #                                              is_before_data=True, start_sub_time=start_time_stamp)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(before_snapshot_json_list.__len__()):
        #     info = before_snapshot_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验指数前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收指数快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收指数盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'通过接收指数逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnInstrIndex01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_indexCode1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用指数行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅指数之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅指数之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅指数之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

# --------------------------------------------------按合约订阅--信托产品-----------------------------------------------------
    def test_InstrTrst01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code1 = SEHK_TrstCode1
        code2 = SEHK_TrstCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用信托产品行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验信托产品静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验信托产品前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验信托产品前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收信托产品快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收信托产品盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收信托产品逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_UnInstrTrst01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_TrstCode1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用信托产品行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅信托产品之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅信托产品之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅信托产品之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

# --------------------------------------------------按合约订阅--涡轮-----------------------------------------------------
    def test_InstrWarrant01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code1 = SEHK_WarrantCode1
        code2 = SEHK_WarrantCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用涡轮行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验涡轮静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验涡轮前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验涡轮前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收涡轮快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收涡轮盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收涡轮逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_UnInstrWarrant01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_WarrantCode1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用涡轮行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅涡轮之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅涡轮之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅涡轮之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

# --------------------------------------------------按合约订阅--牛熊证-----------------------------------------------------
    def test_InstrCbbc01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code1 = SEHK_CbbcCode1
        code2 = SEHK_CbbcCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用牛熊证行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验牛熊证静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验牛熊证前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验牛熊证前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收牛熊证快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收牛熊证盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收牛熊证逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_UnInstrCbbc01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_CbbcCode1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用牛熊证行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅牛熊证之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅牛熊证之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅牛熊证之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

# --------------------------------------------------按合约订阅--界内证-----------------------------------------------------
    def test_InstrInner01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code1 = SEHK_InnerCode1
        code2 = SEHK_InnerCode2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用界内证行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验界内证静态数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验界内证前快照数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验界内证前盘口数据')
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_orderbook_json_list.__len__()):
            info = before_orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 接收800条丢掉
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.only_recvMsg(recv_num=800))

        self.logger.debug(u'通过接收界内证快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收界内证盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收界内证逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000,
                                                                                                  recv_timeout_sec=20))
        inner_test_result = self.inner_stock_zmq_test_case('test_stock_04_QuoteTradeData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

    def test_UnInstrInner01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_InnerCode1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用界内证行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅界内证之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅界内证之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅界内证之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100,
                                                                                                  recv_timeout_sec=20))
        self.assertTrue(info_list.__len__() == 0)

if __name__ == "__main__":
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(Test_Subscribe("test_SubscribeTradeTickReqApi_006"))
    # runner = unittest.TextTestRunner(verbosity=2)
    # inner_test_result = runner.run(suite)

    # pytest.main(["-v", "-s",
    #              "test_stock_subscribe_api.py",
    #              "-k test_SubscribeBrokerSnapshotReq001",
    #              "--show-capture=stderr"
    #              ])
