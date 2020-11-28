# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/10/10
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

    # --------------------------------------------------登录-----------------------------------------------------------
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
            self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_INVAILD))
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
        # 响应时间大于接受时间大于请求时间
        self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
                        int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))

    # def test_LoginReq03(self):
    #     """等待token失效再登陆，登陆失败"""
    #     time.sleep(60 * 10 + 1)
    #     self.api = SubscribeApi(delay_ws_url, self.new_loop)
    #     asyncio.get_event_loop().run_until_complete(
    #         future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
    #     start_time_stamp = int(time.time() * 1000)
    #     frequence = 4
    #     first_rsp_list = asyncio.get_event_loop().run_until_complete(
    #         future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
    #     self.assertTrue(
    #         self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_FAILD))
    #     self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
    #     # 响应时间大于接受时间大于请求时间
    #     self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
    #
    # def test_LoginReq04(self):
    #     """等待token即将失效再登陆， 登陆成功"""
    #     time.sleep(60 * 10 - 1)
    #     self.api = SubscribeApi(delay_ws_url, self.new_loop)
    #     asyncio.get_event_loop().run_until_complete(
    #         future=self.api.client.ws_connect())  # 重连以确保连接不会超时退出
    #     start_time_stamp = int(time.time() * 1000)
    #     frequence = 4
    #     first_rsp_list = asyncio.get_event_loop().run_until_complete(
    #         future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp,
    #                                  frequence=frequence))
    #     self.assertTrue(
    #         self.common.searchDicKV(first_rsp_list[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))
    #     self.assertTrue(int(self.common.searchDicKV(
    #         first_rsp_list[0], 'startTimeStamp')) == start_time_stamp)
    #     # 响应时间大于接受时间大于请求时间
    #     self.assertTrue(int(self.common.searchDicKV(first_rsp_list[0], 'rspTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'recvReqTimeStamp')) >=
    #                     int(self.common.searchDicKV(first_rsp_list[0], 'startTimeStamp')))
    #
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

    #  -------------------------------------------------退出---------------------------------------------------------

    def test_LogoutReq01(self):
        """登陆后退出"""
        start_time_stamp = int(time.time() * 1000)
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp))
        self.assertTrue(first_rsp_list == [])   # 退出登陆即断连无消息接收

    def test_LogoutReq02(self):
        """未登录时，退出登录"""
        start_time_stamp = int(time.time() * 1000)
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=self.api.LogoutReq(start_time_stamp=start_time_stamp))
        self.assertTrue(first_rsp_list == [])   # 退出登陆即断连无消息接收

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
        self.assertTrue(first_rsp_list == [])   # 退出登陆即断连无消息接收

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
        self.assertTrue(first_rsp_list == [])   # 退出登陆即断连无消息接收
        self.setUp()
        sec_rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp))
        self.assertTrue(self.common.searchDicKV(
            sec_rsp[0], 'retCode') == RetCode.Name(RetCode.CHECK_TOKEN_SUCCESS))

    # --------------------------------------------------心跳-----------------------------------------
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

    # --------------------------------------------------测速-------------------------------------------------------
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

