# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/7/15
# @Software: PyCharm

import unittest
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from common.common_method import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from pb_files.common_type_def_pb2 import *


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
        self.api = SubscribeApi(delay_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())

    def tearDown(self):
        asyncio.set_event_loop(self.new_loop)
        self.api.client.disconnect()

    # ------------------------------------------登录-----------------------------------------------------------
    def test_LoginReq01(self):
        """正常登陆"""
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
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
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_INVAILD))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq03(self):
        """等待token失效再登陆，登陆失败"""
        time.sleep(60 * 10 + 1)
        self.api = SubscribeApi(delay_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_EXPIRED))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    def test_LoginReq04(self):
        """等待token即将失效再登陆， 登陆成功"""
        time.sleep(60 * 10 - 1)
        self.api = SubscribeApi(delay_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
        start_time_stamp = int(time.time() * 1000)
        frequence = 4
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
                                     frequence=frequence))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
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
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
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
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
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
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
        self.logger.debug("判断是否返回快照数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug("判断是否返回盘口数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

        self.logger.debug("判断是否返回逐笔数据，如果返回则错误")
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=10))
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
        self.assertTrue(self.common.searchDicKV(sec_rsp[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))

    # ----------------------------------------心跳-----------------------------------------
    def test_HearbeatReqApi01(self):
        """登录成功后50秒内发送心跳"""
        asyncio.get_event_loop().run_until_complete(future=self.api.LoginReq(token=self.market_token))
        time.sleep(3)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'connId') == '123')

    def test_HearbeatReqApi02(self):
        """登录成功后，在第一次心跳发送后的50秒内，发送第二次心跳"""
        asyncio.get_event_loop().run_until_complete(future=self.api.LoginReq(token=self.market_token))
        time.sleep(49)
        first_rsp_list1 = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(self.common.searchDicKV(first_rsp_list1[0], 'connId') == '123')
        time.sleep(49)
        first_rsp_list2 = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(self.common.searchDicKV(first_rsp_list2[0], 'connId') == '123')

    # @unittest.skip('耗时较长，先跳过')
    def test_HearbeatReqApi03(self):
        """登录成功后超过50秒发送心跳"""
        asyncio.get_event_loop().run_until_complete(future=self.api.LoginReq(token=self.market_token))
        time.sleep(51)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list.__len__() == 0)

    # @unittest.skip('耗时较长，先跳过')
    def test_HearbeatReqApi04(self):
        """登录成功后，在第一次心跳发送后的50秒外，发送第二次心跳"""
        asyncio.get_event_loop().run_until_complete(future=self.api.LoginReq(token=self.market_token))
        time.sleep(49)
        first_rsp_list1 = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(self.common.searchDicKV(first_rsp_list1[0], 'connId') == '123')
        time.sleep(51)
        first_rsp_list2 = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list2.__len__() == 0)

    # @unittest.skip('不测试')
    def test_HearbeatReqApi05(self):
        """未登录时发送心跳，则无响应"""
        first_rsp_list = asyncio.get_event_loop().run_until_complete(future=self.api.HearbeatReqApi(connid=123))
        self.assertTrue(first_rsp_list.__len__() == 0)

    # -------------------------------------------------------测速-------------------------------------------------------
    def test_VelocityReqApi01(self):
        start_time_stamp = int(time.time() * 1000)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.VelocityReqApi(start_time=start_time_stamp))

        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTime')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'sendTime')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvTime')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTime')))

    # --------------------------------------------------订阅start-------------------------------------------------------

    # --------------------------------------------------订阅分时数据-------------------------------------------------------
    def test_SubscribeKlineMinReqApi_001(self):
        """分时订阅一个合约"""
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
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list: 
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.logger.debug(u'分时订阅，检查返回结果')
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

        self.logger.debug(u'分时订阅，检查返回结果2')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        recv_code_list = []
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            code = self.common.searchDicKV(info, 'code')
            recv_code_list.append(code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致
        self.assertTrue(set(recv_code_list) == {code1, code2})

    def test_SubscribeKlineMinReqApi_010(self):
        """外期 NYMEX分时订阅一个合约"""
        frequence = 100
        exchange = NYMEX_exchange
        code = NYMEX_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKlineMinReqApi_011(self):
        """外期 COMEX 分时订阅一个合约"""
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
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKlineMinReqApi_012(self):
        """外期 CBOT 分时订阅一个合约"""
        frequence = 100
        exchange = CBOT_exchange
        code = CBOT_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKlineMinReqApi_013(self):
        """外期 CME 分时订阅一个合约"""
        frequence = 100
        exchange = CME_exchange
        code = CME_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致


    def test_SubscribeKlineMinReqApi_014(self):
        """外期 SGX 分时订阅一个合约"""
        frequence = 100
        exchange = SGX_exchange
        code = SGX_code1
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'分时订阅，检查返回结果')
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------取消订阅分时数据-------------------------------------------------------

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
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retMsg') == 'instr have no subscribe')
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKlineMinReqApi_010(self):
        """外期 NYMEX 分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = NYMEX_exchange
        code = NYMEX_code1
        code2 = NYMEX_code2
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKlineMinReqApi_011(self):
        """外期 COMEX 分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = COMEX_exchange
        code = COMEX_code1
        code2 = COMEX_code2
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKlineMinReqApi_012(self):
        """外期 CBOT 分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = CBOT_exchange
        code = CBOT_code2
        code2 = CBOT_code1
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKlineMinReqApi_013(self):
        """外期 CME 分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = CME_exchange
        code = CME_code1
        code2 = CME_code2
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKlineMinReqApi_014(self):
        """外期 SGX 分时订阅一个合约,取消订阅一个未订阅的合约"""
        frequence = 100
        exchange = SGX_exchange
        code = SGX_code1
        code2 = SGX_code2
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
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------K线订阅----------------------------------------------
    def test_SubscribeKLineMsgReqApi_001(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_002(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.THREE_MIN"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.THREE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 3) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_003(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.FIVE_MIN"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 5) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_004(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.FIFTEEN_MIN"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.FIFTEEN_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 15) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_005(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.THIRTY_MIN"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.THIRTY_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 30) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_006(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.HOUR"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 60) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_007(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.TWO_HOUR"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.TWO_HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 120) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_008(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.FOUR_HOUR"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.FOUR_HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 240) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_009(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.DAY"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.DAY
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_010(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.WEEK"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.WEEK
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_011(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.MONTH"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.MONTH
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_012(self):
        """订阅单个合约的K线: peroid_type = KLinePeriodType.YEAR"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        base_info = [{'exchange': exchange, 'code': code}]
        peroid_type = KLinePeriodType.YEAR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeKLineMsgReqApi_013(self):
        """订阅多个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code}, {'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        code_list = []
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            instr_code = self.common.searchDicKV(info, 'code')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instr_code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致
            code_list.append(instr_code)
        self.assertTrue(set(code_list) == {code, code2})

    def test_SubscribeKLineMsgReqApi_014(self):
        """订阅多个合约的K线: peroid_type = KLinePeriodType.MINUTE, 其中一个合约名词错误"""
        frequence = 100
        exchange = HK_exchange
        code = HK_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange, 'code': code}, {'exchange': exchange, 'code': code2}]
        peroid_type = KLinePeriodType.MINUTE
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        rsp_list =asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info, start_time_stamp=start_time_stamp, recv_num=3))

        if self.common.searchDicKV(rsp_list[0], 'retCode') != 'SUCCESS':
            rsp_list = rsp_list[::-1]
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.assertTrue(self.common.searchDicKV(rsp_list[1], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[1], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[1], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[1], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[1], 'startTimeStamp')))
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------取消K线订阅-------------------------------------------
    def test_UnsubscribeKLineMsgReqApi_001(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
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
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_002(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.THREE_MIN"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.THREE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 3) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_003(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.FIVE_MIN"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.FIVE_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 5) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_004(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.FIFTEEN_MIN"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.FIFTEEN_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 15) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_005(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.THIRTY_MIN"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.THIRTY_MIN
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 30) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_006(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.HOUR"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 60) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_007(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.TWO_HOUR"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.TWO_HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 120) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_008(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.FOUR_HOUR"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.FOUR_HOUR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 240) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_009(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.DAY"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.DAY
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_010(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.WEEK"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.WEEK
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_011(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.MONTH"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.MONTH
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_012(self):
        """订阅两个合约，取消订阅其中一个合约的K线: peroid_type = KLinePeriodType.YEAR"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        base_info = [{'exchange': exchange, 'code': code1}, {'exchange': exchange, 'code': code2}]
        cancer_base_info = [{'exchange': exchange, 'code': code1}]
        peroid_type = KLinePeriodType.YEAR
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        # 先订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                      start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeKLineMsgReqApi_013(self):
        """订阅1个合约，取消订阅但取消失败: peroid_type = KLinePeriodType.MINUTE"""
        frequence = 100
        exchange = HK_exchange
        code1 = HK_code1
        code2 = 'xxxx'
        base_info = [{'exchange': exchange, 'code': code1}]
        cancer_base_info = [{'exchange': exchange, 'code': code2}]
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
        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        # 再取消订阅
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnsubscribeKLineMsgReqApi(peroid_type=peroid_type, base_info=cancer_base_info,
                                                    start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收K线数据的接口，筛选出K线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code1)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code1, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, period_type=peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------订阅逐笔成交数据---------------------------------------
    def test_SubscribeTradeTickReqApi_001(self):
        """订阅一个合约的逐笔: frequence=None"""
        frequence = None
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
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code)
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        recv_code_list = []
        for info in info_list:
            code = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
            recv_code_list.append(code)
        self.assertTrue(set(recv_code_list) == {code1, code2})
        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)
        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_SubscribeTradeTickReqApi_010(self):
        """ 外期 NYMEX 订阅一个合约的逐笔"""
        frequence = None
        exchange = NYMEX_exchange
        code = NYMEX_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeTradeTickReqApi_011(self):
        """ 外期 COMEX 订阅一个合约的逐笔"""
        frequence = None
        exchange = COMEX_exchange
        code = COMEX_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeTradeTickReqApi_012(self):
        """ 外期 CBOT 订阅一个合约的逐笔"""
        frequence = None
        exchange = CBOT_exchange
        code = CBOT_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeTradeTickReqApi_013(self):
        """ 外期 CME 订阅一个合约的逐笔"""
        frequence = None
        exchange = CME_exchange
        code = CME_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_SubscribeTradeTickReqApi_014(self):
        """ 外期 SGX 订阅一个合约的逐笔"""
        frequence = None
        exchange = SGX_exchange
        code = SGX_code1
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
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------取消订阅逐笔成交数据-------------------------------------------------------
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(rsp_list[0], 'code') == code2)

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeTradeTickReqApi_010(self):
        """外期 NYMEX 订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = NYMEX_exchange
        code1 = NYMEX_code2
        code2 = NYMEX_code1
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeTradeTickReqApi_011(self):
        """外期 COMEX 订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = NYMEX_exchange
        code1 = NYMEX_code1
        code2 = NYMEX_code2
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeTradeTickReqApi_012(self):
        """外期 CBOT 订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = CBOT_exchange
        code1 = CBOT_code2
        code2 = CBOT_code1
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeTradeTickReqApi_013(self):
        """外期 CME 订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = CME_exchange
        code1 = CME_code1
        code2 = CME_code2
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_UnsubscribeTradeTickReqApi_014(self):
        """外期 CME 订阅两个合约的逐笔，再取消其中一个的合约的逐笔"""
        frequence = 100
        exchange = SGX_exchange
        code1 = SGX_code1
        code2 = SGX_code2
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

        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20, recv_timeout_sec=21))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp -
                            delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code2, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------订阅手机图表数据(手机专用)-------------------------------
    def test_StartCharDataReq_001(self):
        """分时页面请求订阅一个合约，frequence=4"""
        exchange = HK_exchange
        code = HK_code1
        frequence = 1
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
        self.assertTrue(app_rsp['exchange'] == 'HKFE')
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(sourceUpdateTime / (pow(10, 6)) - (start_time_stamp - delay_minute * 60 * 1000))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_002(self):
        """分时页面请求订阅一个合约，frequence=0(当成9999处理)"""
        exchange = HK_exchange
        code = HK_code1
        frequence = 0
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
        self.assertTrue(app_rsp['exchange'] == 'HKFE')
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_008(self):
        """分时页面请求订阅一个合约，frequence=100,再订阅第二个合约"""
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')

        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果2')
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
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据2')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据2')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=200))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        recv_code_list = []
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
            recv_code_list.append(instrCode)
        self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=200))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        recv_code_list = []
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
            recv_code_list.append(instrCode)
        self.assertTrue(set(recv_code_list) == {code1, code2})

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_010(self):
        """外期 NYMEX 分时页面请求订阅一个合约，frequence=None"""
        exchange = NYMEX_exchange
        code = NYMEX_code1
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
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_011(self):
        """外期 COMEX 分时页面请求订阅一个合约，frequence=None"""
        exchange = COMEX_exchange
        code = COMEX_code1
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
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(sourceUpdateTime / (pow(10, 6)) - (start_time_stamp - delay_minute * 60 * 1000))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_012(self):
        """外期 CBOT 分时页面请求订阅一个合约，frequence=None"""
        exchange = CBOT_exchange
        code = CBOT_code1
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
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(sourceUpdateTime / (pow(10, 6)) - (start_time_stamp - delay_minute * 60 * 1000))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_013(self):
        """外期 CME 分时页面请求订阅一个合约，frequence=None"""
        exchange = CME_exchange
        code = CME_code1
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
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(sourceUpdateTime / (pow(10, 6)) - (start_time_stamp - delay_minute * 60 * 1000))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    def test_StartCharDataReq_014(self):
        """外期 SGX 分时页面请求订阅一个合约，frequence=None"""
        exchange = SGX_exchange
        code = SGX_code1
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
        self.assertTrue(app_rsp['code'] == code)
        self.assertTrue(app_rsp['exchange'] == exchange)
        basic_json_list = [app_rsp['basicData']]
        before_snapshot_json_list = [app_rsp['snapshot']]
        before_orderbook_json_list = [app_rsp['orderbook']]
        self.logger.debug(u'校验静态数据值')
        self.assertTrue(basic_json_list.__len__() == 1)
        for info in basic_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateTimestamp'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_BASIC, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前快照数据')
        self.assertTrue(before_snapshot_json_list.__len__() == 1)
        for info in before_snapshot_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'校验前盘口数据')
        self.assertTrue(before_orderbook_json_list.__len__() == 1)
        for info in before_orderbook_json_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)  # 毫秒级
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            print(sourceUpdateTime / (pow(10, 6)) - (start_time_stamp - delay_minute * 60 * 1000))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推逐笔数据

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=50))
        self.assertTrue(info_list.__len__() == 0)  # 不主推分时数据

    # --------------------------------------------------取消订阅手机图表数据(手机专用)-------------------------------

    def test_StopChartDataReqApi_002(self):
        """订阅2个合约,停止请求其中一个的分时页面数据"""
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        frequence = 100
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'通过调用请求分时页面数据接口，订阅数据，并检查返回结果')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code1, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StartChartDataReqApi(exchange, code2, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS')
        self.logger.debug(u'取消订阅分时页面数据')
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

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code2)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_StopChartDataReqApi_004(self):
        """停止请求分时页面数据,exchange传入UNKNOWN"""
        exchange = HK_exchange
        exchange2 = 'UNKNOWN'
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
        start_time_stamp = int(time.time() * 1000)
        self.logger.debug(u'取消订阅分时页面数据')
        app_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.StopChartDataReqApi(exchange2, code, start_time_stamp))
        self.assertTrue(app_rsp_list.__len__() == 1)
        app_rsp = app_rsp_list[0]
        self.assertTrue(self.common.searchDicKV(app_rsp, 'retCode') == 'FAILURE')
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于开始测速时间
        self.assertTrue(int(self.common.searchDicKV(app_rsp, 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(app_rsp, 'startTimeStamp')))
        self.assertTrue(app_rsp['code'] == code)

        self.logger.debug(u'通过接收快照数据的接口，筛选出快照数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_SNAPSHOT, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'通过接收盘口数据的接口，筛选出盘口数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteOrderBookDataApi(recv_num=50))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            instrCode = self.common.searchDicKV(info, 'instrCode')
            self.assertTrue(instrCode == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(instrCode, QuoteMsgType.PUSH_ORDER_BOOK, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------查询当日分时数据-------------------------------------------------------
    def test_QueryKLineMinMsgReqApi_001(self):
        """分时查询： isSubKLineMin = True"""
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
        for info in info_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        start_time_stamp = int(time.time() * 1000)
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMinMsgReqApi_002(self):
        """分时查询： isSubKLineMin = False"""
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
        for info in info_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryKLineMinMsgReqApi_003(self):
        """分时查询： isSubKLineMin = True, 订阅两个合约"""
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
        self.logger.debug(u'分时数据查询，检查返回结果')
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
        for info in info_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'查询第二个合约')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code2, query_type, direct, start, end,
                                                   vol,
                                                   start_time_stamp))
        query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list']
        sub_kline_min_rsp_list = final_rsp['sub_kline_min_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_min_rsp_list[0], 'code') == code2)
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
        for info in info_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        start_time_stamp = int(time.time() * 1000)
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=100))
        recv_code_list = []
        for info in info_list:
            code = self.common.searchDicKV(info, 'code')
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致
            recv_code_list.append(code)
        self.assertTrue(set(recv_code_list) == {code1, code2})

    def test_QueryKLineMinMsgReqApi_004(self):
        """分时查询： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = True
        exchange = CBOT_exchange
        code = CBOT_code1
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
        for info in info_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        start_time_stamp = int(time.time() * 1000)
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------查询五日分时数据-------------------------------------------------------

    def test_QueryFiveDaysKLineMinReqApi_001(self):
        """五日分时查询： isSubKLineMin = True"""
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
        for i in range(len(day_data_list)):
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            for info in info_list:
                self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == HK_exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info['data'][0], 'updateDateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE_MIN, sourceUpdateTime)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryFiveDaysKLineMinReqApi_002(self):
        """五日分时查询： isSubKLineMin = False"""
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
        for i in range(len(day_data_list)):
            info_list = self.common.searchDicKV(day_data_list[i], 'data')
            for info in info_list:
                self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                            delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收分时数据的接口，筛选出分时数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineMinDataApi(recv_num=10))
        self.assertTrue(info_list.__len__() == 0)

    # --------------------------------------------------查询历史K线-------------------------------------------------------
    def test_QueryKLineMsgReqApi_001(self):
        """K线查询: BY_DATE_TIME, 1分K, 前20分钟的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime, peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_002(self):
        """K线查询: BY_DATE_TIME, 3分K, 前30分钟的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.THREE_MIN
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 30 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 3) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 3) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 40 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 5) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 5) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 45 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 15) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 15) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 30) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 30) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 60) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                            delay_minute - 60) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 120) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 120) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 240) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 240) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_009(self):
        """K线查询: BY_DATE_TIME, 日K, 前2天的数据, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 2 * 24 * 60 * 60 * 1000
        end = start_time_stamp + 2 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)
        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_012(self):
        """K线查询: BY_DATE_TIME, 1分K, 前60分钟的数据, isSubKLine = False, frequence=100"""
        frequence = 100
        isSubKLine = False
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MINUTE
        query_type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.UNKNOWN_QUERY_DIRECT
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(sub_kline_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口,此时获取不到K线数据')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=100))
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 1) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 3) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 3) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 5) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 5) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 15) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 15) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_017(self):
        """K线查询: BY_DATE_TIME, 30分K, 向前查询10根K线, isSubKLine = True, frequence=100"""
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 30) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 30) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 60) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 60) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 120) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 120) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                    delay_minute - 240) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (
                        delay_minute - 240) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        vol = 1
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MINUTE')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 1) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                            delay_minute - 3) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THREE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 3) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 5) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIVE_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 5) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 15) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FIFTEEN_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 15) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_028(self):
        """K线查询: BY_DATE_TIME, 30分K, 向后查询10根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code3
        peroid_type = KLinePeriodType.THIRTY_MIN
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 30) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'THIRTY_MIN')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 30) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 60) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 60) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 120) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'TWO_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 120) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - (
                        delay_minute - 240) * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'FOUR_HOUR')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - (delay_minute - 240) * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_032(self):
        """K线查询: BY_VOL, 日K, 向后获取2根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.DAY
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'DAY')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

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
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'WEEK')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryKLineMsgReqApi_034(self):
        """K线查询: BY_DATE_TIME, 月K, 向后获取1根K线, isSubKLine = True, frequence=100"""
        frequence = 100
        isSubKLine = True
        exchange = HK_exchange
        code = HK_code1
        peroid_type = KLinePeriodType.MONTH
        query_type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start = start_time_stamp - 3 * 24 * 60 * 60 * 1000
        end = None
        vol = 1
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
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'retMsg') == 'query kline msg success')
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_kline_rsp_list[0], 'code') == code)

        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_kline_rsp_list[0], 'retMsg') == 'Subscribe KLine success')

        self.logger.debug(u'校验回包里的历史k线数据')
        k_data_list = self.common.searchDicKV(query_kline_rsp_list[0], 'kData')
        self.assertTrue(k_data_list.__len__() == vol)
        for info in k_data_list:
            self.assertTrue(
                self.common.changeStrTimeToStamp(info['updateDateTime']) <= start_time_stamp - delay_minute * 60 * 1000)

        self.logger.debug(u'通过接收k线数据的接口，筛选出k线数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.PushKLineDataApi(recv_num=20))
        self.assertTrue(info_list.__len__() > 0)
        start_time_stamp = int(time.time() * 1000)
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == exchange)
            self.assertTrue(self.common.searchDicKV(info, 'code') == code)
            self.assertTrue(self.common.searchDicKV(info, 'peroidType') == 'MONTH')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'updateDateTime'))
            self.assertTrue(
                self.common.changeStrTimeToStamp(sourceUpdateTime) <= start_time_stamp - delay_minute * 60 * 1000)
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_KLINE, sourceUpdateTime,
                                                            peroid_type)
            self.assertTrue(self.common.compareKData(info, db_json_info))  # 数据与入库记录一致

    # --------------------------------------------------逐笔成交查询-------------------------------------------------------
    def test_QueryTradeTickMsgReqApi_001(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔15分钟, isSubTrade = True, frequence=2"""
        frequence = 2
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        # exchange = CME_exchange
        # code = CME_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (delay_minute + 5) * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10, 6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_002(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔10分钟, isSubTrade = True, frequence=None"""
        frequence = None
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (delay_minute + 5) * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_003(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔5分钟, isSubTrade = False, frequence=100"""
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (delay_minute + 5) * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_004(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔0分钟, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - delay_minute * 60 * 1000
        end_time = start_time
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_005(self):
        """逐笔成交查询: BY_DATE_TIME,时间间隔-5分钟, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code2
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (5 + delay_minute) * 60 * 1000
        end_time = start_time_stamp - (10 + delay_minute) * 60 * 1000
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'FAILURE')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retMsg') == 'query condition error')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)

        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0])

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_006(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间的前10分钟-前5分钟, isSubTrade = False, frequence=100"""
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (10 + delay_minute) * 60 * 1000
        end_time = start_time_stamp - (5 + delay_minute) * 60 * 1000
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_007(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔5分钟, isSubTrade = True, frequence=100; 订阅两个合约"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        type = QueryKLineMsgType.BY_DATE_TIME
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (5 + delay_minute) * 60 * 1000
        end_time = start_time_stamp
        vol = None
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code1, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code1)
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code1, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'开始订阅第二个合约:')
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - 5 * 60 * 1000
        end_time = start_time_stamp
        vol = None
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code2, type, direct, start_time, end_time, vol, start_time_stamp, recv_num=100))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code2)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code2)
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据2')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验2')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        recv_code_list = []

        for info in info_list:
            code = self.common.searchDicKV(info, 'instrCode')
            recv_code_list.append(code)
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致
        self.assertTrue(set(recv_code_list) == {code1, code2})

    def test_QueryTradeTickMsgReqApi_008(self):
        """逐笔成交查询: BY_VOL,direct=WITH_FRONT, vol=100,起始时间为当前时间, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
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
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_009(self):
        """逐笔成交查询: BY_VOL,direct=WITH_FRONT, vol=100,起始时间为当前时间, isSubTrade = False, frequence=100"""
        frequence = 100
        isSubTrade = False
        exchange = HK_exchange
        code = HK_code1
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
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code)
        self.assertTrue(final_rsp['sub_trade_tick_rsp_list'].__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

    def test_QueryTradeTickMsgReqApi_010(self):
        """逐笔成交查询: BY_VOL,direct=WITH_FRONT, vol=100,起始时间为过去5分钟, isSubTrade = True, frequence=100"""
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
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_011(self):
        """逐笔成交查询: BY_VOL,direct=WITH_FRONT, vol=100,起始时间为未来10分钟, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + 10 * 60 * 1000
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_012(self):
        """逐笔成交查询: BY_VOL,direct=WITH_BACK, vol=100,起始时间为过去10分钟, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (10 + delay_minute) * 60 * 1000
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_013(self):
        """逐笔成交查询: BY_VOL,direct=WITH_BACK, vol=100000,起始时间为过去1分钟, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (1 + delay_minute) * 60 * 1000
        end_time = None
        vol = 100000
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        self.assertTrue(tick_data_list.__len__() < vol)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_014(self):
        """逐笔成交查询: BY_VOL,direct=WITH_BACK, vol=100,起始时间为未来时间, isSubTrade = True, frequence=100"""
        frequence = 100
        isSubTrade = True
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp + (10 + delay_minute) * 60 * 1000
        end_time = None
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp))
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
        self.assertTrue('tickData' not in query_trade_tick_rsp_list[0].keys())

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_015(self):
        """逐笔成交查询: BY_DATE_TIME,与当前时间间隔10分钟, isSubTrade = True, frequence=100;
        再订阅第二个合约：BY_VOL,direct=WITH_FRONT, vol=100,起始时间为当前时间, isSubTrade = False, frequence=100"""
        frequence = 100
        isSubTrade = True
        isSubTrade2 = False
        exchange = HK_exchange
        code1 = HK_code1
        code2 = HK_code2
        type = QueryKLineMsgType.BY_DATE_TIME
        type2 = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp - (10 + delay_minute) * 60 * 1000
        start_time2 = start_time_stamp - delay_minute * 60 * 1000
        end_time = start_time_stamp
        vol = 100
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code1, type, direct, start_time, end_time, vol, start_time_stamp))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code1)

        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'code') == code1)
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接收时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(sub_trade_tick_rsp_list[0], 'startTimeStamp')))

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() > 0)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code1, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

        self.logger.debug(u'开始订阅第二个合约:')
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.QueryTradeTickMsgReqApi(isSubTrade2, exchange, code2, type2, direct, start_time2, end_time, vol, start_time_stamp, recv_num=100))
        query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']
        sub_trade_tick_rsp_list = final_rsp['sub_trade_tick_rsp_list']
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS')
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'exchange') == exchange)
        self.assertTrue(self.common.searchDicKV(query_trade_tick_rsp_list[0], 'code') == code2)
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)

        self.logger.debug(u'校验回包里的历史逐笔数据')
        tick_data_list = self.common.searchDicKV(query_trade_tick_rsp_list[0], 'tickData')
        self.assertTrue(tick_data_list.__len__() == vol)
        for info in tick_data_list:
            sourceUpdateTime = int(self.common.searchDicKV(info, 'time'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟

        self.logger.debug(u'通过接收逐笔数据的接口，筛选出逐笔数据,并校验')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteTradeDataApi(recv_num=20))
        start_time_stamp = int(time.time() * 1000)
        self.assertTrue(info_list.__len__() > 0)
        self.assertTrue(self.common.checkFrequence(info_list, frequence))
        for info in info_list:
            self.assertTrue(self.common.searchDicKV(info, 'exchange') == 'HKFE')
            self.assertTrue(self.common.searchDicKV(info, 'instrCode') == code1)
            sourceUpdateTime = int(self.common.searchDicKV(info, 'sourceUpdateTime'))
            self.assertTrue(
                int(sourceUpdateTime / (pow(10,
                                            6))) <= start_time_stamp - delay_minute * 60 * 1000 + tolerance_time)  # 毫秒级别对比，延迟delay_minute分钟
            db_json_info = self.api.sq.get_subscribe_record(code1, QuoteMsgType.PUSH_TRADE_DATA, sourceUpdateTime)
            self.assertTrue(self.common.compareSubData(info, db_json_info))  # 数据与入库记录一致

    def test_QueryTradeTickMsgReqApi_025(self):
        """逐笔成交查询: isSubTrade = None时则不订阅"""
        frequence = 2
        isSubTrade = None
        exchange = HK_exchange
        code = HK_code1
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_BACK
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
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
        self.assertTrue(sub_trade_tick_rsp_list.__len__() == 0)
        self.logger.debug(u'通过接收快照数据接口，筛选出快照数据，并校验。')
        info_list = asyncio.get_event_loop().run_until_complete(future=self.api.QuoteSnapshotApi(recv_num=100))
        self.assertTrue(info_list.__len__() == 0)

# --------------------------------------------查询品种交易状态（不延迟）------------------------------------------------

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
        self.assertTrue(datas.__len__() == 5)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']

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
        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == 4)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']

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
        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == 6)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']

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
        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == 14)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']

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
        datas = first_rsp_list[0]['data']
        self.assertTrue(datas.__len__() == 3)
        for data in datas:
            self.assertTrue(data['exchange'] == exchange)
            product_code = data['productCode']
            status = data['status']
            time_stamp = data['timeStamp']

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

        self.logger.debug(u'检查返回数据')
        self.assertTrue(self.common.searchDicKV(first_rsp_list[0], 'retCode') == 'FAILURE')
