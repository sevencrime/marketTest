# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/21
# @Software: PyCharm

import unittest

from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from testcase.zmq_testcase.zmq_stock_record_testcase import CheckZMQ
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from pb_files.common_type_def_pb2 import *


class stockSubscribeTestCases(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.logger = get_log()
        self.http = MarketHttpClient()
        # self.market_token = self.http.get_market_token(self.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
        self.market_token = ''


    @classmethod
    def setUpClass(cls):
        cls.common = Common()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.new_loop = self.common.getNewLoop()
        asyncio.set_event_loop(self.new_loop)
        self.api = SubscribeApi(union_ws_url, self.new_loop, is_record=True)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())
        self.is_delay = False

    def tearDown(self):
        asyncio.set_event_loop(self.new_loop)
        self.api.client.disconnect()

    def inner_zmq_test_case(self, case_name, check_json_list, is_before_data=False, start_sub_time=None):
        suite = unittest.TestSuite()
        suite.addTest(CheckZMQ(case_name))
        suite._tests[0].check_json_list = check_json_list
        suite._tests[0].is_before_data = is_before_data
        suite._tests[0].sub_time = start_sub_time
        suite._tests[0].is_delay = self.is_delay
        runner = unittest.TextTestRunner()
        inner_test_result = runner.run(suite)
        return inner_test_result

    # --------------------------------------------------订阅start-------------------------------------------------------

    # --------------------------------------------------按合约订阅-------------------------------------------------------
    def test_Instr01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        self.logger.debug(u'****************test_Instr01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recvNum=2000))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__()==0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_Instr01 测试结束********************')

    # 按合约代码订阅时，订阅单市场多合约
    def test_Instr02(self):
        """按合约代码订阅时，订阅单市场多合约"""
        self.logger.debug(u'****************test_Instr02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = SEHK_code3
        code4 = SEHK_code4
        code5 = SEHK_code5
        code6 = SEHK_code6

        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2},
                     {'exchange': SEHK_exchange, 'code': code3}, {'exchange': SEHK_exchange, 'code': code4},
                     {'exchange': SEHK_exchange, 'code': code5}, {'exchange': SEHK_exchange, 'code': code6}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list, is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        self.logger.debug(u'****************test_Instr02 测试结束********************')

    # 按合约代码订阅时，合约代码为空
    def test_Instr03(self):
        """按合约代码订阅时，合约代码为空"""
        self.logger.debug(u'****************test_Instr03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with instr failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr03 测试结束********************')

    # 按合约代码订阅时，合约代码错误
    def test_Instr04(self):
        """按合约代码订阅时，合约代码错误"""
        self.logger.debug(u'****************test_Instr04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = 'xxx'

        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with instr failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr04 测试结束********************')

    # 订阅一个正确的合约代码，一个错误的合约代码
    def test_Instr05(self):
        """订阅一个正确的合约代码，一个错误的合约代码"""
        self.logger.debug(u'****************test_Instr05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = 'xxx'

        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("sub with instr failed, errmsg [instr [ SEHK_{} ] error].".format(code2) == self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') is None)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recvNum=1500))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        self.logger.debug(u'****************test_Instr05 测试结束********************')

    # 按合约代码订阅时，exchange错误
    def test_Instr06(self):
        """按合约代码订阅时，合约代码与市场不对应"""
        self.logger.debug(u'****************test_Instr06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = NASDAQ_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with instr failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr06 测试结束********************')

    def test_Instr07(self):
        """按合约代码订阅时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_Instr07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchangeType = ExchangeType.UNKNOWN
        code = SEHK_code1
        base_info = [{'exchange': exchangeType, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr07 测试结束********************')

    def test_Instr08(self):
        """按合约代码订阅时，合约代码 无，品种代码 正常，交易所 正常"""
        self.logger.debug(u'****************test_Instr08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchangeType = SEHK_exchange
        product_code = 'HHI'
        base_info = [{'exchange': exchangeType, 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr08 测试结束********************')

    def test_Instr09(self):
        """按合约代码订阅时，订阅单市场单合约,child_type SubChildMsgType.UNKNOWN_SUB_CHILD"""
        self.logger.debug(u'****************test_Instr09 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        child_type = SubChildMsgType.UNKNOWN_SUB_CHILD
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recvNum=2000))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_Instr09 测试结束********************')

    # --------------------------------------------查询快照数据--------------------------------------------------------------

    def test_QuerySnapshotApi_01(self):
        """查询单市场，单合约的快照数据"""
        self.logger.debug(u'****************test_QuerySnapshotApi_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_01 测试结束********************')

    def test_QuerySnapshotApi_02(self):
        """查询单市场，多合约的快照数据"""
        self.logger.debug(u'****************test_QuerySnapshotApi_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=1))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_02 测试结束********************')

    def test_QuerySnapshotApi_03(self):
        """查询单市场，多合约的快照数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuerySnapshotApi_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = 'XXX'
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.SubsQueryBmpMsgReqApi(
            sub_type=sub_type, child_type=child_type, base_info=base_info, start_time_stamp=start_time_stamp,
            recv_num=2))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[1],
                                    'retMsg') == "sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(
                code2))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_03 测试结束********************')

    def test_QuerySnapshotApi_04(self):
        """查询单市场，多合约的快照数据，部分合约代码为空"""
        self.logger.debug(u'****************test_QuerySnapshotApi_04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_04 测试结束********************')

    def test_QuerySnapshotApi_05(self):
        """查询快照数据时，code为空"""
        self.logger.debug(u'****************test_QuerySnapshotApi_05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_05 测试结束********************')

    def test_QuerySnapshotApi_06(self):
        """查询快照数据时，code错误"""
        self.logger.debug(u'****************test_QuerySnapshotApi_06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = 'xxxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(
            "sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(
                first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_06 测试结束********************')

    def test_QuerySnapshotApi_07(self):
        """查询快照数据时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_QuerySnapshotApi_07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code1
        exchange = 'UNKNOWN'
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0],
                                                'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_07 测试结束********************')

    def test_QuerySnapshotApi_08(self):
        """查询快照数据时，品种代码正常、合约代码无"""
        self.logger.debug(u'****************test_QuerySnapshotApi_08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        product_code = 'HHI'
        base_info = [{'exchange': SEHK_exchange, 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(
            "sub with msg failed, errmsg [req info is unknown]." == self.common.searchDicKV(first_rsp_list[0],
                                                                                            'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_08 测试结束********************')

    # -------------证券不按品种订阅---------------------------------按品种订阅---------------------------------------------
    # -------------证券不按市场订阅----------------------------按市场订阅---------------------------------------------------
    # 按市场进行订阅
    def test_Market_001_01(self):
        """ 按市场订阅，订阅一个市场(code不传入参数)"""
        self.logger.debug(u'****************test_Market_001_01 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MARKET

        base_info = [{'exchange': SEHK_exchange}]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')

        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.SubsQutoMsgReqApi(
            sub_type=sub_type, child_type=None, base_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MARKET')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recvNum=100000))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        else:
            self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Market_001_01 测试结束********************')

    # --------------------------------------------订阅快照数据--------------------------------------------------------------
    def test_QuoteSnapshotApi_01(self):
        """订阅单市场，单合约的快照数据"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'instrCode') == code)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_01 测试结束********************')

    def test_QuoteSnapshotApi_02(self):
        """订阅单市场，多合约的快照数据"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=1, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'instrCode') in (code1, code2))

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_02 测试结束********************')

    def test_QuoteSnapshotApi_03(self):
        """订阅单市场，多合约的快照数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = 'XXX'
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.SubsQutoMsgReqApi(
            sub_type=sub_type, child_type=child_type, base_info=base_info,start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[1], 'retMsg') == "sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(code2))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'instrCode') in code1)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_03 测试结束********************')

    def test_QuoteSnapshotApi_04(self):
        """订阅单市场，多合约的快照数据，部分合约代码为空"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(snapshot_json_list[0], 'instrCode') == code1)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_04 测试结束********************')

    def test_QuoteSnapshotApi_05(self):
        """订阅快照数据时，code为空"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_05 测试结束********************')

    def test_QuoteSnapshotApi_06(self):
        """订阅快照数据时，code错误"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = 'xxxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_06 测试结束********************')

    def test_QuoteSnapshotApi_07(self):
        """订阅快照数据时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code1
        exchange = 'UNKNOWN'
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_07 测试结束********************')

    def test_QuoteSnapshotApi_08(self):
        """订阅快照数据时，品种代码正常、合约代码无"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        product_code = 'HHI'
        base_info = [{'exchange': SEHK_exchange, 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [req info is unknown]."== self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_08 测试结束********************')

    # ------------------------------------------------订阅静态数据---------------------------------------------------
    def test_QuoteBasicInfo_Msg_001(self):
        """ 订阅单个市场、单个合约的静态数据 """
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_001 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'前盘口数据校验')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'校验静态数据') #推送频率太低，一般都收不到
        # inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', static_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(static_json_list.__len__()):
        #     info = static_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_001 测试结束********************')

    def test_QuoteBasicInfo_Msg_002(self):
        """ 订阅单个市场、多个合约的静态数据 """
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_002 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'静态数据校验')
        self.assertTrue(before_basic_json_list.__len__() == 2)  # 应仅返回两条
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'前盘口数据校验')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'校验静态数据')  # 推送频率太低，一般都收不到
        # inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', static_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # for i in range(static_json_list.__len__()):
        #     info = static_json_list[i]
        #     self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
        #     self.assertTrue(self.common.searchDicKV(info, 'instrCode') in [code1, code2])

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_002 测试结束********************')

    def test_QuoteBasicInfo_Msg_003(self):
        """ exchange不为空，code为空"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_003 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = None
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 不返回数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_003 测试结束********************')

    def test_QuoteBasicInfo_Msg_004(self):
        """ exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_004 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': 'UNKNOWN', 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 不返回数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_004 测试结束********************')

    def test_QuoteBasicInfo_Msg_005(self):
        """ 传入多个合约code，部分code是错误的code"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_005 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = 'xxxx'
        code2 = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              recv_num=2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("instr [ SEHK_{} ] error".format(code1) in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'静态数据校验')
        self.assertTrue(before_basic_json_list.__len__() == 1)  # 仅返回code2的静态数据
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') == code2)
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'静态数据校验') # 推送频率太低，一般都收不到
        # self.assertTrue(before_basic_json_list.__len__() == 1)  # 仅返回code2的静态数据
        # self.assertTrue(self.common.searchDicKV(static_json_list[0], 'instrCode') == code2)
        # inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', static_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_005 测试结束********************')

    def test_QuoteBasicInfo_Msg_006(self):
        """ 传入多个合约code，部分code为空"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_006 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = ''
        code2 = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              recv_num=2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("req info is unknown" in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'静态数据校验')
        self.assertTrue(before_basic_json_list.__len__() == 1)  # 仅返回code2的静态数据
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') == code2)
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'静态数据校验') # 推送频率太低，一般都收不到
        # self.assertTrue(before_basic_json_list.__len__() == 1)  # 仅返回code2的静态数据
        # self.assertTrue(self.common.searchDicKV(static_json_list[0], 'instrCode') == code2)
        # inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', static_json_list)
        # self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_006 测试结束********************')

    def test_QuoteBasicInfo_Msg_007(self):
        """ code传入错误的合约信息"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_007 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = 'xxxxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [instr [ SEHK_{} ] error].".format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 不返回数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_007 测试结束********************')

    def test_QuoteBasicInfo_Msg_008(self):
        """ exchange不为空，合约代码 无、品种代码 正常"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_008 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        product_code = 'HHI'
        base_info = [{'exchange': SEHK_exchange, 'product_code': product_code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [req info is unknown].')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 不返回数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_008 测试结束********************')

    # -----------------------------------------订阅盘口数据----------------------------------------------------
    def test_QuoteOrderBookDataApi01(self):
        """订阅单市场，单合约的盘口数据"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi01 测试结束********************')

    def test_QuoteOrderBookDataApi02(self):
        """订阅单市场，多合约盘口数据"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)


        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi02 测试结束********************')

    def test_QuoteOrderBookDataApi03(self):
        """订阅单市场，多合约的盘口数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = 'ddd'
        code3 = 'xxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2},
                     {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [instr [ SEHK_{} SEHK_{} ] error].".format(code2,code3) == self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_ORDER_BOOK')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi03 测试结束********************')

    def test_QuoteOrderBookDataApi04(self):
        """订阅单市场，多合约的盘口数据，部分市场合约代码为空"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [req info is unknown]." == self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_ORDER_BOOK')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)


        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(orderbook_json_list[0], 'instrCode') in code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi04 测试结束********************')

    def test_QuoteOrderBookDataApi05(self):
        """订阅盘口数据时，code为空"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = 'SEHK'
        code = ''
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('sub with msg failed, errmsg [req info is unknown].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断是否返回逐笔数据，返回则错误')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi05 测试结束********************')

    def test_QuoteOrderBookDataApi06(self):
        """订阅盘口数据时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = 'UNKNOWN'
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('sub with msg failed, errmsg [req info is unknown].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断是否返回逐笔数据，返回则错误')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi06 测试结束********************')

    def test_QuoteOrderBookDataApi07(self):
        """订阅盘口数据时，code参数错误"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = 'SEHK'
        code = 'xxxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('sub with msg failed, errmsg [instr [ SEHK_{} ] error].'.format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断是否返回逐笔数据，返回则错误')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi07 测试结束********************')

    def test_QuoteOrderBookDataApi08(self):
        """订阅盘口数据时，合约代码 无、品种代码 正常"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = 'SEHK'
        product_code = 'HHI'
        base_info = [{'exchange': SEHK_exchange, 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('sub with msg failed, errmsg [req info is unknown].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断是否返回逐笔数据，返回则错误')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi08 测试结束********************')

    def test_Subscribe_Msg_01(self):
        """订阅时sub_type传入UNKNOWN_SUB"""
        self.logger.debug(u'****************test_Subscribe_Msg_01 测试开始********************')
        sub_type = SubscribeMsgType.UNKNOWN_SUB
        code = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub quote msg failed, errmsg [subscribeMsgType is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Subscribe_Msg_01 测试结束********************')

    def test_Subscribe_Msg_02(self):
        """订阅时sub_type传入None"""
        self.logger.debug(u'****************test_Subscribe_Msg_02 测试开始********************')
        sub_type = None
        code = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub quote msg failed, errmsg [subscribeMsgType is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Subscribe_Msg_02 测试结束********************')

    def test_Subscribe_Msg_03(self):
        """订阅时child_type传入UNKNOWN_SUB_CHILD"""
        self.logger.debug(u'****************test_Subscribe_Msg_03 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.UNKNOWN_SUB_CHILD
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [subChildMsgType is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Subscribe_Msg_03 测试结束********************')

    def test_Subscribe_Msg_04(self):
        """订阅时child_type传入None"""
        self.logger.debug(u'****************test_Subscribe_Msg_04 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = None
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(before_basic_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 逐笔订阅不返回静态、快照数据
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with msg failed, errmsg [subChildMsgType is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Subscribe_Msg_04 测试结束********************')

    # ----------------------------------------------------订阅end-------------------------------------------------------

    # --------------------------------------------------取消订阅start----------------------------------------------------

    # -------------------------------------------------按合约取消订阅-----------------------------------------------------
    def test_UnInstr01(self):
        """订阅一个合约，取消订阅一个合约数据"""
        self.logger.debug(u'****************test_UnInstr01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_UnInstr01 测试结束********************')

    def test_UnInstr02(self):
        """订阅多个合约，取消订阅多个合约数据"""
        self.logger.debug(u'****************test_UnInstr02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)
        self.logger.debug(u'****************test_UnInstr02 测试结束********************')

    def test_UnInstr03(self):
        """订阅多个，取消订阅其中的一个合约"""
        self.logger.debug(u'****************test_UnInstr03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        self.logger.debug(u'****************test_UnInstr03 测试结束********************')

    def test_UnInstr04(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnInstr04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用取消行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(SEHK_code2) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        self.logger.debug(u'****************test_UnInstr04 测试结束********************')

    def test_UnInstr05(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致"""
        self.logger.debug(u'****************test_UnInstr05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = SEHK_code3
        code4 = 'xxxx'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}, {'exchange': SEHK_exchange, 'code': code4}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[1], 'retMsg') == 'unsub with instr failed,errmsg [instr [SEHK_{} ] error].'.format(code4))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        self.logger.debug(u'****************test_UnInstr05 测试结束********************')

    def test_UnInstr06(self):
        """按合约取消订阅时，code为空"""
        self.logger.debug(u'****************test_UnInstr06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code1
        code2 = ''
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with instr failed,errmsg [instrument code is null].')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        self.logger.debug(u'****************test_UnInstr06 测试结束********************')

    def test_UnInstr07(self):
        """按合约取消订阅时，code为None"""
        self.logger.debug(u'****************test_UnInstr07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = SEHK_code2
        code2 = None
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with instr failed,errmsg [instrument code is null].')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        self.logger.debug(u'****************test_UnInstr07 测试结束********************')

    def test_UnInstr08(self):
        """按合约取消订阅时，exchange为UNKONWN"""
        self.logger.debug(u'****************test_UnInstr08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        exchange1 = SEHK_exchange
        exchange2 = ExchangeType.UNKNOWN
        base_info1 = [{'exchange': exchange1, 'code': code}]
        base_info2 = [{'exchange': exchange2, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with instr failed,errmsg [exchange is unknown].')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_UnInstr08 测试结束********************')

    def test_UnInstr09(self):
        """按合约取消订阅时，exchange为None"""
        self.logger.debug(u'****************test_UnInstr09 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        exchange1 = 'SEHK'
        exchange2 = None
        base_info1 = [{'exchange': SEHK_exchange, 'code': code}]
        base_info2 = [{'exchange': exchange2, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with instr failed,errmsg [exchange is unknown].')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_UnInstr09 测试结束********************')

    def test_UnInstr10(self):
        """按合约取消订阅时，base_info为None"""
        self.logger.debug(u'****************test_UnInstr10 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        exchange1 = 'SEHK'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code}]
        base_info2 = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with instr failed,errmsg [unSub info is null].')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_UnInstr10 测试结束********************')

    def test_UnInstr11(self):
        """实时方式订阅一个合约，延时方式取消订阅一个合约数据"""
        self.logger.debug(u'****************test_UnInstr11 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))

        # 实时方式订阅
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=False))
        # 延时方式取消
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=True))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(orderbook_json_list.__len__()):
            info = orderbook_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'****************test_UnInstr11 测试结束********************')

    def test_UnInstr12(self):
        """延时方式订阅一个合约，实时方式取消订阅一个合约数据"""
        self.logger.debug(u'****************test_UnInstr12 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 延时方式订阅
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=True))
        # 实时方式取消
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=False))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(
            'unsub with instr failed,errmsg [no have subscribe [SEHK_{}]].'.format(code) == self.common.searchDicKV(
                first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi(recv_timeout_sec=30))
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(trade_json_list.__len__()):
            info = trade_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'****************test_UnInstr12 测试结束********************')

    # ------------------------------------------------证券不按市场和品种取消订阅--------------------------------------------------------

    # ------------------------------------------取消订阅快照数据---------------------------------------------------

    def test_UnSnapshot_001(self):
        """取消单个市场，单个合约的快照数据"""
        self.logger.debug(u'****************test_UnSnapshot_001 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')

        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code)
        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSnapshot_001 测试结束********************')

    def test_UnSnapshot_002(self):
        """取消单个市场,多个合约的快照数据"""
        self.logger.debug(u'****************test_UnSnapshot_002 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')

        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSnapshot_002 测试结束********************')

    def test_UnSnapshot_003(self):
        """订阅多个合约快照数据，取消订阅部分快照数据"""
        self.logger.debug(u'****************test_UnSnapshot_003 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')

        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        self.logger.debug(u'****************test_UnSnapshot_003 测试结束********************')

    def test_UnSnapshot_004(self):
        """取消订阅之后，再次发起订阅"""
        self.logger.debug(u'****************test_UnSnapshot_004 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500,recv_timeout_sec=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        # 再次发起订阅
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        self.logger.debug(u'****************test_UnSnapshot_004 测试结束********************')


    def test_UnSnapshot_005(self):
        """订阅一个合约的快照数据，取消订阅时，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnSnapshot_005 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2)==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照口数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        self.logger.debug(u'****************test_UnSnapshot_005 测试结束********************')

    def test_UnSnapshot_006(self):
        """订阅一个合约的快照数据，取消订阅时，合约代码错误"""
        self.logger.debug(u'****************test_UnSnapshot_006 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = 'xxx'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [ instr [SEHK_xxx  ] error ].".format(code2) ==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照口数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        self.logger.debug(u'****************test_UnSnapshot_006 测试结束********************')

    def test_UnSnapshot_007(self):
        """取消订阅快照数据时，code为空"""
        self.logger.debug(u'****************test_UnSnapshot_007 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [ instr [SEHK  ] error ]." in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))

        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        self.logger.debug(u'****************test_UnSnapshot_007 测试结束********************')

    def test_UnSnapshot_008(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnSnapshot_008 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = SEHK_code3
        code4 = SEHK_code4
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3},
                      {'exchange': SEHK_exchange, 'code': code4}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].".format(code4) ==
                        self.common.searchDicKV(first_rsp_list[1], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        self.logger.debug(u'****************test_UnSnapshot_008 测试结束********************')

    def test_UnSnapshot_009(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码为空"""
        self.logger.debug(u'****************test_UnSnapshot_009 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = None
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("instr [SEHK ] error " in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        self.logger.debug(u'****************test_UnSnapshot_009 测试结束********************')

    def test_UnSnapshot_010(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码错误"""
        self.logger.debug(u'****************test_UnSnapshot_010 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = 'xxxxx'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [instr [SEHK_{} ] error ].".format(code3) ==
                        self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        self.logger.debug(u'****************test_UnSnapshot_010 测试结束********************')

    def test_UnSnapshot_011(self):
        """取消订阅之后，再次发起取消订阅"""
        self.logger.debug(u'****************test_UnSnapshot_011 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == "unsub with msg success.")

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        # 再次发起取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2)) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'****************test_UnSnapshot_011 测试结束********************')

    def test_UnSnapshot_012(self):
        """取消订阅快照数据时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_UnSnapshot_012 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = 'SEHK'
        code = SEHK_code1
        base_info1 = [{'exchange': SEHK_exchange, 'code': code}]
        base_info2 = [{'exchange': ExchangeType.UNKNOWN, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [UNKNOWN_{}  ] error ].'.format(code) in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code))
        self.logger.debug(u'****************test_UnSnapshot_012 测试结束********************')

    def test_UnSnapshot_013(self):
        """实时订阅一个合约的快照数据，延时取消订阅时，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnSnapshot_013 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        # 实时订阅
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=False))
        # 延时取消
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=True))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2)==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照口数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        self.logger.debug(u'****************test_UnSnapshot_013 测试结束********************')

    def test_UnSnapshot_014(self):
        """延时订阅一个合约的快照数据，实时取消订阅时，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnSnapshot_014 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 延时订阅
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=True))
        # 实时取消
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=False))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2)==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照口数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))

        self.logger.debug(u'****************test_UnSnapshot_014 测试结束********************')

    # -------------------------------------------------------取消订阅静态数据-------------------------------------------------
    def test_UnQuoteBasicInfo_Msg_001(self):
        """ 取消订阅单个市场、单个合约的静态数据"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_001 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # 通过调用行情取消订阅接口，取消订阅数据
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_001 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_002(self):
        """ 取消订阅单个市场、多个合约的静态数据"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_002 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_002 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_003(self):
        """ 先订阅多个合约的静态数据，再取消其中一个合约的静态数据"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_003 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code4
        code2 = SEHK_code1
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2, start_time_stamp=start_time_stamp,
            is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'重新订阅成功，筛选出静态数据,并校验')
        # 因静态数据只会在订阅时和开市时才会推送，所以这里不好校验。
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_003 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_004(self):
        """ 先订阅2个合约的静态数据，再取消这2个合约的静态数据，再次订阅"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_004 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        # 再次订阅静态数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_004 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_005(self):
        """ 取消订阅静态数据，exchange不为空，code为None"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_005 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = None
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [SEHK  ] error ].' in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_005 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_006(self):
        """ code传入错误的合约信息"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_006 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        # 取消code1，code2入参错误
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        code3 = 'xxx'
        code4 = 'xxx'
        base_info = [{'exchange': SEHK_exchange, 'code': code3}, {'exchange': SEHK_exchange, 'code': code4}]
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [SEHK_{} SEHK_{}  ] error ].'.format(code3, code4) in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.logger.debug(u'取消订阅失败，筛选出静态数据,并校验')
        # 因静态数据只会在订阅时和开市时才会推送，所以这里不好校验。
        # info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        # self.assertTrue(info_list.__len__() > 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_006 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_007(self):
        """ exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_007 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in code)

        # 通过调用行情取消订阅接口，取消订阅数据
        base_info = [{'exchange': 'UNKNOWN', 'code': code}]
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [UNKNOWN_{}  ] error ].'.format(code) in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅失败，筛选出静态数据,并校验')
        # 因静态数据只会在订阅时和开市时才会推送，所以这里不好校验。
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_007 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_008(self):
        """ 静态数据取消，取消后再次取消"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_008 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code))

        # 通过调用行情取消订阅接口，取消订阅数据
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        # 再次取消
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code))
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_008 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_009(self):
        """ 实时方式订阅，延时方式取消"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_009 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 实时方式订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=False))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 通过调用行情取消订阅接口，取消订阅数据
        # 取消code1，code2入参错误
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        # 延时方式取消
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=True))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [SEHK_{} SEHK_{}  ] error ].'.format(code1, code2) in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.logger.debug(u'取消订阅失败，筛选出静态数据,并校验')
        # 因静态数据只会在订阅时和开市时才会推送，所以这里不好校验。
        # info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        # self.assertTrue(info_list.__len__() > 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_009 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_010(self):
        """ 延时方式订阅，实时方式取消"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_010 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 延时方式订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=True))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 实时方式取消
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info, start_time_stamp=start_time_stamp,
            is_delay=False))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{} SEHK_{}]].'.format(code1, code2) in self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.logger.debug(u'取消订阅失败，筛选出静态数据,并校验')
        # 因静态数据只会在订阅时和开市时才会推送，所以这里不好校验。
        # info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=20))
        # self.assertTrue(info_list.__len__() > 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_010 测试结束********************')

    # ------------------------------------------------取消订阅盘口数据-----------------------------------------------
    def test_UnQuoteOrderBookDataApi01(self):
        """取消单个市场，单个合约的盘口数据"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500,
                                                                                                      recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi01 测试结束********************')

    def test_UnQuoteOrderBookDataApi02(self):
        """取消单个市场,多个合约的盘口数据"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi02 测试结束********************')

    def test_UnQuoteOrderBookDataApi03(self):
        """订阅多个合约盘口数据，取消订阅部分合约数据"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi03 测试结束********************')

    def test_UnQuoteOrderBookDataApi04(self):
        """取消订阅之后，再发起订阅"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        # 再次发起订阅
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi04 测试结束********************')

    def test_UnQuoteOrderBookDataApi05(self):
        """订阅一个合约的盘口数据，取消订阅时，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code1)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code2) ==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))

        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi05 测试结束********************')

    def test_UnQuoteOrderBookDataApi06(self):
        """订阅一个合约的盘口数据，取消订阅时，合约代码错误"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = 'xxx'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code1)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [ instr [SEHK_xxx  ] error ].".format(code2) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi06 测试结束********************')

    def test_UnQuoteOrderBookDataApi07(self):
        """订阅多个合约盘口数据，取消订阅时部分合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = SEHK_code5
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].".format(code3) ==self.common.searchDicKV(first_rsp_list[1], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi07 测试结束********************')

    def test_UnQuoteOrderBookDataApi08(self):
        """订阅多个合约盘口数据，取消订阅时部分合约代码错误"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code6
        code2 = SEHK_code1
        code3 = 'xxx'
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("unsub with msg failed,errmsg [instr [SEHK_{} ] error ].".format(code3) == self.common.searchDicKV(first_rsp_list[1], 'retMsg'))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi08 测试结束********************')

    def test_UnQuoteOrderBookDataApi09(self):
        """订阅多个合约盘口数据，取消订阅时部分合约代码为空"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi09 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        code2 = SEHK_code2
        code3 = None
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code2}]
        base_info2 = [{'exchange': SEHK_exchange, 'code': code1}, {'exchange': SEHK_exchange, 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') in (code1, code2))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue('instr [SEHK ] error ' in self.common.searchDicKV(first_rsp_list[1], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code2))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi09 测试结束********************')

    def test_UnQuoteOrderBookDataApi10(self):
        """取消订阅盘口数据后再次取消"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi10 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = 'SEHK'
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == "unsub with msg success.")

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        # 再次取消
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi10 测试结束********************')

    def test_UnQuoteOrderBookDataApi11(self):
        """取消订阅盘口数据时，exchange传入UNKNOWN"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi11 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = SEHK_exchange
        exchange2 = ExchangeType.UNKNOWN
        code = SEHK_code1
        base_info1 = [{'exchange': exchange1, 'code': code}]
        base_info2 = [{'exchange': exchange2, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=1, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [UNKNOWN_{}  ] error ].'.format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code))
        else:
            self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi11 测试结束********************')

    def test_UnQuoteOrderBookDataApi12(self):
        """取消订阅盘口数据时，code为空"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi12 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = SEHK_exchange
        code1 = SEHK_code1
        code2 = ''
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
            self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code1)
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=1, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [ instr [SEHK  ] error ].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi12 测试结束********************')

    def test_UnQuoteOrderBookDataApi13(self):
        """实时方式订阅一个合约的盘口数据，延时方式取消订阅"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi13 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 实时方式订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=False))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        # self.assertTrue(info_list.__len__() == 1)  # 应仅返回一条
        self.assertTrue(self.common.searchDicKV(info_list[0], 'exchange') == 'SEHK')
        self.assertTrue(self.common.searchDicKV(info_list[0], 'instrCode') == code1)

        # 延时方式取消
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info1,
                                                start_time_stamp=start_time_stamp, is_delay=True))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code1) ==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code1))

        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi13 测试结束********************')

    def test_UnQuoteOrderBookDataApi14(self):
        """延时方式订阅一个合约的盘口数据，实时方式取消订阅时，合约代码与订阅合约代码不一致"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi14 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = SEHK_code1
        base_info1 = [{'exchange': SEHK_exchange, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 延时方式订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=True))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'SEHK')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        # 实时方式取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info1,
                                                start_time_stamp=start_time_stamp, is_delay=False))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code1) ==
                        self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi14 测试结束********************')

    def test_UnSubsQutoMsgApi01(self):
        """取消订阅（合约）时，sub_type传入UNKNOWN_SUB,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_INSTR
        sub_type2 = SubscribeMsgType.UNKNOWN_SUB
        code = SEHK_code4
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=None, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi01 测试结束********************')

    def test_UnSubsQutoMsgApi02(self):
        """取消订阅（合约）时，sub_type 不存在,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_INSTR
        sub_type2 = None
        code = SEHK_code4
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug('通过调用行情取消订阅接口，取消订阅数据')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=None, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi02 测试结束********************')

    # ------------------------------------------------证券不按市场和品种取消订阅--------------------------------------------------------
    def test_UnSubsQutoMsgApi03(self):
        """取消订阅（消息类型，快照）时，sub_type传入UNKNOWN_SUB,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = SubscribeMsgType.UNKNOWN_SUB
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code4
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi03 测试结束********************')

    def test_UnSubsQutoMsgApi04(self):
        """取消订阅（消息类型，快照）时，sub_type 为None,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = None
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = SEHK_code4
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi04 测试结束********************')

    def test_UnSubsQutoMsgApi05(self):
        """取消订阅（消息类型，静态）时，sub_type传入UNKNOWN_SUB,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = SubscribeMsgType.UNKNOWN_SUB
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi05 测试结束********************')

    def test_UnSubsQutoMsgApi06(self):
        """取消订阅（消息类型，静态）时，sub_type传入None,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi06 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = None
        child_type = SubChildMsgType.SUB_BASIC
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi06 测试结束********************')

    def test_UnSubsQutoMsgApi07(self):
        """取消订阅（消息类型，盘口）时，sub_type传入UNKNOWN_SUB,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi07 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = SubscribeMsgType.UNKNOWN_SUB
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi07 测试结束********************')

    def test_UnSubsQutoMsgApi08(self):
        """取消订阅（消息类型，盘口）时，sub_type传入None,取消成功"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi08 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type1 = SubscribeMsgType.SUB_WITH_MSG_DATA
        sub_type2 = None
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type1, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type2, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp,is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue('unsub all msg success.' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))


        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi08 测试结束********************')

    def test_UnSubsQutoMsgApi09(self):
        """取消订阅时，child_type为UNKNOWN_SUB_CHILD"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi09 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type1 = SubChildMsgType.SUB_ORDER_BOOK
        child_type2 = SubChildMsgType.UNKNOWN_SUB_CHILD
        exchange = 'SEHK'
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type1, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type2, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [unsubChildMsgType is unknown].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code))
        else:
            self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'****************test_UnSubsQutoMsgApi09 测试结束********************')

    def test_UnSubsQutoMsgApi10(self):
        """取消订阅时，child_type为None"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi10 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type1 = SubChildMsgType.SUB_ORDER_BOOK
        child_type2 = None
        exchange = 'SEHK'
        code = SEHK_code1
        base_info = [{'exchange': SEHK_exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type1, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type2, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [unsubChildMsgType is unknown].' == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi10 测试结束********************')

    def test_UnSubsQutoMsgApi11(self):
        """取消订阅时，child_type与订阅时的child_type不一致"""
        self.logger.debug(u'****************test_UnSubsQutoMsgApi11 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type1 = SubChildMsgType.SUB_ORDER_BOOK
        child_type2 = SubChildMsgType.SUB_BASIC
        exchange = SEHK_exchange
        code = SEHK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type1, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type2, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue('unsub with msg failed,errmsg [no have subscribe [SEHK_{}]].'.format(code) == self.common.searchDicKV(first_rsp_list[0], 'retMsg'))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=10))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue((self.common.searchDicKV(info, 'instrCode') == code))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSubsQutoMsgApi11 测试结束********************')

    # -------------------------------------------取消订阅end---------------------------------------------------

    # ------------------------------------------------外盘-----------------------------------------------------------

    # ------------------------------------------------按合约订阅---------------------------------------------------------
    def test_Instr_01(self):
        """按合约代码订阅时，订阅单市场单合约"""
        self.logger.debug(u'****************test_Instr_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code1
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list,
                                                         start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr_01 测试结束********************')

    def test_Instr_02(self):
        """按合约代码订阅时，订阅多市场多合约"""
        self.logger.debug(u'****************test_Instr_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        exchange3 = NASDAQ_exchange
        code4 = NASDAQ_code1
        exchange4 = BATS_exchange
        code5 = BATS_code1
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange3, 'code': code4},
                     {'exchange': exchange4, 'code': code5}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
                self.assertTrue(
                    self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
                self.assertTrue(
                    self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

            self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
                self.assertTrue(
                    self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))
        self.logger.debug(u'****************test_Instr_02 测试结束********************')

    def test_Instr_03(self):
        """按合约代码订阅时，订阅单市场单合约,但市场和合约不匹配"""
        self.logger.debug(u'****************test_Instr_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = ASE_exchange
        code1 = NYSE_code1
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with instr failed, errmsg [instr [ {}_{} ] error].'.format(exchange1,code1))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__()  == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__()  == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr_03 测试结束********************')

    def test_Instr_04(self):
        """按合约代码订阅时，订阅单市场单合约,但合约错误"""
        self.logger.debug(u'****************test_Instr_04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = NYSE_exchange
        code1 = 'XXXXX'
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retMsg') ==
            'sub with instr failed, errmsg [instr [ {}_{} ] error].'.format(exchange1, code1))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr_04 测试结束********************')

    def test_Instr_05(self):
        """按合约代码订阅时，订阅单市场单合约,但合约为空"""
        self.logger.debug(u'****************test_Instr_05 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = NYSE_exchange
        code1 = ''
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'sub with instr failed, errmsg [req info is unknown].')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 0)

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_Instr_05 测试结束********************')

    # --------------------------------------------查询外盘快照数据--------------------------------------------------------
    def test_QuerySnapshotApi_001(self):
        """查询单市场，单合约的快照数据"""
        self.logger.debug(u'****************test_QuerySnapshotApi_001 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code1
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQueryBmpMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_001 测试结束********************')

    def test_QuerySnapshotApi_002(self):
        """查询单市场，多合约的快照数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuerySnapshotApi_002 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.SubsQueryBmpMsgReqApi(
            sub_type=sub_type, child_type=child_type, base_info=base_info, start_time_stamp=start_time_stamp,
            recv_num=2))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_snapshot_json_list = quote_rsp['snapshot_json_list']

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情查询接口，查询数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[1],
                                    'retMsg') == "sub with msg failed, errmsg [instr [ ASE_{} ] error].".format(
                code2))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuerySnapshotApi_002 测试结束********************')

    # --------------备注：---证券不按品种和市场订阅-------------------------------------------------------------------------
    # --------------------------------------------订阅外盘快照数据--------------------------------------------------------
    def test_QuoteSnapshotApi_001(self):
        """订阅单市场，单合约的快照数据"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_001 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code1
        base_info = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_001 测试结束********************')

    def test_QuoteSnapshotApi_002(self):
        """订阅单市场，多合约的快照数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuoteSnapshotApi_002 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.SubsQutoMsgReqApi(
            sub_type=sub_type, child_type=child_type, base_info=base_info, start_time_stamp=start_time_stamp,
            recv_num=2, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(
            self.common.searchDicKV(first_rsp_list[1], 'retMsg') == "sub with msg failed, errmsg [instr [ ASE_{} ] error].".format(code2))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteSnapshotApi_002 测试结束********************')

    # --------------------------------------------------订阅外盘期货股票数据---------------------------------------------

    def test_QuoteBasicInfo_Msg_01(self):
        """ 订阅单市场，单合约的静态数据 """
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_01 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        exchange = NYSE_exchange
        code = NYSE_code1
        base_info = [{'exchange': exchange, 'code': code}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_01 测试结束********************')

    def test_QuoteBasicInfo_Msg_02(self):
        """ 单市场，多合约，部分合约代码错误"""
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_02 测试开始********************')
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              recv_num=2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retMsg') == "sub with msg failed, errmsg [instr [ ASE_{} ] error].".format(code2))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'静态数据校验')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteBasicInfo_Msg_02 测试结束********************')

    # ---------------------------------------------订阅外盘期货盘口数据--------------------------------------------------

    def test_QuoteOrderBookDataApi_01(self):
        """订阅单市场，多合约的盘口数据"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = NYSE_exchange
        code1 = NYSE_code1
        code2 = NYSE_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange')  == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi_01 测试结束********************')

    def test_QuoteOrderBookDataApi_02(self):
        """订阅多市场，多合约的盘口数据，部分合约代码错误"""
        self.logger.debug(u'****************test_QuoteOrderBookDataApi_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange = ASE_exchange
        code1 = ASE_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        before_orderbook_json_list = quote_rsp['before_orderbook_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue("sub with msg failed, errmsg [instr [ ASE_{} ] error].".format(code2) == self.common.searchDicKV(first_rsp_list[1],'retMsg'))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_ORDER_BOOK')
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
        #                 int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)


        self.logger.debug(u'校验前盘口数据')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', before_orderbook_json_list,
                                                         is_before_data=True, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(before_orderbook_json_list.__len__()):
                info = before_orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(before_orderbook_json_list.__len__() == 0)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        self.assertTrue(trade_json_list.__len__() == 0)

        self.logger.debug("判断是否返回静态数据，如果返回则错误")
        self.assertTrue(static_json_list.__len__() == 0)
        self.logger.debug(u'****************test_QuoteOrderBookDataApi_02 测试结束********************')

    # -----------------------------------------------取消订阅外盘------------------------------------------------------
    # ------------------------------------------外盘，按合约取消订阅--------------------------------------------------

    def test_UnInstr_01(self):
        """订阅单个市场一个合约，取消订阅一个合约数据"""
        self.logger.debug(u'****************test_UnInstr_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = NASDAQ_exchange
        code = NASDAQ_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

            self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_UnInstr_01 测试结束********************')

    def test_UnInstr_02(self):
        """订阅多个市场多个合约，取消订阅多个市场的合约数据"""
        self.logger.debug(u'****************test_UnInstr_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        exchange3 = NASDAQ_exchange
        code4 = NASDAQ_code1
        exchange4 = BATS_exchange
        code5 = BATS_code1
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange3, 'code': code4},
                     {'exchange': exchange4, 'code': code5}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (
            code1, code2, code3, code4, code5))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (
            code1, code2, code3, code4, code5))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (
                code1, code2, code3, code4, code5))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3, exchange4))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (
                code1, code2, code3, code4, code5))
        else:
            self.assertTrue(trade_json_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        self.assertTrue(snapshot_json_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'判断取消订阅之后，是否还会收到逐笔数据，如果还能收到，则测试失败')
        self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_UnInstr_02 测试结束********************')

    def test_UnInstr_03(self):
        """订阅单个市场多个合约，取消订阅某部分合约数据"""
        self.logger.debug(u'****************test_UnInstr_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code2
        code2 = NASDAQ_code1
        base_info = [{'exchange': exchange1, 'code': code1},{'exchange': exchange1, 'code': code2}]
        base_info2 = [{'exchange': exchange1, 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
        else:
            self.assertTrue(trade_json_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        quote_rsp = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteStatic_snapshot_tradeDataApi())
        trade_json_list = quote_rsp['trade_json_list']
        snapshot_json_list = quote_rsp['snapshot_json_list']
        orderbook_json_list = quote_rsp['orderbook_json_list']
        static_json_list = quote_rsp['static_json_list']

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', snapshot_json_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(snapshot_json_list.__len__()):
            info = snapshot_json_list[i]
            self.assertTrue(
                self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', orderbook_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(orderbook_json_list.__len__()):
                info = orderbook_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        else:
            self.assertTrue(orderbook_json_list.__len__() == 0)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_04_QuoteTradeData', trade_json_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(trade_json_list.__len__()):
                info = trade_json_list[i]
                self.assertTrue(
                    self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        else:
            self.assertTrue(trade_json_list.__len__() == 0)
        self.logger.debug(u'****************test_UnInstr_03 测试结束********************')

    # -------------------------------------------取消订阅外盘期货快照数据----------------------------------------------------

    def test_UnSnapshot_01(self):
        """订阅多个市场，取消多个市场，多个合约的快照数据"""
        self.logger.debug(u'****************test_UnSnapshot_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，取消订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnSnapshot_01 测试结束********************')

    def test_UnSnapshot_02(self):
        """取消订阅之后，再次发起订阅"""
        self.logger.debug(u'****************test_UnSnapshot_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'判断取消订阅之后，是否还会收到快照数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)


        #  再次订阅
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        self.logger.debug(u'****************test_UnSnapshot_02 测试结束********************')

    def test_UnSnapshot_03(self):
        """订阅一个市场，取消订阅时，部分合约代码与订阅时的代码不一致"""
        self.logger.debug(u'****************test_UnSnapshot_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code2
        code2 = NASDAQ_code1
        code3 = 'xxxx'
        base_info1 = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        base_info2 = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code3}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retMsg') ==
                        'unsub with msg failed,errmsg [instr [ASE_{} ] error ].'.format(code3))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=20))
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', info_list,
                                                     start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(info_list.__len__()):
            info = info_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
        self.logger.debug(u'****************test_UnSnapshot_03 测试结束********************')

    # -----------------------------------------------取消订阅外盘期货静态数据---------------------------------------------

    def test_UnQuoteBasicInfo_Msg_01(self):
        """ 订阅多个市场，取消订阅多个市场，多个合约的静态数据"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_01 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_01 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_02(self):
        """ 取消订阅，再次发起订阅"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_02 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        # 再次订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_02 测试结束********************')

    def test_UnQuoteBasicInfo_Msg_03(self):
        """ 订阅多个市场，取消订阅一个市场，部分合约代码与订阅时的代码不一致"""
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_03 测试开始********************')
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        code3 = 'xxxx'
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2}]
        base_info2 = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                      {'exchange': exchange1, 'code': code3}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retMsg') == 'unsub with msg success.')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retMsg') == 'unsub with msg failed,errmsg [instr [ASE_{} ] error ].'.format(code3))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'取消订阅成功，筛选出静态数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteBasicInfo_Msg_03 测试结束********************')

    # ------------------------------------------取消订阅外盘期货盘口数据------------------------------------------------

    def test_UnQuoteOrderBookDataApi_01(self):
        """订阅多个市场，取消订阅多个市场的盘口数据"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_01 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=8000))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_01 测试结束********************')

    def test_UnQuoteOrderBookDataApi_02(self):
        """订阅多个市场，取消订阅一个市场的盘口数据"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_02 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        base_info2 = [{'exchange': exchange2, 'code': code4}, {'exchange': exchange3, 'code': code5},
                     {'exchange': exchange3, 'code': code6}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500, recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500, recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(
                    self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_02 测试结束********************')

    def test_UnQuoteOrderBookDataApi_03(self):
        """取消订阅后，再次订阅"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_03 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500, recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    #     再次订阅
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=2000))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_03 测试结束********************')


    def test_UnQuoteOrderBookDataApi_04(self):
        """订阅多个市场，取消订阅一个市场，部分合约代码与订阅时的合约代码不一致"""
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_04 测试开始********************')
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        exchange1 = ASE_exchange
        code1 = ASE_code1
        code2 = ASE_code2
        exchange2 = NYSE_exchange
        code3 = NYSE_code1
        code4 = NYSE_code2
        exchange3 = NASDAQ_exchange
        code5 = NASDAQ_code1
        code6 = NASDAQ_code2
        code7 = 'xxxx'
        base_info = [{'exchange': exchange1, 'code': code1}, {'exchange': exchange1, 'code': code2},
                     {'exchange': exchange2, 'code': code3}, {'exchange': exchange2, 'code': code4},
                     {'exchange': exchange3, 'code': code5}, {'exchange': exchange3, 'code': code6}]
        base_info2 = [{'exchange': exchange3, 'code': code4}, {'exchange': exchange3, 'code': code5},
                      {'exchange': exchange3, 'code': code6}, {'exchange': exchange3, 'code': code7}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, is_delay=self.is_delay))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_03_QuoteBasicInfo', before_basic_json_list)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_basic_json_list.__len__()):
            info = before_basic_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))

        self.logger.debug(u'校验前快照数据')
        inner_test_result = self.inner_zmq_test_case('test_stock_01_QuoteSnapshot', before_snapshot_json_list,
                                                     is_before_data=True, start_sub_time=start_time_stamp)
        self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
        for i in range(before_snapshot_json_list.__len__()):
            info = before_snapshot_json_list[i]
            self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
            self.assertTrue(
                self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))


        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500, recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3, code4, code5, code6))
        else:
            self.assertTrue(info_list.__len__() == 0)

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, rspNum=2, is_delay=self.is_delay))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list.reverse()

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        # self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
        #                 int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retMsg') ==
                        'unsub with msg failed,errmsg [instr [NASDAQ_{} NASDAQ_{} ] error ].'.format(code4, code7))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500, recv_timeout_sec=20))
        if self.is_delay is False:
            inner_test_result = self.inner_zmq_test_case('test_stock_02_QuoteOrderBookData', info_list, start_sub_time=start_time_stamp)
            self.assertTrue(inner_test_result.failures.__len__() + inner_test_result.errors.__len__() == 0)
            for i in range(info_list.__len__()):
                info = info_list[i]
                self.assertTrue(self.common.searchDicKV(info, 'exchange') in (exchange1, exchange2, exchange3))
                self.assertTrue(
                    self.common.searchDicKV(info, 'instrCode') in (code1, code2, code3))
        else:
            self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'****************test_UnQuoteOrderBookDataApi_04 测试结束********************')


if __name__ == '__main_':
    unittest.main()

