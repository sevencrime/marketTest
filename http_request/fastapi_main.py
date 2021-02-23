#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json
import time
import asyncio

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from typing import List, Optional
from fastapi import FastAPI, Query

from common.common_method import Common
from common.get_basic.get_InstrCode import get_instr_API
from common.test_log.ed_log import get_log
from http_request.market import MarketHttpClient
from pb_files.quote_type_def_pb2 import *
from test_config import *
from websocket_py3.ws_api.subscribe_api_for_second_phase import SubscribeApi

app = FastAPI()
logger = get_log()
common = Common()

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get('/onedi/quote', response_class=HTMLResponse)    # 查询前静态, 前快照, 前盘口
def StartChartData(exchange:str, code:str):
    # exchange = exchange
    # code = code

    frequence = None
    start_time_stamp = int(time.time() * 1000)
    # http = MarketHttpClient()
    # market_token = http.get_market_token(
    #     http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
    market_token = None
    loop = Common().getNewLoop()
    api = SubscribeApi(union_ws_url, loop)
    loop.run_until_complete(future=api.client.ws_connect())
    loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
    asyncio.run_coroutine_threadsafe(api.hearbeat_job(), loop)
    app_rsp_list = loop.run_until_complete(future=api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))
    app_rsp = app_rsp_list[0]
    api.client.disconnect()

    # return app_rsp

    return """
    <html>
    <head>
    <title>查询合约</title>
    </head>
    <body>
    <pre id="out_pre"></pre>
    </body>
    <script type="text/javascript">
       var result = JSON.stringify({text}, null, 2);//将字符串转换成json对象
       document.getElementById('out_pre').innerText= result ;
    </script>
    </html>
    """.format(text=app_rsp)


@app.get('/onedi/QueryExchangeSort')    # 查询交易所排序, 暂时没人用, 有需要再改
def QueryExchangeSort(exchange:str, count:int, sortFiled:str):
    frequence = None
    start_time_stamp = int(time.time() * 1000)
    # http = MarketHttpClient()
    # market_token = http.get_market_token(
    #     http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
    market_token = None
    loop = Common().getNewLoop()
    api = SubscribeApi(union_ws_url, loop)
    loop.run_until_complete(future=api.client.ws_connect())
    loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
    # asyncio.run_coroutine_threadsafe(api.hearbeat_job(), new_loop)
    rsp_sort_list = asyncio.get_event_loop().run_until_complete(
        future=api.QueryExchangeSortMsgReqApi(isSubTrade=None, exchange=exchange, sortFiled=sortFiled,
                                                count=count, start_time_stamp=start_time_stamp, recv_num=1))
    app_sort = rsp_sort_list[0]
    api.client.disconnect()
    return app_sort


@app.get('/onedi/instr', response_class=HTMLResponse)    # 查询单个代码的合约信息
def get_instr_info(code:str):
    # exchange = exchange
    # code = code

    # return get_instr_API(code)
    instr_update_stamp, instr = asyncio.run(get_instr_API(code))
    print(instr_update_stamp)
    print(instr)

    return """
    <html>
    <head>
    <title>查询合约</title>
    </head>
    <body>
    <p>码表更新时间 : {update_stamp}</p>
    <pre id="out_pre"></pre>
    </body>
    <script type="text/javascript">
       var result = JSON.stringify({text}, null, 2);//将字符串转换成json对象
       document.getElementById('out_pre').innerText= result ;
    </script>
    </html>
    """.format(update_stamp=instr_update_stamp, text=instr)


@app.get('/onedi/Earnings', response_class=HTMLResponse)    # 查询当日收益, 需求不明确, 待定
def get_Earnings(code:str, price:float, exchange:str="SEHK"):
    code = code
    exchange = exchange
    if exchange == "SEHK":
        q_price = price * pow(10, 3)

    frequence = None
    isSubKLine = False
    peroid_type = KLinePeriodType.DAY
    query_type = QueryKLineMsgType.BY_VOL
    direct = QueryKLineDirectType.WITH_FRONT
    start_time_stamp = int(time.time() * 1000)
    start = start_time_stamp
    end = None
    vol = 10
    market_token = None

    try:
        loop = common.getNewLoop()
        api = SubscribeApi(union_ws_url, loop)
        loop.run_until_complete(future=api.client.ws_connect())
        loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
        asyncio.run_coroutine_threadsafe(api.hearbeat_job(), loop)

        # 查询十日K线
        kline_list = loop.run_until_complete(
            future=api.QueryKLineMsgReqApi(isSubKLine, exchange, code, peroid_type, query_type, direct, start,
                                                end, vol, start_time_stamp, recv_num=1))
        query_kline = kline_list['query_kline_rsp_list'][0]
        assert common.searchDicKV(query_kline, 'retCode') == 'SUCCESS'
        high_list = []
        for _kData in query_kline.get("kData"):
            k_high = int(common.searchDicKV(_kData, "high") or 0)
            high_list.append(k_high)

        # 分割五日和十日
        if high_list.__len__() > 5:
            five_high_price = max(high_list[-5:])
            ten_high_price = max(high_list)

            five_earnings =  (five_high_price - q_price) / q_price * 100 
            ten_earnings = (ten_high_price - q_price) / q_price * 100 
        else:       # 少于五日时, 按五日判断
            high_price = max(high_list)
            five_earnings =  (high_price - q_price) / q_price * 100 
            ten_earnings =  (high_price - q_price) / q_price * 100 


        # 查询快照
        app_rsp_list = loop.run_until_complete(future=api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))
        app_rsp = app_rsp_list[0]
        assert common.searchDicKV(app_rsp, 'retCode') == 'SUCCESS'
        snapshot = app_rsp.get("snapshot")
        cur_highPrice = int(common.searchDicKV(snapshot, "high") or 0)
        cur_earnings = (cur_highPrice - q_price) / q_price * 100  


        print("当日收益 : {}".format(cur_earnings))
        print("五日收益 : {}".format(five_earnings))
        print("十日收益 : {}".format(ten_earnings))

        return """
        <html>
        <head>
        <title>查询收益率</title>
        </head>
        <body>
        <p>查询股票代码 : {code} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;入选价 : {price}</p>
        <p> 当日收益: &nbsp;&nbsp;{cur_earnings} </p>
        <p> 五日收益: &nbsp;&nbsp;{five_earnings} </p>
        <p> 十日收益: &nbsp;&nbsp;{ten_earnings} </p>
        </body>
        </html>
        """.format(cur_earnings=cur_earnings, five_earnings=five_earnings, ten_earnings=ten_earnings, code=code, price=price)

    except Exception as e:
        raise e

    finally:
        api.client.disconnect()


############################ test api ###################

@app.get("/items/")
async def read_items(q: Optional[List[str]] = Query(None, title="Query string"), k: Optional[List[str]] = Query(None, description="备注信息", alias="item-query")):
    query_items = {"q": q, "k": k}
    return query_items




if __name__ == "__main__":
    import os
    # os.system("uvicorn fastapi_main:app --reload")
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=8001, reload=True)

# 虚拟机地址: http://192.168.121.130:8001/onedi/quote?exchange=SEHK&code=00700
# 本地地址: http://192.168.80.110:8001/onedi/quote?exchange=SEHK&code=0000100
# 远程 ： http://192.168.80.19:8001/onedi/quote?exchange=SEHK&code=0000100
#         http://192.168.80.19:8001/onedi/instr?exchange=SEHK&code=0000100
# 查询收益 : http://192.168.80.19:8001/onedi/Earnings?code=00700&price=733000
