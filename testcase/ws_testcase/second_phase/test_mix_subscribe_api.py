# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/9/1
# @Software: PyCharm

import unittest
import pytest
import allure
from parameterized import parameterized, param
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from pb_files.common_type_def_pb2 import *
import sys, os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = curPath[:curPath.find("marketTest\\") + len("marketTest\\")]
sys.path.append(rootPath)


class Test_Subscribe(unittest.TestCase):
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

    # --------------------------------------------------订阅start-------------------------------------------------------

    def test_SubsQutoMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的快照数据, 延时订阅一个单市场，单合约的快照数据"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange1 = SEHK_exchange
        code1 = SEHK_code1
        # exchange1 = SEHK_exchange
        # code1 = '0000100'
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_code1
        # exchange2 = NASDAQ_exchange
        # code2 = NASDAQ_code2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['first_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    def test_SubsQutoMsgReqApi_002(self):
        """延时订阅美股市场，单合约的盘口数据, 不发送数据"""
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code1
        base_info2 = [{'exchange': exchange2, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------订阅分时数据-------------------------------------------------------

    def test_SubscribeKlineMinReqApi_001(self):
        """实时订阅一个单市场，单合约的分时数据, 延时订阅一个单市场，单合约的分时数据"""
        start_time_stamp = int(time.time() * 1000)

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        # exchange1 = HK_exchange
        # code1 = HK_code1
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NYSE_exchange
        code2 = NYSE_code1

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp - 60 * 1000)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (
                                delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------取消订阅分时数据-------------------------------------------------------

    def test_UnsubscribeKlineMinReqApi_001(self):
        """实时订阅一个单市场，单合约的分时数据, 延时订阅一个单市场，单合约的分时数据, 分别取消订阅"""
        start_time_stamp = int(time.time() * 1000)

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKlineMinReqApi_002(self):
        """实时订阅一个单市场，单合约的分时数据, 延时订阅一个单市场，单合约的分时数据, 错位取消订阅,报错"""
        start_time_stamp = int(time.time() * 1000)

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKlineMinReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKlineMinReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp - 60 * 1000)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (
                                delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------K线订阅----------------------------------------------

    def test_SubscribeKLineMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的5分K数据, 延时订阅一个单市场，单合约的5分K数据"""
        start_time_stamp = int(time.time() * 1000)
        peroid_type = KLinePeriodType.FIVE_MIN
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收Kline数据的接口，筛选出Kline数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------取消K线订阅-------------------------------------------

    def test_UnsubscribeKLineMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的5分K数据, 延时订阅一个单市场，单合约的5分K数据, 分别取消订阅"""
        start_time_stamp = int(time.time() * 1000)
        peroid_type = KLinePeriodType.FIVE_MIN
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收Kline数据的接口，筛选出Kline数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeKLineMsgReqApi_002(self):
        """实时订阅一个单市场，单合约的5分K数据, 延时订阅一个单市场，单合约的5分K数据, 错位取消订阅, 取消失败"""
        start_time_stamp = int(time.time() * 1000)
        peroid_type = KLinePeriodType.FIVE_MIN
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info1,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info2,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收Kline数据的接口，筛选出Kline数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------订阅逐笔成交数据---------------------------------------

    def test_SubscribeTradeTickReqApi_001(self):
        """实时订阅一个单市场，单合约的逐笔数据, 延时订阅一个单市场，单合约的逐笔数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    def test_SubscribeTradeTickReqApi_002(self):
        """实美股市场在延迟行情中不返回逐笔数据"""
        start_time_stamp = int(time.time() * 1000)

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code1

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------取消订阅逐笔成交数据-------------------------------------------------------

    def test_UnsubscribeTradeTickReqApi_001(self):
        """实时订阅一个单市场，单合约的逐笔数据, 延时订阅一个单市场，单合约的逐笔数据,对应取消，取消成功"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeTradeTickReqApi_002(self):
        """实时订阅一个单市场，单合约的逐笔数据, 延时订阅一个单市场，单合约的逐笔数据,错位取消，取消失败"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeTradeTickReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------订阅经纪席位快照接口(证券专用)-------------------------------

    def test_SubscribeBrokerSnapshotReqApi_001(self):
        # 延时行情里没有经纪席位快照推送
        """实时订阅一个单市场，单合约的经纪席位数据, 延时订阅一个单市场，单合约的经纪席位数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        code1 = SEHK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_code2

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['first_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收经纪席位的接口，筛选出经纪席位，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'timestampBuy') if self.common.searchDicKV(info, 'timestampBuy') else self.common.searchDicKV(info, 'timestampSell'))
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.fail('延时行情里没有经纪席位快照推送')
    # --------------------------------------------------取消经纪位席位快照接口(证券专用)-------------------------------

    def test_UnSubscribeBrokerSnapshotReqApi_001(self):
        """实时订阅一个单市场，单合约的经纪席位数据, 延时订阅一个单市场，单合约的经纪席位数据， 取消订阅，取消成功"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        code1 = SEHK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_code2

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收经纪席位的接口，筛选出经纪席位，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnSubscribeBrokerSnapshotReqApi_002(self):
        """实时订阅一个单市场，单合约的经纪席位数据, 延时订阅一个单市场，单合约的经纪席位数据， 错序取消，取消失败"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        code1 = SEHK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_code2

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubscribeBrokerSnapshotReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收经纪席位的接口，筛选出经纪席位，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushBrokerSnapshotApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.fail('延时行情不应推送经济席位')

    # --------------------------------------------------暗盘行情订阅(证券专用)-------------------------------
    def test_SubscribeGreyMarketQuoteMsgReqApi_001(self):
        """延时订阅一个单市场，单合约的暗盘数据"""
        sub_quote_type1 = SubQuoteMsgType.DELAY_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收暗盘数据的接口，筛选出暗盘数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    def test_SubscribeGreyMarketQuoteMsgReqApi_002(self):
        """实时订阅一个单市场，单合约的暗盘数据, 延时订阅一个单市场，单合约的暗盘数据"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_greyMarketCode2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['first_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收暗盘数据的接口，筛选出暗盘数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------取消暗盘行情订阅接口(证券专用)-------------------------------
    def test_UnsubscribeGreyMarketQuoteMsgReqApi_001(self):
        """实延时订阅一个单市场，单合约的暗盘数据, 取消订阅成功"""
        sub_quote_type1 = SubQuoteMsgType.DELAY_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                                              start_time_stamp=start_time_stamp,
                                                              sub_quote_type=sub_quote_type1, recv_num=20))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeGreyMarketQuoteMsgReqApi_002(self):
        """实时订阅一个单市场，单合约的暗盘数据, 延时订阅一个单市场，单合约的暗盘数据, 取消订阅成功"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_newshares_code2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                                              start_time_stamp=start_time_stamp,
                                                              sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                              start_time_stamp=start_time_stamp,
                                                              sub_quote_type=sub_quote_type2, recv_num=20))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeGreyMarketQuoteMsgReqApi_003(self):
        """实时订阅一个单市场，单合约的暗盘数据, 延时订阅一个单市场，单合约的暗盘数据, 错位取消，取消失败"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_greyMarketCode1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_greyMarketCode2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 订阅
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        # 取消订阅
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info1,
                                                              start_time_stamp=start_time_stamp,
                                                              sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeGreyMarketQuoteMsgReqApi(base_info=base_info2,
                                                              start_time_stamp=start_time_stamp,
                                                              sub_quote_type=sub_quote_type1, recv_num=50))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.GreyMarketQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------已上市新股行情订阅(证券专用)-------------------------------

    def test_SubscribeNewSharesQuoteMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的已上市新股数据, 延时订阅一个单市场，单合约的已上市新股数据"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_newshares_code2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['first_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['first_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收已上市新股数据的接口，筛选出已上市新股数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------取消已上市新股行情订阅接口(证券专用)-------------------------------

    def test_UnsubscribeNewSharesQuoteMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的已上市新股数据, 延时订阅一个单市场，单合约的已上市新股数据， 对应取消，取消成功"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_newshares_code2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info1,
                                                             start_time_stamp=start_time_stamp,
                                                             sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2,
                                                             start_time_stamp=start_time_stamp,
                                                             sub_quote_type=sub_quote_type2, recv_num=50))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收已上市新股数据的接口，筛选出已上市新股数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_UnsubscribeNewSharesQuoteMsgReqApi_002(self):
        """实时订阅一个单市场，单合约的已上市新股数据, 延时订阅一个单市场，单合约的已上市新股数据， 错位取消，取消失败"""
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        start_time_stamp = int(time.time() * 1000)
        exchange1 = SEHK_exchange
        code1 = SEHK_newshares_code1
        base_info1 = [{'exchange': exchange1, 'code': code1}]

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_newshares_code2
        base_info2 = [{'exchange': exchange2, 'code': code2}]

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeNewSharesQuoteMsgReqApi(base_info=base_info2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2, recv_num=20))
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info1,
                                                             start_time_stamp=start_time_stamp,
                                                             sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeNewSharesQuoteMsgReqApi(base_info=base_info2,
                                                             start_time_stamp=start_time_stamp,
                                                             sub_quote_type=sub_quote_type1, recv_num=50))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收已上市新股数据的接口，筛选出已上市新股数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.NewsharesQuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------订阅手机图表数据(手机专用)-------------------------------

    def test_StartChartDataReqApi_001(self):
        """实时订阅一个单市场，单合约的图表数据, 延时订阅一个单市场，单合约的图表数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        code1 = '00700'

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code1

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的快照数据1')
        sourceUpdateTime = int(self.common.searchDicKV(quote_rsp1[0]['snapshot'], 'sourceUpdateTime'))
        self.assertTrue(
            int(sourceUpdateTime / (pow(10, 6))) < start_time_stamp)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的快照数据2')
        sourceUpdateTime = int(self.common.searchDicKV(quote_rsp2[0]['snapshot'], 'sourceUpdateTime'))
        self.assertTrue(
            int(sourceUpdateTime / (pow(10,
                                        6))) <= start_time_stamp - (
                        delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'检查回包里面的盘口数据1')
        sourceUpdateTime = int(self.common.searchDicKV(quote_rsp1[0]['orderbook'], 'sourceUpdateTime'))
        self.assertTrue(
            int(sourceUpdateTime / (pow(10, 6))) < start_time_stamp)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的盘口数据2')
        sourceUpdateTime = int(self.common.searchDicKV(quote_rsp2[0]['orderbook'], 'sourceUpdateTime'))
        self.assertTrue(
            int(sourceUpdateTime / (pow(10,
                                        6))) <= start_time_stamp - (
                        delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------取消订阅手机图表数据(手机专用)-------------------------------

    def test_StopChartDataReqApi_001(self):
        """实时订阅一个单市场，单合约的图表数据, 延时订阅一个单市场，单合约的图表数据,停止订阅，停止成功"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = CME_exchange
        code1 = CME_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange=exchange1, code=code1,
                                                 start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange=exchange2, code=code2,
                                                 start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_StopChartDataReqApi_002(self):
        """实时订阅一个单市场，单合约的图表数据, 延时订阅一个单市场，单合约的图表数据,错位取消，取消失败"""
        start_time_stamp = int(time.time() * 1000)
        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = CME_exchange
        code1 = CME_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange1, code=code1,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange=exchange2, code=code2,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange=exchange1, code=code1,
                                                 start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange=exchange2, code=code2,
                                                 start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------查询当日分时数据-------------------------------------------------------

    def test_QueryKLineMinMsgReqApi_001(self):
        """实时订阅一个单市场，单合约的查询当日分时, 延时订阅一个单市场，单合约的查询当日分时数据"""
        start_time_stamp = int(time.time() * 1000)
        isSubKLineMin = True
        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        code1 = SEHK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NASDAQ_exchange
        code2 = NASDAQ_code1

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin=isSubKLineMin, exchange=exchange1, code=code1,
                                                   query_type=query_type, direct=direct, start=start, end=end, vol=vol,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin=isSubKLineMin, exchange=exchange2, code=code2,
                                                   query_type=query_type, direct=direct, start=start, end=end, vol=vol,
                                              start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['query_kline_min_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['query_kline_min_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的分时数据1')
        datas = quote_rsp1['query_kline_min_rsp_list'][0]['data']
        for data in datas:
            sourceUpdateTime = int(self.common.searchDicKV(data, 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) < start_time_stamp)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的分时数据2')
        datas = quote_rsp2['query_kline_min_rsp_list'][0]['data']
        for data in datas:
            sourceUpdateTime = int(self.common.searchDicKV(data, 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp - 60 * 1000)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------查询五日分时数据-------------------------------------------------------

    def test_QueryFiveDaysKLineMinReqApi_001(self):
        """实时订阅一个单市场，单合约的查询五日分时, 延时订阅一个单市场，单合约的查询五日分时数据"""
        start_time_stamp = int(time.time() * 1000)
        isSubKLineMin = True
        start = None  # app 订阅服务该字段无意义

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = HK_exchange
        code1 = HK_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin=isSubKLineMin, exchange=exchange1, code=code1,
                                                        start=start, start_time_stamp=start_time_stamp,
                                                        sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryFiveDaysKLineMinReqApi(isSubKLineMin=isSubKLineMin, exchange=exchange2, code=code2,
                                                        start=start, start_time_stamp=start_time_stamp,
                                                        sub_quote_type=sub_quote_type2))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['query_5day_klinemin_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['query_5day_klinemin_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的分时数据1')
        day_data_list = self.common.searchDicKV(quote_rsp1['query_5day_klinemin_rsp_list'][0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        for i in range(len(day_data_list)):
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            for info in info_list:
                self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp + 1 * 60 * 1000)

        self.logger.debug(u'检查回包里面的分时数据2')
        day_data_list = self.common.searchDicKV(quote_rsp2['query_5day_klinemin_rsp_list'][0], 'dayData')
        self.assertTrue(day_data_list.__len__() == 5)
        for i in range(len(day_data_list)):
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            for info in info_list:
                self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp - 60 * 1000)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------查询历史K线-------------------------------------------------------

    def test_QueryKLineMsgReqApi_001(self):
        """实时查询一个单市场，单合约的1分K数据, 延时查询一个单市场，单合约的1分K数据"""
        start_time_stamp = int(time.time() * 1000)
        isSubKLine = True
        start = None  # app 订阅服务该字段无意义
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start = start_time_stamp
        end = None
        vol = 100

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = CME_exchange
        code1 = CME_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = CBOT_exchange
        code2 = CBOT_code10

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'查询K线数据，并检查返回结果')
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine=isSubKLine, exchange=exchange1, code=code1,
                                                peroid_type=peroid_type, query_type=query_type,
                                                direct=direct, start=start, end=end, vol=vol,
                                                start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMsgReqApi(isSubKLine=isSubKLine, exchange=exchange2, code=code2,
                                                peroid_type=peroid_type, query_type=query_type,
                                                direct=direct, start=start, end=end, vol=vol,
                                                start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['query_kline_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['query_kline_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的分时数据1')
        k_data_list = self.common.searchDicKV(quote_rsp1['query_kline_rsp_list'][0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp + 1 * 60 * 1000)

        self.logger.debug(u'检查回包里面的分时数据2')
        k_data_list = self.common.searchDicKV(quote_rsp2['query_kline_rsp_list'][0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            sourceUpdateTime = self.common.changeStrTimeToStamp(sourceUpdateTime)
            if self.common.searchDicKV(info, 'code') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp - 60 * 1000)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------逐笔成交查询-------------------------------------------------------

    def test_QueryTradeTickMsgReqApi_001(self):
        """实时查询一个单市场，单合约的逐笔数据, 延时查询一个单市场，单合约的逐笔数据"""
        isSubTrade = True
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = NASDAQ_exchange
        code1 = NASDAQ_code1

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        code2 = SEHK_code1

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        self.logger.debug(u'查询K线数据，并检查返回结果')
        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade=isSubTrade, exchange=exchange1, code=code1,
                                                    query_type=query_type, direct=direct, start_time=start_time,
                                                    end_time=end_time,  vol=vol, start_time_stamp=start_time_stamp,
                                                    sub_quote_type=sub_quote_type1))
        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade=isSubTrade, exchange=exchange2, code=code2,
                                                    query_type=query_type, direct=direct, start_time=start_time,
                                                    end_time=end_time, vol=vol, start_time_stamp=start_time_stamp,
                                                    sub_quote_type=sub_quote_type2))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1['query_trade_tick_rsp_list'][0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2['query_trade_tick_rsp_list'][0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的逐笔数据1')
        tick_data_list = self.common.searchDicKV(quote_rsp1['query_trade_tick_rsp_list'][0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)
        for info in tick_data_list:
            self.assertTrue(int(self.common.searchDicKV(info, 'time')) / (pow(10, 6)) <= start_time_stamp)

        self.logger.debug(u'检查回包里面的逐笔数据2')
        tick_data_list = self.common.searchDicKV(quote_rsp2['query_trade_tick_rsp_list'][0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)
        for info in tick_data_list:
            self.assertTrue(int(self.common.searchDicKV(info, 'time')) / (pow(10, 6)) <= start_time_stamp -
                    delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time')) / (pow(10, 6))
            if self.common.searchDicKV(info, 'instrCode') == code1:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange1)
                self.assertTrue(
                    int(sourceUpdateTime) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange2)
                self.assertTrue(
                    int(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------查询板块接口(证券专用)------------------------------------------------
    def test_QueryPlateSortMsgReqApi_001(self):
        """实时查询一个单市场的板块信息, 延时查询另一个单市场的板块信息"""
        start_time_stamp = int(time.time() * 1000)
        isSubTrade = True
        sort_direct = QueryInstrSortType.ASCENDING_ORDER
        count = 10

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        zone1 = ZoneType.HK
        plate_type1 = PlateType.LISTED_NEW_SHARES

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        zone2 = ZoneType.US
        plate_type2 = PlateType.CHINA_CONCEPT_STOCK

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone1, plate_type=plate_type1,
                                                    sort_direct=sort_direct, count=count,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone=zone2, plate_type=plate_type2,
                                                    sort_direct=sort_direct, count=count,
                                                    start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2,
                                                    recv_num=200))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的快照数据1')
        info_list = self.common.searchDicKV(quote_rsp1[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp - 1 * 60 * 1000)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的快照数据2')
        info_list = self.common.searchDicKV(quote_rsp2[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'exchange') == 'SEHK':
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------交易所股票排序查询接口(证券专用)------------------------------------------------
    def test_QueryExchangeSortMsgReqApi_001(self):
        """实时查询一个单市场的交易所股票排序, 延时查询另一个单市场的交易所股票排序"""
        start_time_stamp = int(time.time() * 1000)
        isSubTrade = True
        count = 10

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        sortFiled1 = SnapshotSortField.DIVIDEND_RATIO_TTM

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = NASDAQ_exchange
        sortFiled2 = SnapshotSortField.R_F_RATIO

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange1, sortFiled=sortFiled1,
                                                       count=count, start_time_stamp=start_time_stamp,
                                                       sub_quote_type=sub_quote_type1))

        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange2, sortFiled=sortFiled2,
                                                       count=count, start_time_stamp=start_time_stamp,
                                                       sub_quote_type=sub_quote_type2, recv_num=100))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的快照数据1')
        info_list = self.common.searchDicKV(quote_rsp1[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp - 1 * 60 * 1000)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的快照数据2')
        info_list = self.common.searchDicKV(quote_rsp2[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'exchange') == 'SEHK':
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

    # --------------------------------------------------查询指数成份股接口(证券专用)------------------------------------------------

    def test_QueryIndexShareMsgReqApi_001(self):
        """实时查询一个单市场的指数成份股, 延时查询另一个单市场的指数成份股"""
        start_time_stamp = int(time.time() * 1000)
        isSubTrade = True
        count = 10

        sub_quote_type1 = SubQuoteMsgType.REAL_QUOTE_MSG
        exchange1 = SEHK_exchange
        index1 = IndexType.HSI_INDEX
        sort_direct1 = QueryInstrSortType.DESCENDING_ORDER

        sub_quote_type2 = SubQuoteMsgType.DELAY_QUOTE_MSG
        exchange2 = SEHK_exchange
        index2 = IndexType.HSCEI_INDEX
        sort_direct2 = QueryInstrSortType.DESCENDING_ORDER

        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

        quote_rsp1 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange1, index=index1,
                                                     sort_direct=sort_direct1, count=count,
                                                     start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type1))

        quote_rsp2 = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange2, index=index2,
                                                     sort_direct=sort_direct2, count=count,
                                                     start_time_stamp=start_time_stamp, sub_quote_type=sub_quote_type2,
                                                     recv_num=100))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(quote_rsp1[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(quote_rsp2[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'检查回包里面的快照数据1')
        info_list = self.common.searchDicKV(quote_rsp1[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp - 1 * 60 * 1000)  # 毫秒级别对比

        self.logger.debug(u'检查回包里面的快照数据2')
        info_list = self.common.searchDicKV(quote_rsp2[0], 'snapshotData')
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据，并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        for info in info_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            if self.common.searchDicKV(info, 'exchange') == 'SEHK':
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10, 6))) >= start_time_stamp)  # 毫秒级别对比
            else:
                self.assertTrue(
                    int(sourceUpdateTime / (pow(10,
                                                6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

if __name__ == "__main__":
    # suite = unittest.TestSuite()
    # suite.addTest(Test_Subscribe("test_SubscribeTradeTickReqApi_006"))
    # runner = unittest.TextTestRunner(verbosity=2)
    # inner_test_result = runner.run(suite)

    pytest.main(["-v", "-s",
                 "test_stock_subscribe_api.py",
                 "-k test_SubscribeBrokerSnapshotReq001",
                 "--show-capture=stderr"
                 ])
