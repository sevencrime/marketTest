# -*- coding: utf-8 -*-
# !/usr/bin/python


import asyncio
import time
import unittest

import allure
import pytest

from common.common_method import Common
from common.test_log.ed_log import get_log
from test_config import *
from websocket_py3.ws_api.subscribe_api_for_second_phase import *

@pytest.fixture()
def SZ_api():
    loop = asyncio.get_event_loop()
    uri = "ws://120.79.42.118:11516"
    api = SubscribeApi(uri, loop)
    loop.run_until_complete(future=api.client.ws_connect())
    yield api
    api.client.disconnect()
    if loop.is_closed():
        loop.close()


@pytest.fixture()
def HK_api():
    loop = asyncio.get_event_loop()
    uri = "ws://47.242.137.135:11516"
    api = SubscribeApi(uri, loop)
    loop.run_until_complete(future=api.client.ws_connect())
    yield api
    api.client.disconnect()
    if loop.is_closed():
        loop.close()


@allure.feature("对比深圳和香港环境的数据")
@pytest.mark.usefixtures("SZ_api", "HK_api")
class Test_Comtrast_PRD():

    common = Common()
    logger = get_log()
    market_token = None

    @pytest.mark.parametrize(
        "exchange, code", [
            ("SEHK", "00700"),
            ("SEHK", SEHK_indexCode1),
            (ASE_exchange, ASE_code1),
            (NASDAQ_exchange, NASDAQ_code1),
            (NYSE_exchange, NYSE_code1),
            (HK_exchange, HK_main1),
            (NYMEX_exchange, NYMEX_code1),
        ]
    )
    def test_contrast_StartChartDataReq(self, SZ_api, HK_api, exchange, code):
        """订阅手机图表数据(手机专用)--订阅一个港股，frequence=4"""
        # exchange = SEHK_exchange
        # code = "00700"

        exchange = exchange
        code = code

        frequence = None
        start_time_stamp = int(time.time() * 1000)

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            future=SZ_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(SZ_api.hearbeat_job(), loop)
        self.logger.debug(u'订阅深圳--手机图表')
        sz_rsp_list = loop.run_until_complete(
            future=SZ_api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))

        app_rsp = sz_rsp_list[0]
        assert self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS'
        sz_basic_json_list = app_rsp['basicData']
        sz_before_snapshot_json_list = app_rsp['snapshot']
        sz_before_orderbook_json_list = []
        if self.common.searchDicKV(sz_before_snapshot_json_list, "dataType") != "EX_INDEX":
            sz_before_orderbook_json_list = app_rsp['orderbook']

        del sz_basic_json_list["commonInfo"]
        del sz_before_snapshot_json_list["commonInfo"]

        loop.run_until_complete(
            future=HK_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(HK_api.hearbeat_job(), loop)
        self.logger.debug(u'订阅香港--手机图表')
        hk_rsp_list = loop.run_until_complete(
            future=HK_api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))

        app_rsp = hk_rsp_list[0]
        assert self.common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS'
        hk_basic_json_list = app_rsp['basicData']
        hk_before_snapshot_json_list = app_rsp['snapshot']
        hk_before_orderbook_json_list = []
        if self.common.searchDicKV(hk_before_snapshot_json_list, "dataType") != "EX_INDEX":
            hk_before_orderbook_json_list = app_rsp['orderbook']

        del hk_basic_json_list["commonInfo"]
        del hk_before_snapshot_json_list["commonInfo"]

        assert sz_basic_json_list == hk_basic_json_list
        assert sz_before_snapshot_json_list == hk_before_snapshot_json_list
        if sz_before_orderbook_json_list or hk_before_orderbook_json_list:
            del sz_before_orderbook_json_list["commonInfo"]
            del hk_before_orderbook_json_list["commonInfo"]
            assert sz_before_orderbook_json_list == hk_before_orderbook_json_list

    @pytest.mark.parametrize(
        "exchange, code", [
            ("SEHK", "00700"),
            ("SEHK", SEHK_indexCode1),
            (ASE_exchange, ASE_code1),
            (NASDAQ_exchange, NASDAQ_code1),
            (NYSE_exchange, NYSE_code1),
            (HK_exchange, HK_main1),
            (NYMEX_exchange, NYMEX_code1),
        ]
    )
    def test_contrast_QueryKLineMinMsgReqApi(self, SZ_api, HK_api, exchange, code):
        """分时查询--查询并订阅港股的分时数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = False
        exchange = exchange
        code = code

        query_type = QueryKLineMsgType.UNKNOWN_QUERY_KLINE  # app 订阅服务该字段无意义
        direct = QueryKLineDirectType.WITH_BACK  # app 订阅服务该字段无意义
        start = 0  # app 订阅服务该字段无意义
        end = 0  # app 订阅服务该字段无意义
        vol = 0  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            future=SZ_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(SZ_api.hearbeat_job(), loop)
        self.logger.debug(u'查询深圳分时数据')
        final_rsp = loop.run_until_complete(
            future=SZ_api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))

        sz_query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list'][0]

        assert self.common.searchDicKV(sz_query_kline_min_rsp_list, 'retCode') == 'SUCCESS'

        loop.run_until_complete(
            future=HK_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(HK_api.hearbeat_job(), loop)
        self.logger.debug(u'查询深圳分时数据')
        final_rsp = loop.run_until_complete(
            future=HK_api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end,
                                                   vol, start_time_stamp))

        hk_query_kline_min_rsp_list = final_rsp['query_kline_min_rsp_list'][0]

        assert self.common.searchDicKV(hk_query_kline_min_rsp_list, 'retCode') == 'SUCCESS'

        assert sz_query_kline_min_rsp_list.get("data") == hk_query_kline_min_rsp_list.get("data")

    @pytest.mark.parametrize(
        "exchange, code", [
            ("SEHK", "00700"),
            ("SEHK", SEHK_indexCode1),
            (ASE_exchange, ASE_code1),
            (NASDAQ_exchange, NASDAQ_code1),
            (NYSE_exchange, NYSE_code1),
            (HK_exchange, HK_main1),
            (NYMEX_exchange, NYMEX_code1),
        ]
    )
    def test_contrast_QueryFiveDaysKLineMinReqApi(self, SZ_api, HK_api, exchange, code):
        """五日分时查询, 查询并订阅数据： isSubKLineMin = True"""
        frequence = 100
        isSubKLineMin = False
        exchange = exchange
        code = code
        start = None  # app 订阅服务该字段无意义
        start_time_stamp = int(time.time() * 1000)

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        # 深圳
        loop.run_until_complete(
            future=SZ_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(SZ_api.hearbeat_job(), loop)
        final_rsp = loop.run_until_complete(
            future=SZ_api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        sz_query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list'][0]
        assert self.common.searchDicKV(sz_query_5day_klinemin_rsp_list, 'retCode') == 'SUCCESS'

        # 香港
        loop.run_until_complete(
            future=HK_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(HK_api.hearbeat_job(), loop)
        final_rsp = loop.run_until_complete(
            future=HK_api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp))
        hk_query_5day_klinemin_rsp_list = final_rsp['query_5day_klinemin_rsp_list'][0]
        assert self.common.searchDicKV(hk_query_5day_klinemin_rsp_list, 'retCode') == 'SUCCESS'

        assert sz_query_5day_klinemin_rsp_list.get("hk_query_5day_klinemin_rsp_list") == hk_query_5day_klinemin_rsp_list.get("hk_query_5day_klinemin_rsp_list")

    @pytest.mark.parametrize(
        "exchange, code", [
            ("SEHK", "00700"),
            ("SEHK", SEHK_indexCode1),
            (ASE_exchange, ASE_code1),
            (NASDAQ_exchange, NASDAQ_code1),
            (NYSE_exchange, NYSE_code1),
            (HK_exchange, HK_main1),
            (NYMEX_exchange, NYMEX_code1),
        ]
    )
    def test_contrast_QueryKLineMsgReqApi(self, SZ_api, HK_api, exchange, code):
        """K线查询港股: 按BY_DATE_TIME方式查询, 1分K, 前一小时的数据, 并订阅K线数据"""
        frequence = None
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

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            future=SZ_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(SZ_api.hearbeat_job(), loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = loop.run_until_complete(
            future=SZ_api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        sz_query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        assert self.common.searchDicKV(sz_query_kline_rsp_list[0], 'retCode') == 'SUCCESS'


        loop.run_until_complete(
            future=HK_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(HK_api.hearbeat_job(), loop)
        self.logger.debug(u'查询K线数据，并检查返回结果')
        final_rsp = loop.run_until_complete(
            future=HK_api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp))
        hk_query_kline_rsp_list = final_rsp['query_kline_rsp_list']
        assert self.common.searchDicKV(hk_query_kline_rsp_list[0], 'retCode') == 'SUCCESS'

        assert sz_query_kline_rsp_list[0].get("kData") == hk_query_kline_rsp_list[0].get("kData")


    @pytest.mark.parametrize(
        "exchange, code", [
            ("SEHK", "00700"),
            (ASE_exchange, ASE_code1),
            (NASDAQ_exchange, NASDAQ_code1),
            (NYSE_exchange, NYSE_code1),
            (HK_exchange, HK_main1),
            (NYMEX_exchange, NYMEX_code1),
        ]
    )
    def test_contrast_QueryTradeTickMsgReqApi(self, SZ_api, HK_api, exchange, code):
        """
        查询逐笔成交--查询5分钟的逐笔成交数据, 并订阅逐笔成交
        """
        frequence = 100
        isSubTrade = False
        exchange = exchange
        code = code
        type = QueryKLineMsgType.BY_VOL
        direct = QueryKLineDirectType.WITH_FRONT
        start_time_stamp = int(time.time() * 1000)
        start_time = start_time_stamp
        end_time = None
        vol = 100

        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(
            future=SZ_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(SZ_api.hearbeat_job(), loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        _start = time.time()
        final_rsp = loop.run_until_complete(
            future=SZ_api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        self.logger.debug("查询回包时间 : {}".format(time.time() - _start))
        sz_query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']

        assert self.common.searchDicKV(sz_query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS'

        loop.run_until_complete(
            future=HK_api.LoginReq(token=self.market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(HK_api.hearbeat_job(), loop)
        self.logger.debug(u'逐笔成交查询，并检查返回结果')
        final_rsp = loop.run_until_complete(
            future=HK_api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol,
                                                    start_time_stamp))
        hk_query_trade_tick_rsp_list = final_rsp['query_trade_tick_rsp_list']

        assert self.common.searchDicKV(hk_query_trade_tick_rsp_list[0], 'retCode') == 'SUCCESS'

        assert sz_query_trade_tick_rsp_list[0].get("tickData") == hk_query_trade_tick_rsp_list[0].get("tickData")





if __name__ == "__main__":
    pytest.main(["-v", "-s",
                 "test_contrast_PRD_SZ_AND_HK.py",
                 "-k test_contrast_StartChartDataReq",
                 # "-m=Grey",
                 # "--pdb",
                 "--show-capture=stderr",
                 "--disable-warnings",
                 ])

