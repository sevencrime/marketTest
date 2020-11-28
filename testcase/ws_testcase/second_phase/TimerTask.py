#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import datetime
import logging
import time
import asyncio

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

from common.basic_info import exchangeTradeTime
from common.common_method import Common
from pb_files.quote_msg_def_pb2 import *
from pb_files.quote_type_def_pb2 import *
from test_config import *
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from websocket_py3.ws_api.subscribe_api_for_second_phase import SubscribeApi



class TimerTask(object):
    """docstring for TimerTask"""
    def __init__(self):
        super(TimerTask, self).__init__()
        self.logger = get_log("timerTask")
        self.max_instances = 5  # 最大并发数
        # self.scheduler = BlockingScheduler()
        self.scheduler = AsyncIOScheduler()
        self.common = Common()

    # 清盘-实时行情校验
    def Liquidation(self, exchange, code, sub_quote_type=sub_quote_type):
        """ 测试清盘 """
        self.logger.debug("执行的参数为: exchange: {}, code: {}, sub_quote_type: {}".format(exchange, code, sub_quote_type))
        exchange = exchange
        code = code
        frequence = None
        isSubKLineMin = True
        query_type = 0
        direct = 0
        start = 0
        end = 0
        vol = 0
        start_time_stamp = int(time.time() * 1000)
        isSubTrade = True
        type = "BY_VOL"
        start_time = start_time_stamp
        end_time = None
        vol = 100
        count = 50

        http = MarketHttpClient()
        market_token = http.get_market_token(
            http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
        loop = self.common.getNewLoop()
        api = SubscribeApi(union_ws_url, loop, logger=self.logger)
        loop.run_until_complete(future=api.client.ws_connect())
        loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        # asyncio.run_coroutine_threadsafe(api.hearbeat_job(), new_loop)
        self.logger.debug("订阅手机图表行情, 不会返回前快照数据和前盘口数据, {}".format(sub_quote_type))
        app_rsp_list = loop.run_until_complete(future=api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1, sub_quote_type=sub_quote_type))
        app_rsp = app_rsp_list[0]
        basic_json_list = app_rsp.get("basicData")  # 静态数据
        assert app_rsp.get("snapshot") is None
        if exchange not in ["ASE", "NYSE", "NASDAQ"]:       # 美股盘前
            assert app_rsp.get("orderbook") is None

        self.logger.debug("查询并订阅分时, 查询为空, 订阅成功, 不会返回前数据, {}".format(sub_quote_type))
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end, vol, start_time_stamp, sub_quote_type=sub_quote_type))
        if sub_quote_type == "REAL_QUOTE_MSG":
            assert self.common.searchDicKV(final_rsp["query_kline_min_rsp_list"][0], 'retCode') == 'FAILURE'
        elif sub_quote_type == "DELAY_QUOTE_MSG":
            assert self.common.searchDicKV(final_rsp["query_kline_min_rsp_list"][0], 'data') is None

        assert self.common.searchDicKV(final_rsp["sub_kline_min_rsp_list"][0], 'retCode') == 'SUCCESS'
        assert final_rsp.get("before_kline_min_list") is None

        self.logger.debug("查询五日分时")
        pass

        self.logger.debug("查询并订阅逐笔, 查询为空, 订阅成功, 不会返回前数据, {}".format(sub_quote_type))
        final_rsp = asyncio.get_event_loop().run_until_complete(
            future=api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp, sub_quote_type=sub_quote_type))

        if sub_quote_type == "REAL_QUOTE_MSG":
            assert self.common.searchDicKV(final_rsp["query_trade_tick_rsp_list"][0], 'retCode') == 'FAILURE'
        elif sub_quote_type == "DELAY_QUOTE_MSG":
            assert self.common.searchDicKV(final_rsp["query_trade_tick_rsp_list"][0], 'data') is None

        assert self.common.searchDicKV(final_rsp["sub_trade_tick_rsp_list"][0], 'retCode') == 'SUCCESS'
        assert final_rsp.get("before_tickdata_list") is None

        # 港股才有经济席位
        if exchange == "SEHK":     # 只有港股有经济席位
            self.logger.debug("订阅经济席位快照, 不会返回前数据, {}".format(sub_quote_type))
            final_rsp = asyncio.get_event_loop().run_until_complete(
                future=api.SubscribeBrokerSnapshotReqApi(exchange, code, start_time_stamp, sub_quote_type=sub_quote_type))
            assert self.common.searchDicKV(final_rsp["first_rsp_list"][0], 'retCode') == 'SUCCESS'
            assert final_rsp["before_broker_snapshot_json_list"] == []

            # 查询指数成分股
            self.logger.debug("查询港股指数成分股")
            IndexShare = asyncio.get_event_loop().run_until_complete(
                future=api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct="DESCENDING_ORDER", indexCode="0000100",
                                                        count=count, start_time_stamp=int(time.time() * 1000)))
            for indexData in self.common.searchDicKV(IndexShare, "snapshotData"):
                assert indexData.get("last") is None
                assert indexData.get("riseFall") is None

            # 按版块
            self.logger.debug("查询港股版块信息")
            for sort in ["MAIN", "LISTED_NEW_SHARES", "RED_SHIPS", "ETF", "GME"]:
                PlateSort = asyncio.get_event_loop().run_until_complete(
                    future=api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone="HK", plate_type="DESCENDING_ORDER",
                                                            sort_direct=sort, count=count, start_time_stamp=int(time.time() * 1000)))
                for quoteData in self.common.searchDicKV(PlateSort, "snapshotData"):
                    assert quoteData.get("last") is None
                    assert quoteData.get("riseFall") is None


        if exchange in [ASE_exchange, NYSE_exchange, NASDAQ_exchange]:
            self.logger.debug("查询美股中概版和明星版")
            for sort in ["START_STOCK", "CHINA_CONCEPT_STOCK"]:
                PlateSort = asyncio.get_event_loop().run_until_complete(
                    future=api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone="US", plate_type="DESCENDING_ORDER",
                                                            sort_direct=sort, count=count, start_time_stamp=int(time.time() * 1000)))
                for quoteData in self.common.searchDicKV(PlateSort, "snapshotData"):
                    assert quoteData.get("last") is None
                    assert quoteData.get("riseFall") is None

            self.logger.debug("查询美股交易所排序--按涨跌排序")
            ExchangeSort = asyncio.get_event_loop().run_until_complete(
                future=api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled="R_F_RATIO",
                                                        count=count, start_time_stamp=int(time.time() * 1000)))
            for ex_sort in self.common.searchDicKV(ExchangeSort, "snapshotData"):
                assert ex_sort.get("last") is None
                assert ex_sort.get("riseFall") is None

        api.client.disconnect()

    # 清盘-延时行情校验
    def Liquidation_DELAY(self, exchange, code):
        """ 延迟清盘 """
        self.Liquidation(exchange, code, "DELAY_QUOTE_MSG")

    # 验证交易状态改变通知
    def push_TradeStasut(self, exchange, code):
        exchange = exchange
        product_list = [code]
        frequence = None
        start_time_stamp = int(time.time() * 1000)

        http = MarketHttpClient()
        market_token = http.get_market_token(
            http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
        loop = self.common.getNewLoop()
        api = SubscribeApi(union_ws_url, loop, logger=self.logger)
        loop.run_until_complete(future=api.client.ws_connect())
        loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(api.hearbeat_job(), loop)

        self.logger.debug(u'通过查询接口，获取查询结果信息')
        first_rsp_list = asyncio.get_event_loop().run_until_complete(
            future=api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list, recv_num=3))
        cur_status = self.common.searchDicKV(first_rsp_list, "status")
        self.logger.info("cur_status : {}".format(cur_status))
        _start = time.time()
        PUSH_TRADE_STATUS = False
        push_status_count = 0
        while time.time() - _start < 120:   # 循环120秒
            rsp = asyncio.get_event_loop().run_until_complete(future=api.client.recv(recv_timeout_sec=5))
            if rsp:
                rev_data = QuoteMsgCarrier()
                rev_data.ParseFromString(rsp[0])
                self.logger.info(rev_data)
                if rev_data.type == QuoteMsgType.PUSH_TRADE_STATUS:
                    PUSH_TRADE_STATUS = True
                    push_status_count += 1
                    tradeStatus = TradeStatusData()
                    tradeStatus.ParseFromString(rev_data.data)
                    self.logger.warning(tradeStatus)
                    assert tradeStatus.status != cur_status

        assert PUSH_TRADE_STATUS == True
        assert push_status_count == 1

    # 定时任务回调
    def Listener(self, event):
        # 监听器, 输出对应的错误信息
        if event.exception:
            self.logger.error("{} 异常, 错误信息为 : \n{}".format(event.job_id, event.traceback))

    # 创建清盘定时任务
    def run_CleanData(self):
        self.logger.debug("runner 定时任务验证清盘")
        HK_stock = [
            [SEHK_exchange, SEHK_code1],
            [SEHK_exchange, SEHK_code2],
            [SEHK_exchange, SEHK_indexCode1],
            [SEHK_exchange, SEHK_indexCode2],
            [SEHK_exchange, SEHK_TrstCode1],
            [SEHK_exchange, SEHK_TrstCode2],
            [SEHK_exchange, SEHK_WarrantCode1],
            [SEHK_exchange, SEHK_WarrantCode2],
            [SEHK_exchange, SEHK_CbbcCode1],
            [SEHK_exchange, SEHK_CbbcCode2],
            [SEHK_exchange, SEHK_InnerCode1],
            [SEHK_exchange, SEHK_InnerCode2],
        ]
        US_stock = [
            [ASE_exchange, ASE_code1],
            [ASE_exchange, ASE_code2],
            [NYSE_exchange, NYSE_code1],
            [NYSE_exchange, NYSE_code2],
            [NASDAQ_exchange, NASDAQ_code1],
            [NASDAQ_exchange, NASDAQ_code4],
        ]

        # 实时订阅清盘定时任务
        [self.scheduler.add_job(self.Liquidation, 'cron', hour="08", minute="55-59", args=product, id='CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in HK_stock]
        [self.scheduler.add_job(self.Liquidation, 'cron', hour="22", minute="25-29", args=product, id='CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in US_stock]
        [self.scheduler.add_job(self.Liquidation_DELAY, 'cron', hour="08", minute="55-59", args=product, id='DELAY_CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in HK_stock]
        [self.scheduler.add_job(self.Liquidation_DELAY, 'cron', hour="22", minute="25-29", args=product, id='DELAYCleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in US_stock]

        # 从exchangeTradeTime遍历, 添加定时任务
        curDate = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
        for key, value in exchangeTradeTime.items():
            if key in ["HK_Stock", "US_Stock", "Grey"]:
                continue

            arg = key.split('_')
            arg[1] = arg[1] + "main"
            # print(arg)
            _time = datetime.datetime.strptime(curDate + value[0], '%Y-%m-%d%H:%M')     # 开盘时间
            if arg[0] not in ["HKFE", "SGX", "SEHK", "Grey"] and not isSummerTime:
                # 冬令时加一个小时
                _time = datetime.datetime.strptime(curDate + value[0], '%Y-%m-%d%H:%M') + datetime.timedelta(hours=1)

            start_date = _time  # copy一个变量
            delay_endTime = _time
            start_date = start_date - datetime.timedelta(minutes=10)
            delay_endTime = delay_endTime + datetime.timedelta(minutes=14)  #

            job_id = "CleanData_{}>>>start_date:{}, end_date:{}".format(arg, start_date, _time)
            # print(job_id)
            self.scheduler.add_job(self.Liquidation, 'interval', minutes=1, start_date=start_date, end_date=_time, args=arg, id=job_id)

            # 延时行情
            delay_job_id = "DELAY_CleanData_{}>>>start_date:{}, end_date:{}".format(arg, start_date, delay_endTime)
            # print(delay_job_id)
            self.scheduler.add_job(self.Liquidation_DELAY, 'interval', minutes=1, start_date=start_date, end_date=delay_endTime, args=arg, id=delay_job_id)

    # 创建交易状态推送定时任务
    def run_TradeStatus(self):
        pass
        self.logger.debug("交易交易状态推送通知")
        # 从exchangeTradeTime遍历, 添加定时任务
        curDate = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
        for key, value in exchangeTradeTime.items():
            if key in ["HK_Stock", "US_Stock", "Grey"]:
                continue

            arg = key.split('_')    
            for val in value:
                _time = datetime.datetime.strptime(curDate + val, '%Y-%m-%d%H:%M')
                if arg[0] not in ["HKFE", "SGX", "SEHK", "Grey"] and not isSummerTime:
                    # 冬令时加一个小时
                    _time = datetime.datetime.strptime(curDate + val, '%Y-%m-%d%H:%M') + datetime.timedelta(hours=1)
                _time = _time - datetime.timedelta(seconds=30)
                s_time = datetime.datetime.strftime(_time, "%H%M")
                job_id = "push_status_{}>>>BeginTime:{}".format('-'.join(arg), s_time)
                # print(job_id)
                self.scheduler.add_job(self.push_TradeStasut, 'cron', hour=s_time[:-2], minute=s_time[-2:], second="30", args=arg, max_instances=self.max_instances, id=job_id)

        # 港股
        self.scheduler.add_job(self.push_TradeStasut, 'cron', hour="09", minute="29", second="30", args=["SEHK", "00700"], max_instances=self.max_instances, id="SEHK_pushStatus_open")
        self.scheduler.add_job(self.push_TradeStasut, 'cron', hour="11-12,15", minute="59", second="30", args=["SEHK", "00700"], max_instances=self.max_instances, id="SEHK_pushStatus")

        # 美股
        self.scheduler.add_job(self.push_TradeStasut, 'cron', hour="22", minute="29", second="30", args=[NASDAQ_exchange, NASDAQ_code1], max_instances=self.max_instances, id="NASDAQ_pushStatus_open")
        self.scheduler.add_job(self.push_TradeStasut, 'cron', hour="04", minute="59", second="30", args=[NASDAQ_exchange, NASDAQ_code1], max_instances=self.max_instances, id="NASDAQ_pushStatus")

    # 定时任务运行入口
    def run_Scheduler(self):
        self.run_CleanData()
        self.run_TradeStatus()
        self.scheduler.add_listener(self.Listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass



if __name__ == '__main__':
    pass
    timer = TimerTask()
    # timer.run_CleanData()
    # timer.run_TradeStatus()
    timer.run_Scheduler()
    # timer.push_TradeStasut("CBOT", "ZS")
