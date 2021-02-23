#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import datetime
import logging
import time
import asyncio
from builtins import KeyboardInterrupt, SystemExit, object, super

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
from zmq_py3.router_dealer.dealer import start

# import nest_asyncio
# nest_asyncio.apply()


class TimerTask(object):
    """docstring for TimerTask"""
    def __init__(self):
        super(TimerTask, self).__init__()
        self.logger = get_log("timerTask")
        self.max_instances = 20  # 最大并发数
        # self.scheduler = BlockingScheduler()
        self.scheduler = AsyncIOScheduler()
        self.common = Common()

    # 清盘-实时行情校验
    async def CleanData(self, exchange, code, loop, sub_quote_type=sub_quote_type):
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

        # http = MarketHttpClient()
        # market_token = http.get_market_token(
        #     http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

        market_token = None
        asyncio.set_event_loop(loop)

        try:
            api = SubscribeApi(union_ws_url, loop, logger=self.logger)
            await api.client.ws_connect()
            await api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence)
            asyncio.run_coroutine_threadsafe(api.hearbeat_job(), loop)
            self.logger.debug("订阅手机图表行情, 不会返回前快照数据和前盘口数据, {}, {}".format(sub_quote_type, code))
            app_rsp_list = await api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1, sub_quote_type=sub_quote_type)
            app_rsp = app_rsp_list[0]
            basic_json_list = app_rsp.get("basicData")  # 静态数据
            assert self.common.searchDicKV(app_rsp.get("snapshot"), "high") is None
            assert self.common.searchDicKV(app_rsp.get("snapshot"), "open") is None
            assert self.common.searchDicKV(app_rsp.get("snapshot"), "low") is None
            assert self.common.searchDicKV(app_rsp.get("snapshot"), "close") is None
            assert self.common.searchDicKV(app_rsp.get("snapshot"), "last") is None
            if exchange not in ["ASE", "NYSE", "NASDAQ"]:       # 美股盘前
                assert app_rsp.get("orderbook") is None

            self.logger.debug("查询并订阅分时, 查询为空, 订阅成功, 不会返回前数据, {}, {}".format(sub_quote_type, code))
            final_rsp = await api.QueryKLineMinMsgReqApi(isSubKLineMin, exchange, code, query_type, direct, start, end, vol, start_time_stamp, sub_quote_type=sub_quote_type)
            if sub_quote_type == "REAL_QUOTE_MSG":
                assert self.common.searchDicKV(final_rsp["query_kline_min_rsp_list"][0], 'retCode') == 'INITQUOTE_TIME'
            elif sub_quote_type == "DELAY_QUOTE_MSG":
                assert self.common.searchDicKV(final_rsp["query_kline_min_rsp_list"][0], 'data') is None

            assert self.common.searchDicKV(final_rsp["sub_kline_min_rsp_list"][0], 'retCode') == 'SUCCESS'
            assert final_rsp.get("before_kline_min_list") is None

            self.logger.debug("查询五日分时")
            fiveday_rsp = await api.QueryFiveDaysKLineMinReqApi(isSubKLineMin, exchange, code, start, start_time_stamp)

            query_5day_klinemin_rsp_list = fiveday_rsp['query_5day_klinemin_rsp_list']
            sub_kline_min_rsp_list = fiveday_rsp['sub_kline_min_rsp_list']
            assert self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'retCode') == 'SUCCESS'
            assert self.common.searchDicKV(sub_kline_min_rsp_list[0], 'retCode') == 'SUCCESS'
            # 
            self.logger.debug(u'校验五日分时清盘时的数据, {}, {}'.format(sub_quote_type, code))
            day_data_list = self.common.searchDicKV(query_5day_klinemin_rsp_list[0], 'dayData')
            assert day_data_list.__len__() == 5
            # 获取五个交易日
            fiveDateList = self.common.get_fiveDays(exchange)
            self.logger.debug("合约 {} , 五个交易日时间 : {}".format(code, fiveDateList))
            for i in range(len(day_data_list)):
                # 校验五日date依次递增, 遇到节假日无法校验
                assert day_data_list[i].get("date") == fiveDateList[i]
                info_list = self.common.searchDicKV(day_data_list[i], 'data')
                if info_list.__len__() > 0:
                    if exchange == "HKFE":
                        assert day_data_list[i].get("date") == info_list[-1].get("updateDateTime")[:8]
                    else:
                        assert day_data_list[i].get("date") == info_list[0].get("updateDateTime")[:8]


            self.logger.debug("查询并订阅逐笔, 查询为空, 订阅成功, 不会返回前数据, {}, {}".format(sub_quote_type, code))
            final_rsp = await api.QueryTradeTickMsgReqApi(isSubTrade, exchange, code, type, direct, start_time, end_time, vol, start_time_stamp, sub_quote_type=sub_quote_type)

            try:
                assert final_rsp["query_trade_tick_rsp_list"] == []
            except AssertionError:
                assert self.common.searchDicKV(final_rsp["query_trade_tick_rsp_list"], "data") is None

            assert self.common.searchDicKV(final_rsp["sub_trade_tick_rsp_list"][0], 'retCode') == 'SUCCESS'
            assert final_rsp.get("before_tickdata_list") is None

            # 港股才有经济席位
            if exchange == "SEHK":     # 只有港股有经济席位
                self.logger.debug("订阅经济席位快照, 不会返回前数据, {}, {}".format(sub_quote_type, code))
                final_rsp = await api.SubscribeBrokerSnapshotReqApi(exchange, code, start_time_stamp, sub_quote_type=sub_quote_type)
                assert self.common.searchDicKV(final_rsp["first_rsp_list"][0], 'retCode') == 'SUCCESS'
                assert final_rsp["before_broker_snapshot_json_list"] == []

                # 查询指数成分股
                self.logger.debug("查询港股指数成分股, {}, {}".format(sub_quote_type, code))
                IndexShare = await api.QueryIndexShareMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sort_direct="DESCENDING_ORDER", indexCode="0000100",
                                                            count=count, start_time_stamp=int(time.time() * 1000))
                for indexData in self.common.searchDicKV(IndexShare, "snapshotData"):
                    assert indexData.get("last") is None
                    assert indexData.get("riseFall") is None

                # 按版块
                self.logger.debug("查询港股版块信息, {}, {}".format(sub_quote_type, code))
                for plate_type in ["MAIN", "LISTED_NEW_SHARES", "RED_SHIPS", "ETF", "GME"]:
                    PlateSort = await api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone="HK", plate_type=plate_type,
                                                                sort_direct="DESCENDING_ORDER", count=count, start_time_stamp=int(time.time() * 1000))
                    if self.common.searchDicKV(PlateSort, "snapshotData"):
                        for quoteData in self.common.searchDicKV(PlateSort, "snapshotData"):
                            assert quoteData.get("last") is None
                            assert quoteData.get("riseFall") is None


            if exchange in [ASE_exchange, NYSE_exchange, NASDAQ_exchange]:
                self.logger.debug("查询美股中概版和明星版, {}, {}".format(sub_quote_type, code))
                for plate_type in ["START_STOCK", "CHINA_CONCEPT_STOCK"]:
                    PlateSort = await api.QueryPlateSortMsgReqApi(isSubTrade=isSubTrade, zone="US", plate_type=plate_type,
                                                                sort_direct="DESCENDING_ORDER", count=count, start_time_stamp=int(time.time() * 1000))
                    if self.common.searchDicKV(PlateSort, "snapshotData"):
                        for quoteData in self.common.searchDicKV(PlateSort, "snapshotData"):
                            assert quoteData.get("last") is None
                            assert quoteData.get("riseFall") is None

                self.logger.debug("查询美股交易所排序--按涨跌排序, {}, {}".format(sub_quote_type, code))
                ExchangeSort = await api.QueryExchangeSortMsgReqApi(isSubTrade=isSubTrade, exchange=exchange, sortFiled="R_F_RATIO",
                                                            count=count, start_time_stamp=int(time.time() * 1000))
                for ex_sort in self.common.searchDicKV(ExchangeSort, "snapshotData"):
                    assert ex_sort.get("last") is None
                    assert ex_sort.get("riseFall") is None
        finally:
            api.client.disconnect()


    # 验证状态改变后的推送通知
    async def push_TradeStasut(self, exchange, code, loop):
        exchange = exchange
        product_list = [code]
        frequence = None
        start_time_stamp = int(time.time() * 1000)

        market_token = None
        asyncio.set_event_loop(loop)

        try:
            api = SubscribeApi(union_ws_url, loop, logger=self.logger)
            await api.client.ws_connect()
            await api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence)
            asyncio.run_coroutine_threadsafe(api.hearbeat_job(), loop)

            self.logger.debug(u'查询代码:{} 的交易状态, curtime : {}'.format(code, str(datetime.datetime.now())))
            first_rsp_list = await api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=product_list, recv_num=2)
            cur_status = self.common.searchDicKV(first_rsp_list, "status")
            self.logger.info("cur_status : {}".format(cur_status))
            _start = time.time()
            PUSH_TRADE_STATUS = False
            while time.time() - _start < 120:   # 循环120秒
                rsp = await api.client.recv(recv_timeout_sec=5)
                if rsp:
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(rsp[0])
                    # self.logger.debug(rev_data)
                    if rev_data.type == QuoteMsgType.PUSH_TRADE_STATUS:
                        PUSH_TRADE_STATUS = True
                        tradeStatus = TradeStatusData()
                        tradeStatus.ParseFromString(rev_data.data)
                        self.logger.info(tradeStatus)
                        assert tradeStatus.status != cur_status     # 确认校验状态只变化的一次

            assert PUSH_TRADE_STATUS
            self.logger.debug("代码 : {} 有推送交易状态".format(code))

        finally:
            api.client.disconnect()


    async def Liquidation(self, exchange, code):
        # loop = asyncio.new_event_loop()
        # loop.run_until_complete(future=self.CleanData(exchange, code, loop, "REAL_QUOTE_MSG"))
        loop = asyncio.get_event_loop()
        await self.CleanData(exchange, code, loop, "REAL_QUOTE_MSG")

    # 清盘-延时行情校验
    async def Liquidation_DELAY(self, exchange, code):
        """ 延迟清盘 """
        # loop = asyncio.new_event_loop()
        # loop.run_until_complete(future=self.CleanData(exchange, code, loop, "DELAY_QUOTE_MSG"))
        loop = asyncio.get_event_loop()
        await self.CleanData(exchange, code, loop, "DELAY_QUOTE_MSG")


    async def check_TradeStatus(self, exchange, code):
        loop = asyncio.get_event_loop()
        await self.push_TradeStasut(exchange, code, loop)


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
            [SEHK_exchange, SEHK_indexCode1],
            [SEHK_exchange, SEHK_TrstCode1],
            [SEHK_exchange, SEHK_WarrantCode1],
            [SEHK_exchange, SEHK_CbbcCode1],
            [SEHK_exchange, SEHK_InnerCode1],
        ]
        US_stock = [
            [ASE_exchange, ASE_code1],
            [NYSE_exchange, NYSE_code1],
            [NASDAQ_exchange, NASDAQ_code1],
            [BATS_exchange, BATS_code1],
        ]

        # 实时订阅清盘定时任务
        [self.scheduler.add_job(self.Liquidation, 'cron', day_of_week='mon-fri', hour="08", minute="55-59", args=product, id='CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in HK_stock]
        [self.scheduler.add_job(self.Liquidation, 'cron', day_of_week='mon-fri', hour="22", minute="25-29", args=product, id='CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in US_stock]
        [self.scheduler.add_job(self.Liquidation_DELAY, 'cron', day_of_week='mon-fri', hour="08", minute="55-59", args=product, id='DELAY_CleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in HK_stock]
        [self.scheduler.add_job(self.Liquidation_DELAY, 'cron', day_of_week='mon-fri', hour="22", minute="25-29", args=product, id='DELAYCleanData>>{}'.format('-'.join(product)), max_instances=self.max_instances) for product in US_stock]

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
            delay_endTime = delay_endTime + datetime.timedelta(minutes=15)  #
            s_time = datetime.datetime.strftime(start_date, "%H%M")

            job_id = "CleanData_{}>>>start_date:{}, end_date:{}".format(arg, start_date, _time)
            # print(job_id)
            # self.scheduler.add_job(self.Liquidation, 'interval', minutes=1, start_date=start_date, end_date=_time, args=arg, id=job_id)
            self.scheduler.add_job(self.Liquidation, 'cron', day_of_week='mon-fri', hour=s_time[:-2],
                                   minute=s_time[-2:], args=arg, max_instances=self.max_instances, id=job_id)

            # 延时行情
            delay_job_id = "DELAY_CleanData_{}>>>start_date:{}, end_date:{}".format(arg, start_date, delay_endTime)
            # print(delay_job_id)
            # self.scheduler.add_job(self.Liquidation_DELAY, 'interval', minutes=1, start_date=start_date, end_date=delay_endTime, args=arg, id=delay_job_id)
            self.scheduler.add_job(self.Liquidation_DELAY, 'cron', day_of_week='mon-fri', hour=s_time[:-2], minute=s_time[-2:], args=arg, max_instances=self.max_instances, id=delay_job_id)


    # 创建交易状态推送定时任务
    def run_TradeStatus(self):
        self.logger.debug("交易交易状态推送通知")
        # 从exchangeTradeTime遍历, 添加定时任务
        curDate = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
        for key, value in exchangeTradeTime.items():
            if key in ["HK_Stock", "US_Stock", "Grey"]:
                continue

            arg = key.split('_')
            # 每个时间段, 交易状态都会发生变化
            for val in value:
                _time = datetime.datetime.strptime(curDate + val, '%Y-%m-%d%H:%M')
                if arg[0] not in ["HKFE", "SGX", "SEHK", "Grey"] and not isSummerTime:
                    # 冬令时加一个小时
                    _time = datetime.datetime.strptime(curDate + val, '%Y-%m-%d%H:%M') + datetime.timedelta(hours=1)
                
                _time = _time - datetime.timedelta(seconds=30)
                s_time = datetime.datetime.strftime(_time, "%H%M")
                job_id = "push_status_{}>>>BeginTime:{}".format('-'.join(arg), s_time)
                # print(job_id)
                self.scheduler.add_job(self.check_TradeStatus, 'cron', hour=s_time[:-2], minute=s_time[-2:], second="00", args=arg, max_instances=self.max_instances, id=job_id)

        # 港股
        self.scheduler.add_job(self.check_TradeStatus, 'cron', day_of_week='mon-fri', hour="09", minute="29",
                               second="00", args=["SEHK", "00700"], max_instances=self.max_instances, id="SEHK_pushStatus_open")

        self.scheduler.add_job(self.check_TradeStatus, 'cron', day_of_week='mon-fri', hour="11-12,15", minute="59",
                               second="00", args=["SEHK", "00700"], max_instances=self.max_instances, id="SEHK_pushStatus")

        # 美股
        self.scheduler.add_job(self.check_TradeStatus, 'cron', day_of_week='mon-fri', hour="22", minute="29", second="00",
                               args=[NASDAQ_exchange, NASDAQ_code1], max_instances=self.max_instances, id="NASDAQ_pushStatus_open")

        self.scheduler.add_job(self.check_TradeStatus, 'cron', day_of_week='mon-fri', hour="04", minute="59", second="00",
                               args=[NASDAQ_exchange, NASDAQ_code1], max_instances=self.max_instances, id="NASDAQ_pushStatus")

        self.scheduler.add_job(self.check_TradeStatus, 'cron', day_of_week='sat', hour="04", minute="59", second="00", args=[
            NASDAQ_exchange, NASDAQ_code1], max_instances=self.max_instances, id="NASDAQ_pushStatus_sat")

    # 定时任务运行入口
    def run_Scheduler(self):
        self.run_CleanData()
        self.run_TradeStatus()

        # 更新合约
        self.scheduler.add_job(start, 'cron', hour="08", minute="10", args=['SYNC_INSTR_REQ', codegenerate_dealer_address], id="dealer_instr")

        self.scheduler.add_listener(self.Listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.scheduler.start()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass



if __name__ == '__main__':
    pass
    timer = TimerTask()
    timer.run_Scheduler()
    # timer.Liquidation("SEHK", "00700")

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(future=timer.push_TradeStasut("SEHK", "00700", loop))
