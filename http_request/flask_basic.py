#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import time
import asyncio

from flask import Flask, request
from http_request.market import MarketHttpClient
from common.common_method import *
from websocket_py3.ws_api.subscribe_api_for_second_phase import SubscribeApi

logger = get_log()
app = Flask(__name__)


# http://192.168.80.110:7777/onedi?exchange=NASDAQ&code=JD
@app.route('/onedi/quote', methods=['post','get'])    # 查询前静态, 前快照, 前盘口
def StartChartData():           
    exchange = request.args.get('exchange')
    code = request.args.get('code')

    frequence = None
    start_time_stamp = int(time.time() * 1000)
    http = MarketHttpClient()
    market_token = http.get_market_token(
        http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
    loop = Common().getNewLoop()
    api = SubscribeApi(union_ws_url, loop)
    loop.run_until_complete(future=api.client.ws_connect())
    loop.run_until_complete(future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp, frequence=frequence))
    # asyncio.run_coroutine_threadsafe(api.hearbeat_job(), new_loop)
    app_rsp_list = loop.run_until_complete(future=api.StartChartDataReqApi(exchange, code, start_time_stamp, recv_num=1))
    app_rsp = app_rsp_list[0]
    api.client.disconnect()

    return app_rsp


# 查询排序

if __name__ == '__main__':
    # StartChartData()
    app.run(
        host = '0.0.0.0',
        port = 7777,
        debug = True
    )