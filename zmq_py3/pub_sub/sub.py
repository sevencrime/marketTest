# -*- coding: utf-8 -*-
#!/usr/bin/python

import time
import asyncio
import json

import zmq
import zmq.asyncio
from google.protobuf import json_format

from common.common_method import Common
from py_sqlite.market import MarketSqliteDBClient
from test_config import *
from pb_files.quote_msg_def_pb2 import *
from pb_files.quote_type_def_pb2 import *

sq = MarketSqliteDBClient()
common = Common()

run_flag = True
rec_data = []
max_dalayTime = 1000 * 60 * 60   # 延时时间, 毫秒(手动修改)



def check_delayTime(rspTime, recv_data):
    dict_data = json.loads(recv_data)
    sourceUpdateTime = common.searchDicKV(dict_data, "sourceUpdateTime")

    try:
        sourceTime = int(int(sourceUpdateTime) / pow(10, 6))
    except Exception as e:
        print(dict_data)
        raise e
    try:
        # 校验误差
        print("延迟时间 : {} 秒".format(abs(sourceTime - rspTime) / 1000))
        # 校验延时时间不超过 max_dalayTime (行情实时数据, 理论上不能延时)
        assert abs(sourceTime - rspTime) <= max_dalayTime     ## BUG: 股票采集数据延迟太久
    except AssertionError:
        print("本地时间 : {}, 格式化时间 : {}".format(rspTime, common.formatStamp(rspTime)))
        print("源时间: {}, 格式化时间 : {}".format(sourceTime, common.formatStamp(sourceTime)))
        # print("时间差值 : {}".format(abs(sourceTime - rspTime)))
        raise AssertionError


async def start_sub(sub_address):    # 创建一个异步函数，即“协程”
    print('sub_address:', sub_address)
    context = zmq.asyncio.Context(io_threads=3)
    sub_socket = context.socket(socket_type=zmq.SUB)
    sub_socket.connect(sub_address)
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'')

    poller = zmq.asyncio.Poller()
    poller.register(sub_socket)

    while run_flag:
        for event in await poller.poll():
            if event[1] & zmq.POLLIN:
                data = event[0].recv().result()
                rspTime = int(time.time() * 1000)
                rec_data = QuoteMsgCarrier()
                rec_data.ParseFromString(data)

                # if rec_data.type == QuoteMsgType.PUSH_ORDER_BOOK:
                #     order_book = QuoteOrderBookData()
                #     order_book.ParseFromString(rec_data.data)
                #     json_order_book = json_format.MessageToJson(order_book)
                #     print("盘口数据: 接收成功")

                #     # 测试源数据延迟
                #     check_delayTime(rspTime, json_order_book)

                #     sq.pub_new_record(rec_data.type, order_book, json_order_book)

                # elif rec_data.type == QuoteMsgType.PUSH_TRADE_DATA:
                #     trade_data = QuoteTradeData()
                #     trade_data.ParseFromString(rec_data.data)
                #     json_trade_data = json_format.MessageToJson(trade_data)
                #     print("逐笔成交: 接收成功")

                #     # 测试源数据延迟
                #     check_delayTime(rspTime, json_trade_data)

                #     sq.pub_new_record(rec_data.type, trade_data, json_trade_data)

                # elif rec_data.type == QuoteMsgType.PUSH_BASIC:
                #     basic_info = QuoteBasicInfo()
                #     basic_info.ParseFromString(rec_data.data)
                #     json_basic_info = json_format.MessageToJson(basic_info)
                #     print("静态数据: 接收成功")

                #     # 测试源数据延迟
                #     check_delayTime(rspTime, json_basic_info)

                #     sq.pub_new_record(rec_data.type, basic_info, json_basic_info)

                # elif rec_data.type == QuoteMsgType.PUSH_SNAPSHOT:
                #     snap_shot = QuoteSnapshot()
                #     snap_shot.ParseFromString(rec_data.data)
                #     json_snap_shot = json_format.MessageToJson(snap_shot)
                #     print("快照数据: 接收成功")

                #     # 测试源数据延迟
                #     check_delayTime(rspTime, json_snap_shot)  

                #     sq.pub_new_record(rec_data.type, snap_shot, json_snap_shot)

                # elif rec_data.type == QuoteMsgType.PUSH_BROKER_SNAPSHOT:
                if rec_data.type == QuoteMsgType.PUSH_BROKER_SNAPSHOT:
                    trade_data = PushBrokerSnapshot()
                    trade_data.ParseFromString(rec_data.data)
                    json_trade_data = json_format.MessageToJson(trade_data)
                    print("经纪席位快照: 接收成功")
                    sq.pub_new_record(rec_data.type, trade_data, json_trade_data)

#                 elif rec_data.type == QuoteMsgType.PUSH_NEW_SHARES_SNAPSHOT:
#                     trade_data = NewsharesQuoteSnapshot()
#                     trade_data.ParseFromString(rec_data.data)
#                     json_trade_data = json_format.MessageToJson(trade_data)
#                     print("已上市新股行情快照:\n{0}".format(trade_data))
#                     sq.pub_new_record(rec_data.type, trade_data, json_trade_data)
                
#                 elif rec_data.type == QuoteMsgType.PUSH_GREY_MARKET_SNAPSHOT:
#                     trade_data = GreyMarketQuoteSnapshot()
#                     trade_data.ParseFromString(rec_data.data)
#                     json_trade_data = json_format.MessageToJson(trade_data)
#                     print("暗盘行情快照:\n{0}".format(trade_data))
#                     sq.pub_new_record(rec_data.type, trade_data, json_trade_data)

# # ------------------------------------------ 采集器end-----------------------------------------------------------

# # ------------------------------------------ 计算服务start-------------------------------------------------------
#                 # 推送分时K线
#                 elif rec_data.type == QuoteMsgType.PUSH_KLINE_MIN:
#                     kline_min_data = PushKLineMinData()
#                     kline_min_data.ParseFromString(rec_data.data)
#                     json_kline_min_data = json_format.MessageToJson(kline_min_data)
#                     print("推送分时数据: 接收成功")

#                     sq.pub_new_record(rec_data.type, kline_min_data, json_kline_min_data)

#                 # 推送
#                 elif rec_data.type == QuoteMsgType.PUSH_KLINE:
#                     kline_data = PushKLineData()
#                     kline_data.ParseFromString(rec_data.data)
#                     json_min_data = json_format.MessageToJson(kline_data)
#                     print("推送K线数据: 接收成功")

#                     # file_path= txt_file_save_folder + "kline_data.txt"
#                     # with open(file_path, 'a') as f:
#                     #     f.write("推送K线数据:\n" + str(kline_data))
#                     sq.pub_new_record(rec_data.type, kline_data, json_min_data)


# ------------------------------------------ 计算服务end---------------------------------------------------------

if __name__ == "__main__":
    # time.sleep(60*60*4.5)
    asyncio.get_event_loop().run_until_complete(future=start_sub(hk_stock_sub_address))
