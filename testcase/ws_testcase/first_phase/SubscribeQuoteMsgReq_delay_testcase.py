# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/29
# @Software: PyCharm

import unittest
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient


class SubscribeTestCases(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.logger = get_log()
        self.http = MarketHttpClient()
        self.market_token = self.http.get_market_token(self.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

    @classmethod
    def setUpClass(cls):
        cls.common = Common()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.new_loop = self.common.getNewLoop()
        asyncio.set_event_loop(self.new_loop)
        self.api = SubscribeApi(union_ws_url, self.new_loop, is_record=False)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())

    def tearDown(self):
        asyncio.set_event_loop(self.new_loop)
        self.api.client.disconnect()

    # --------------------------------------按合约订阅-----------------------------------------

    def test_Instr_01(self):
        """按合约代码订阅时，订阅一个合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelayDelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Instr_02(self):
        """按合约代码订阅时，订阅多个合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 2)
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 2)
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_snapshot_json_list[1], 'instrCode'))
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=2000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Instr_03(self):
        """订阅一个正确的合约代码，一个错误的合约代码"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = 'xxxx'
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list = first_rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Instr_04(self):
        """订阅多个合约代码，其中一个为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = ''
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list = first_rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=2000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Instr_05(self):
        """NYMEX:按合约代码订阅时，订阅一个合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        exchange = NYMEX_exchange
        code = NYMEX_code1
        base_info = [{'exchange': exchange, 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------按品种订阅----------------------------------------------

    def test_Product_01(self):
        """订阅单市场，单品种"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code = 'HHI'
        base_info = [{'exchange': 'HKFE', 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))

        first_rsp_list = rsp_list['first_rsp_list']
        before_basic_json_list = rsp_list['before_basic_json_list']
        before_snapshot_json_list = rsp_list['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))     # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Product_02(self):
        """
        订阅多个品种
        """
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'HHI'
        product_code2 = 'HSI'
        base_info = [{'exchange': 'HKFE', 'product_code': product_code1},
                     {'exchange': 'HKFE', 'product_code': product_code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, base_info=base_info, start_time_stamp=start_time_stamp))

        first_rsp_list = rsp_list['first_rsp_list']
        before_basic_json_list = rsp_list['before_basic_json_list']
        before_snapshot_json_list = rsp_list['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'productCode') in [product_code1, product_code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[1], 'productCode') in [product_code1, product_code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'productCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'productCode') in (product_code1, product_code2))
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[1], 'productCode') in (product_code1, product_code2))
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'productCode') != self.common.searchDicKV(
            before_snapshot_json_list[1], 'instrCode'))
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') in (product_code1, product_code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') in (product_code1, product_code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') in (product_code1, product_code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Product_03(self):
        """订阅一个正确的品种，一个错误的品种"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'HHI'
        product_code2 = 'xxx'
        base_info = [{'exchange': 'HKFE', 'product_code': product_code1},
                     {'exchange': 'HKFE', 'product_code': product_code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list = first_rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') is None)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Product_04(self):
        """订阅多个品种，其中一个productcode为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'HHI'
        product_code2 = None
        base_info = [{'exchange': 'HKFE', 'product_code': product_code1},
                     {'exchange': 'HKFE', 'product_code': product_code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list = first_rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE':
            first_rsp_list = first_rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_PRODUCT')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') is None)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')))

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'productCode') == product_code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # ---------------------------------------- 按市场订阅-----------------------------------------------------

    def test_Market_01(self):
        """ 按市场订阅，订阅一个市场(code不传入参数)"""
        sub_type = SubscribeMsgType.SUB_WITH_MARKET
        base_info = [{'exchange': 'HKFE'}]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MARKET')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=5000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=3000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_Market_02(self):
        """ 按市场订阅，订阅一个市场,code不为空"""
        sub_type = SubscribeMsgType.SUB_WITH_MARKET
        base_info = [{'exchange': 'HKFE', 'code': 'HHI2005'}]

        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MARKET')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=3000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # def test_Market_03(self):
    #     """ 按市场订阅，订阅多个市场"""
    #     sub_type = SubscribeMsgType.SUB_WITH_MARKET
    #     exchange1 = 'HKFE'
    #     exchange2 = 'SGX'
    #     exchange3 = 'CME'
    #     base_info = [{'exchange': exchange1}, {'exchange': exchange2}, {'exchange': exchange3}]
    #     start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
    #     asyncio.get_event_loop().run_until_complete(
    #         future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
    #     asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
    #     quote_rsp = asyncio.get_event_loop().run_until_complete(
    #         future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
    #                                           start_time_stamp=start_time_stamp))
    #     first_rsp_list = quote_rsp['first_rsp_list']
    #     before_basic_json_list = quote_rsp['before_basic_json_list']
    #     before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
    #
    #     self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
    #     self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
    #     self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MARKET')
    #     self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') is None)
    #     self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
    #     # 响应时间大于接收时间大于请求时间
    #     self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)
    #
    #     self.logger.debug(u'校验静态数据')
    #     self.assertTrue(before_basic_json_list.__len__() > 0)
    #     for info in before_basic_json_list:
    #         instrCode = self.common.searchDicKV(info, 'instrCode')
    #         sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
    #         self.assertTrue(
    #             int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
    #         db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
    #         self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
    #
    #     self.logger.debug(u'校验前快照数据')
    #     self.assertTrue(before_snapshot_json_list.__len__() > 0)
    #     for info in before_snapshot_json_list:
    #         instrCode = self.common.searchDicKV(info, 'instrCode')
    #         sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
    #         self.assertTrue(
    #             int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
    #         db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
    #         self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
    #
    #     self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
    #     info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=1000))
    #     self.assertTrue(info_list.__len__() > 0)
    #     start_time_stamp = int(time.time() * 1000)  # 毫秒级
    #     for info in info_list:
    #         instrCode = self.common.searchDicKV(info, 'instrCode')
    #         sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
    #         self.assertTrue(
    #             int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
    #         db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
    #         self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
    #
    #     self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
    #     info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=1000))
    #     self.assertTrue(info_list.__len__() > 0)
    #     start_time_stamp = int(time.time() * 1000)  # 毫秒级
    #     for info in info_list:
    #         instrCode = self.common.searchDicKV(info, 'instrCode')
    #         sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
    #         self.assertTrue(
    #             int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
    #         db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
    #         self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
    #
    #     self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
    #     info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=3000))
    #     self.assertTrue(info_list.__len__() > 0)
    #     start_time_stamp = int(time.time() * 1000)  # 毫秒级
    #     for info in info_list:
    #         instrCode = self.common.searchDicKV(info, 'instrCode')
    #         sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
    #         self.assertTrue(
    #             int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
    #         db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
    #         self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # -------------------------------------------订阅静态---------------------------------------------------

    def test_QuoteBasicInfo_Msg_001(self):
        """ 订阅单个市场、单个合约的静态数据 """
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_BASIC')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') == code)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

            self.logger.debug(u'前快照数据校验')
            self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

    def test_QuoteBasicInfo_Msg_002(self):
        """ 订阅单个市场、多个合约的静态数据 """
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'静态数据校验')
        self.assertTrue(before_basic_json_list.__len__() == 2)  # 应仅返回两条
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

    def test_QuoteBasicInfo_Msg_003(self):
        """ 传入多个合约code，部分code错误"""
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = 'xxxx'
        code2 = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              recv_num=2, start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]

        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'静态数据校验')
        self.assertTrue(before_basic_json_list.__len__() == 1)  # 仅返回code2的静态数据
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') == code2)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'前快照数据校验')
        self.assertTrue(before_snapshot_json_list.__len__() == 0)  # 不返回快照数据

    # -----------------------------------------订阅快照数据----------------------------------------------------
    def test_QuoteSnapshotApi_01(self):
        """订阅单市场，单合约的快照数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QuoteSnapshotApi_02(self):
        """订阅单市场，多合约的快照数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=1))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 2)
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
        self.logger.debug(u'校验前快照数据')
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_snapshot_json_list[1], 'instrCode'))
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QuoteSnapshotApi_03(self):
        """订阅单市场，多合约的快照数据，部分合约代码为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = None
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_SNAPSHOT')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_SNAPSHOT'))
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # -----------------------------------------订阅盘口数据----------------------------------------------------
    def test_QuoteOrderBookDataApi_01(self):
        """订阅单市场，单合约的盘口数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code = HK_code1
        base_info = [{'exchange': 'HKFE', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 1)
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QuoteOrderBookDataApi_02(self):
        """订阅单市场，多合约盘口数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=1))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() == 2)
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_basic_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_basic_json_list[1], 'instrCode'))
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 2)
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[1], 'instrCode') in [code1, code2])
        self.assertTrue(self.common.searchDicKV(before_snapshot_json_list[0], 'instrCode') != self.common.searchDicKV(
            before_snapshot_json_list[1], 'instrCode'))
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') in (code1, code2))
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QuoteOrderBookDataApi_03(self):
        """订阅单市场，多合约的盘口数据，部分合约代码错误"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code1
        code2 = 'xxxx'
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp, recv_num=2))

        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'subType') == 'SUB_WITH_MSG_DATA')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'childType') == 'SUB_ORDER_BOOK')
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[1], 'startTimeStamp')) - tolerance_time)

        self.logger.debug(u'校验静态数据')
        for info in before_basic_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(int(sourceUpdateTime / (pow(10, 6))) <=
                            start_time_stamp - delay_minute * 60 * 1000)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        for info in before_snapshot_json_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(int(sourceUpdateTime / (pow(10, 6))) <=
                            start_time_stamp - delay_minute * 60 * 1000)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------取消订阅start----------------------------------------------------

    # -------------------------------------------------按合约取消订阅-----------------------------------------------------

    def test_UnInstr03(self):
        """订阅多个，取消订阅其中的一个合约"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnInstr04(self):
        """取消订阅单个合约，合约代码与订阅合约代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnInstr05(self):
        """订阅多个合约，取消订阅多个合约时，其中多个合约代码与订阅的不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code2
        code2 = HK_code1
        code3 = HK_code3
        code4 = 'xxxx'
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3},
                      {'exchange': 'HKFE', 'code': code4}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp))

        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnInstr06(self):
        """按合约取消订阅时，code为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        code1 = HK_code1
        code2 = ''
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # -----------------------------------------按品种取消订阅-------------------------------------------------
    def test_UnProduct03(self):
        """订阅多个，取消订阅其中的一个品种"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'HHI'
        product_code2 = 'MHI'
        base_info1 = [{'exchange': 'HKFE', 'product_code': product_code1},
                      {'exchange': 'HKFE', 'product_code': product_code2}]
        base_info2 = [{'exchange': 'HKFE', 'product_code': product_code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=None, unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnProduct04(self):
        """取消订阅单个品种，品种代码与订阅品种代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'MHI'
        product_code2 = 'HHI'
        product_code3 = 'HSI'
        base_info1 = [{'exchange': 'HKFE', 'product_code': product_code1},
                      {'exchange': 'HKFE', 'product_code': product_code2}]
        base_info2 = [{'exchange': 'HKFE', 'product_code': product_code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        start_time_stamp = int(time.time() * 1000)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp,
            recv_num=100))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnProduct05(self):
        """订阅多个品种，取消订阅多个品种时，其中多个品种代码与订阅的不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'HHI'
        product_code2 = 'MHI'
        product_code3 = 'MCH'
        product_code4 = 'xxx'
        base_info1 = [{'exchange': 'HKFE', 'product_code': product_code1},
                      {'exchange': 'HKFE', 'product_code': product_code2}]
        base_info2 = [{'exchange': 'HKFE', 'product_code': product_code1},
                      {'exchange': 'HKFE', 'product_code': product_code3},
                      {'exchange': 'HKFE', 'product_code': product_code4}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp,
            recv_num=100))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnProduct06(self):
        """按品种取消订阅时，product_code为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        product_code1 = 'MHI'
        product_code2 = ''
        base_info1 = [{'exchange': 'HKFE', 'product_code': product_code1}]
        base_info2 = [{'exchange': 'HKFE', 'product_code': product_code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.UnSubsQutoMsgReqApi(
            unsub_type=sub_type, unchild_type=None, unbase_info=base_info2, start_time_stamp=start_time_stamp,
            recv_num=50))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=300))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # ------------------------------------------------按市场取消订阅--------------------------------------------------------
    def test_UnMarket_003(self):
        """ 按市场取消订阅，exchange为UNKNOWN"""
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MARKET
        child_type = None
        base_info = [{'exchange': HK_exchange}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_MARKET')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == child_type)
        self.assertTrue(before_basic_json_list.__len__() > 0)
        # 再取消订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        base_info = [{'exchange': 'UNKNOWN'}]
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp, recv_num=2000))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=1000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=2000))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnMarket_004(self):
        """ 先按合约订阅，再按市场取消订阅"""
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_INSTR
        child_type = None
        base_info = [{'exchange': 'HKFE', 'code': HK_code1}, {'exchange': 'HKFE', 'code': HK_code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'subType') == 'SUB_WITH_INSTR')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'childType') == child_type)
        self.assertTrue(before_basic_json_list.__len__() > 0)

        # 再取消订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        cancer_sub_type = SubscribeMsgType.SUB_WITH_MARKET
        cancer_base_info = [{'exchange': 'HKFE'}]
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=cancer_sub_type, unbase_info=cancer_base_info,
                                                start_time_stamp=start_time_stamp, recv_num=1000))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=500))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_TRADE_DATA,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # ------------------------------------------取消订阅快照数据---------------------------------------------------

    def test_UnSnapshot_003(self):
        """订阅多个合约快照数据，取消订阅部分快照数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=20, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_004(self):
        """取消订阅之后，再次发起订阅"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                recv_num=300, start_time_stamp=start_time_stamp))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        # 再次发起订阅
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() > 0)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(int(sourceUpdateTime / (pow(10, 6))), start_time_stamp - delay_minute * 60 * 1000)
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_005(self):
        """订阅一个合约的快照数据，取消订阅时，合约代码与订阅合约代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_006(self):
        """订阅一个合约的快照数据，取消订阅时，合约代码错误"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code1
        code2 = 'xxx'
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, recv_num=200))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteBasicInfoApi(recv_num=100))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, sourceUpdateTime)
            self.assertTrue(info == db_json_info)  # 数据与入库记录一致

    def test_UnSnapshot_007(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码与订阅合约代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code2
        code2 = HK_code1
        code3 = HK_code3
        code4 = HK_code4
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3},
                      {'exchange': 'HKFE', 'code': code4}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=20, start_time_stamp=start_time_stamp))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_008(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code2
        code2 = HK_code1
        code3 = None
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_009(self):
        """订阅多个合约快照数据，取消订阅时部分合约代码错误"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        code1 = HK_code2
        code2 = HK_code1
        code3 = 'xxxxx'
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        before_basic_json_list = quote_rsp['before_basic_json_list']
        before_snapshot_json_list = quote_rsp['before_snapshot_json_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_011(self):
        """取消订阅快照数据时，exchange传入UNKNOWN"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = HK_exchange
        code = HK_code1
        base_info1 = [{'exchange': exchange, 'code': code}]
        base_info2 = [{'exchange': 'UNKNOWN', 'code': code}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, recv_num=200))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnSnapshot_012(self):
        """取消订阅快照数据时，code为空"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_SNAPSHOT
        exchange = 'HKFE'
        code1 = HK_code1
        code2 = None
        base_info1 = [{'exchange': exchange, 'code': code1}]
        base_info2 = [{'exchange': exchange, 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, recv_num=200))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # -------------------------------------------------------取消订阅静态数据-------------------------------------------------
    def test_UnQuoteBasicInfo_Msg_004(self):
        """ 先订阅2个合约的静态数据，再取消这2个合约的静态数据，再次订阅"""
        # 先订阅
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_BASIC
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        # 通过调用行情订阅接口，订阅数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 通过调用行情取消订阅接口，取消订阅数据
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 再次订阅静态数据
        start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')
        before_basic_json_list = quote_rsp['before_basic_json_list']

        self.logger.debug(u'校验静态数据')
        self.assertTrue(before_basic_json_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in before_basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # ------------------------------------------------取消订阅盘口数据-----------------------------------------------

    def test_UnQuoteOrderBookDataApi03(self):
        """订阅多个合约盘口数据，取消订阅部分合约数据"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code2
        code2 = HK_code1
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnQuoteOrderBookDataApi04(self):
        """取消订阅之后，再发起订阅"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type, unbase_info=base_info,
                                                recv_num=200, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'判断取消订阅之后，是否还会收到盘口数据，如果还能收到，则测试失败')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

        # 再次发起订阅
        start_time_stamp = int(time.time() * 1000)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnQuoteOrderBookDataApi05(self):
        """订阅一个合约的盘口数据，取消订阅时，合约代码与订阅合约代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code1
        code2 = HK_code2
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnQuoteOrderBookDataApi06(self):
        """订阅一个合约的盘口数据，取消订阅时，合约代码错误"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code1
        code2 = 'xxx'
        base_info1 = [{'exchange': 'HKFE', 'code': code1}]
        base_info2 = [{'exchange': 'HKFE', 'code': code2}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                start_time_stamp=start_time_stamp, recv_num=200))

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnQuoteOrderBookDataApi07(self):
        """订阅多个合约盘口数据，取消订阅时部分合约代码与订阅合约代码不一致"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code2
        code2 = HK_code1
        code3 = HK_code3
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnQuoteOrderBookDataApi08(self):
        """订阅多个合约盘口数据，取消订阅时部分合约代码错误"""
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_MSG_DATA
        child_type = SubChildMsgType.SUB_ORDER_BOOK
        code1 = HK_code2
        code2 = HK_code1
        code3 = 'xxx'
        base_info1 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code2}]
        base_info2 = [{'exchange': 'HKFE', 'code': code1}, {'exchange': 'HKFE', 'code': code3}]
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        quote_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.DelaySubsQutoMsgReqApi(sub_type=sub_type, child_type=child_type, base_info=base_info1,
                                              start_time_stamp=start_time_stamp))
        first_rsp_list = quote_rsp['first_rsp_list']

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        # 取消订阅
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unchild_type=child_type,
                                                unbase_info=base_info2,
                                                recv_num=200, start_time_stamp=start_time_stamp))
        if self.common.searchDicKV(first_rsp_list[0], 'retCode') != 'SUCCESS':
            first_rsp_list = first_rsp_list[::-1]
        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查正确的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过调用行情订阅接口，订阅数据，并检查错误的返回结果')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[1], 'retCode') == 'FAILURE')

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (
                    pow(10, 6))) <= (start_time_stamp - delay_minute * 60 * 1000 + tolerance_time))  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK,
                                                            sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------取消订阅end----------------------------------------------------

if __name__ == '__main_':
    unittest.main()
