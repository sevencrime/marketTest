#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import time
import asyncio
import concurrent.futures

from common.GlobalMap import GlobalMap
from common.common_method import *
from common.get_basic.get_InstrCode import get_all_instrCode
from http_request.market import MarketHttpClient
from test_config import *
from websocket_py3.ws_api.subscribe_api_for_second_phase import SubscribeApi

logger = get_log()
common = Common()
gm = GlobalMap()

http = MarketHttpClient()
market_token = http.get_market_token(
    http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))

async def CleanData(param, sem):
    exchange = param[0]
    code = param[1]
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

    async with sem:
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)

        api = SubscribeApi(union_ws_url, loop, logger=logger)
        await api.client.ws_connect()
        await api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence)
        app_rsp_list = await api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1)
        app_rsp = app_rsp_list[0]
        assert common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS'
        basic = app_rsp['basicData']  # 静态数据
        snapshot = app_rsp['snapshot']  # 快照数据
        orderbook = app_rsp.get("orderbook")  # 盘口

        searchDicKV = lambda dic, keys: int(common.searchDicKV(dic, keys) or 0)

        try:
            logger.warning(searchDicKV(basic, "preClose"))
            logger.warning(searchDicKV(snapshot, "preclose"))
            # assert searchDicKV(basic, "preClose") == searchDicKV(snapshot, "preclose")      # 股票 -- 校验静态数据的昨收价等于快照数据的昨收价
            assert searchDicKV(basic, "preClose") == searchDicKV(snapshot, "settlementPrice")      # 期货
        except Exception as e:
            logger.error("昨收价不一致, exchange: {}, code: {}, basic --> {}, snapshot --> {}".format(
                exchange, code, searchDicKV(basic, "preClose"), searchDicKV(snapshot, "settlementPrice")))


def split_list_n_list(origin_list, n):
    if len(origin_list) % n == 0:
        cnt = len(origin_list) // n
    else:
        cnt = len(origin_list) // n + 1

    for i in range(0, n):
        yield origin_list[i * cnt:(i + 1) * cnt]


def main(codelist1):
    loop = asyncio.get_event_loop()
    sem = asyncio.Semaphore(200)
    tasks = [asyncio.ensure_future(CleanData(param, sem)) for param in codelist1]
    result = loop.run_until_complete(asyncio.wait(tasks))
    for task in tasks:
        print("task结果 : {}".format(task.result()))


if __name__ == "__main__":

    # av_list = split_list_n_list(testcode, 4)
    av_list = split_list_n_list(get_all_instrCode(), 4)

    start = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as exc:
        for i in av_list:
            print(len(i))
            exc.submit(main, i)
    
    print(time.time() - start)
    
