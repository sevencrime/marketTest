# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/29
# @Software: PyCharm

from websocket_py3.ws_api.subscribe_api_for_first_phase import *
from datetime import datetime
from http_request.market import MarketHttpClient

http = MarketHttpClient()


def login():
    market_token = http.get_market_token(
        http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
    start_time_stamp = int(time.time() * 1000)
    asyncio.get_event_loop().run_until_complete(
        future=api.LoginReq(token=market_token, start_time_stamp=start_time_stamp))


# 按市场进行订阅
def market_sub(exchange=HK_exchange):
    sub_type = SubscribeMsgType.SUB_WITH_MARKET
    base_info = [{'exchange': exchange}]
    start_time_stamp = int(time.time() * 1000)  # 毫秒时间戳
    quote_rsp = asyncio.get_event_loop().run_until_complete(
        future=api.SubsQutoMsgReqApi(sub_type=sub_type, child_type=None, base_info=base_info,
                                          start_time_stamp=start_time_stamp))


def get_trade_status(exchange=HK_exchange):
    # 查询交易状态
    asyncio.get_event_loop().run_until_complete(
        future=api.QueryTradeStatusMsgReqApi(exchange=exchange, productList=[], recv_num=0))


def code_list_sub(exchange, code_list):
    for code in code_list:
        # 按品种订阅, 推送静态、快照、盘口、逐笔数据
        product_code = code[:3]
        base_info = [{'exchange': exchange, 'product_code': product_code}]
        asyncio.get_event_loop().run_until_complete(
            future=api.SubsQutoMsgReqApi(sub_type=SubscribeMsgType.SUB_WITH_PRODUCT, base_info=base_info,
                                         start_time_stamp=int(time.time() * 1000), recv_num=0))

        # 订阅分时
        rsp_list = asyncio.get_event_loop().run_until_complete(
            future=api.SubscribeKlineMinReqApi(exchange, code, start_time_stamp=int(time.time()), recv_num=0))
        # 订阅K线
        base_info = [{'exchange': exchange, 'code': code}]
        for period_type in KLinePeriodType.values()[1:-1]:
            rsp_list = asyncio.get_event_loop().run_until_complete(
                future=api.SubscribeKLineMsgReqApi(peroid_type=period_type, base_info=base_info, start_time_stamp=int(time.time()), recv_num=0))


def recv_forever():
    while True:
        asyncio.get_event_loop().run_until_complete(api.HearbeatReqApi(connid=int(time.time()), isKeep=True))
        print('recv_forever heart time:', time.time())
        asyncio.get_event_loop().run_until_complete(api.AppQuoteAllApi(recv_num=500))


if __name__ == '__main__':
    common = Common()
    new_loop = common.getNewLoop()
    api = SubscribeApi(realtime_ws_url, new_loop, is_record=True)
    api.sq.commit('delete from %s;' % (subscribe_table))
    new_loop.run_until_complete(future=api.client.ws_connect())
    login()
    asyncio.run_coroutine_threadsafe(api.hearbeat_job(), new_loop)
    api.logger.debug('Start subscribing：{}'.format(datetime.now()))

    test_scope_list = ['HK', 'NYMEX', 'COMEX', 'CBOT', 'CME', 'SGX']
    # test_scope_list = ['NYMEX', 'COMEX', 'CBOT', 'CME', 'SGX']
    for test_scope in test_scope_list:
        if test_scope == 'HK':
            code_list = [HK_code1, HK_code2, HK_code3, HK_code4, HK_code4, HK_code5, HK_code6]
            # market_sub(exchange=HK_exchange)
            code_list_sub(exchange=HK_exchange, code_list=code_list)
            get_trade_status(exchange=HK_exchange)
        elif test_scope == 'NYMEX':
            code_list = [NYMEX_code1, NYMEX_code2]
            market_sub(exchange=NYMEX_exchange)
            code_list_sub(exchange=NYMEX_exchange, code_list=code_list)
            get_trade_status(exchange=NYMEX_exchange)
        elif test_scope == 'COMEX':
            code_list = [COMEX_code1, COMEX_code2]
            market_sub(exchange=COMEX_exchange)
            code_list_sub(exchange=COMEX_exchange, code_list=code_list)
            get_trade_status(exchange=COMEX_exchange)
        elif test_scope == 'CBOT':
            code_list = [CBOT_code1, CBOT_code2]
            market_sub(exchange=CBOT_exchange)
            code_list_sub(exchange=CBOT_exchange, code_list=code_list)
            get_trade_status(exchange=CBOT_exchange)
        elif test_scope == 'CME':
            code_list = [CME_code1, CME_code2]
            market_sub(exchange=CME_exchange)
            code_list_sub(exchange=CME_exchange, code_list=code_list)
            get_trade_status(exchange=CME_exchange)
        elif test_scope == 'SGX':
            code_list = [SGX_code1, SGX_code2]
            market_sub(exchange=SGX_exchange)
            code_list_sub(exchange=SGX_exchange, code_list=code_list)
            get_trade_status(exchange=SGX_exchange)
    recv_forever()
