# -*- coding: utf-8 -*-
#!/usr/bin/python
import time

import zmq
import zmq.asyncio
from google.protobuf import json_format
from py_sqlite.market import MarketSqliteDBClient
from pb_files.quote_msg_def_pb2 import *
from pb_files.quote_type_def_pb2 import *
from test_config import *
import asyncio
from common.common_method import get_log, Common

run_flag = True
sq = MarketSqliteDBClient()
test_log = get_log()


async def start(send_type, dealer_address):            # 创建一个异步函数，即“协程”
    print('dealer_address:', dealer_address)
    context = zmq.asyncio.Context(io_threads=5)
    dealer_socket = context.socket(socket_type=zmq.DEALER)
    dealer_socket.connect(dealer_address)
    poller = zmq.asyncio.Poller()
    poller.register(dealer_socket)
    returnFlag = False

    _start = time.time()
    while run_flag:
        print("时间 : {}".format(time.time() - _start))
        for event in await poller.poll():
            if send_type == 'SYNC_INSTR_REQ':
                if event[1] & zmq.POLLOUT:
                    data_send = SyncInstrReq(type=SyncInstrMsgType.ALL_INSTR, date_time=20200408)  # ALL_INSTR 全量同步，INCREMENT_INSTR 增量同步
                    quote_msg = QuoteMsgCarrier(type=QuoteMsgType.SYNC_INSTR_REQ, data=data_send.SerializeToString())
                    quote_msg = quote_msg.SerializeToString()
                    await event[0].send(quote_msg)
                    # print("send合约:\n{0}".format(quote_msg))

                if event[1] & zmq.POLLIN:
                    data = event[0].recv().result()
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(data)
                    if rev_data.type == QuoteMsgType.SYNC_INSTR_RSP:
                        rsp_data = SyncInstrRsp()
                        rsp_data.ParseFromString(rev_data.data)

                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        file_path = txt_file_save_folder + "InstrumentInfos.txt"
                        with open(file_path, 'w') as f:
                            f.write("合约数据:\n" + str(json_rsp_data))
                        sq.deal_new_record(rev_data.type, rsp_data, json_rsp_data)
                        returnFlag = True  # 退出循环，接收一次就可以了
                        break

            elif send_type == 'QUERY_RECOVERYDATA_REQ':  # 取股票的静态数据
                if event[1] & zmq.POLLOUT:
                    data_send = RecoveryDataReq(start_time_stamp=int(time.time()))
                    quote_msg = QuoteMsgCarrier(type=QuoteMsgType.QUERY_RECOVERYDATA_REQ, data=data_send.SerializeToString())

                    quote_msg = quote_msg.SerializeToString()
                    await event[0].send(quote_msg)
                    print("send静态:\n{0}".format(quote_msg))

                if event[1] & zmq.POLLIN:
                    data = event[0].recv().result()
                    print("recv:{0}".format(data))
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(data)
                    print(rev_data)

                    if rev_data.type == QUERY_RECOVERYDATA_RSP:
                        rsp_data = RecoveryDataRsp()
                        rsp_data.ParseFromString(rev_data.data)
                        basic_infos = rsp_data.basic_infos
                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        print("静态数据:\n{0}".format(basic_infos))
                        file_path = txt_file_save_folder + "Basic_info_dealer.txt"
                        with open(file_path, 'a') as f:
                            f.write("静态数据:\n" + str(json_rsp_data))

                        sq.deal_new_record(QuoteMsgType.SYNC_BASIC_RSP, basic_infos, json_rsp_data)
                        print(basic_infos)

                        rsp_data = RecoveryDataRsp()
                        rsp_data.ParseFromString(rev_data.data)
                        broker_snapshot_infos = rsp_data.broker_snapshot_infos
                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        print("经纪席位数据:\n{0}".format(broker_snapshot_infos))
                        file_path = txt_file_save_folder + "Broker_snapshot_infos_dealer.txt"
                        with open(file_path, 'a') as f:
                            f.write("经纪席位:\n" + str(json_rsp_data))

                        sq.deal_new_record(QuoteMsgType.PUSH_BROKER_SNAPSHOT, broker_snapshot_infos, json_rsp_data)
                        print(broker_snapshot_infos)

                        returnFlag = True  # 退出循环，接收一次就可以了
                        break

            elif send_type == 'SYNC_BASIC_REQ':  # 取期货的静态数据
                if event[1] & zmq.POLLOUT:
                    data_send = SyncBasicReq(type=SyncInstrMsgType.ALL_INSTR,
                                             date_time=20200408)  # ALL_INSTR 全量同步，INCREMENT_INSTR 增量同步
                    quote_msg = QuoteMsgCarrier(type=QuoteMsgType.SYNC_BASIC_REQ, data=data_send.SerializeToString())

                    quote_msg = quote_msg.SerializeToString()
                    await event[0].send(quote_msg)
                    print("send静态:\n{0}".format(quote_msg))

                if event[1] & zmq.POLLIN:
                    data = event[0].recv().result()
                    print("recv:{0}".format(data))
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(data)
                    print(rev_data)

                    if rev_data.type == QuoteMsgType.SYNC_BASIC_RSP:
                        rsp_data = SyncBasicRsp()
                        rsp_data.ParseFromString(rev_data.data)
                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        print("静态数据:\n{0}".format(rsp_data))

                        file_path = txt_file_save_folder + "Basic_info_dealer.txt"
                        with open(file_path, 'a') as f:
                            f.write("静态数据:\n" + str(rsp_data))
                        sq.deal_new_record(rev_data.type, rsp_data, json_rsp_data)
                        print(json_rsp_data)
                        pass

                        returnFlag = True  # 退出循环，接收一次就可以了
                        break
            elif send_type == 'SNAPSHOT_REQ':
                if event[1] & zmq.POLLOUT:
                    data_send = SyncInstrReq(type=SyncInstrMsgType.ALL_INSTR, date_time=20200408)  # ALL_INSTR 全量同步，INCREMENT_INSTR 增量同步
                    quote_msg = QuoteMsgCarrier(type=QuoteMsgType.SNAPSHOT_REQ, data=data_send.SerializeToString())
                    quote_msg = quote_msg.SerializeToString()
                    await event[0].send(quote_msg)
                    print("send快照:\n{0}".format(quote_msg))

                if event[1] & zmq.POLLIN:
                    data = event[0].recv().result()
                    print("recv:{0}".format(data))
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(data)
                    print(rev_data)

                    if rev_data.type == QuoteMsgType.SNAPSHOT_RSP:
                        rsp_data = SnapshotRsp()
                        rsp_data.ParseFromString(rev_data.data)
                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        print("快照数据:\n{0}".format(rsp_data))
                        file_path = txt_file_save_folder + "snap_shot_dealer.txt"
                        with open(file_path, 'a') as f:
                            f.write("快照数据:\n" + str(rsp_data))
                        sq.deal_new_record(rev_data.type, rsp_data, json_rsp_data)
                        print(json_rsp_data)
                        pass

                        returnFlag = True  # 退出循环，接收一次就可以了
                        break
            elif send_type == "ORDERBOOK_REQ":
                if event[1] & zmq.POLLOUT:
                    data_send = OrderbookReq(type=SyncInstrMsgType.ALL_INSTR, date_time=20210111, start_time_stamp=int(time.time()) *1000)  # ALL_INSTR 全量同步，INCREMENT_INSTR 增量同步
                    quote_msg = QuoteMsgCarrier(type=QuoteMsgType.ORDERBOOK_REQ, data=data_send.SerializeToString())
                    quote_msg = quote_msg.SerializeToString()
                    await event[0].send(quote_msg)

                if event[1] & zmq.POLLIN:
                    data = event[0].recv().result()
                    rev_data = QuoteMsgCarrier()
                    rev_data.ParseFromString(data)

                    if rev_data.type == QuoteMsgType.ORDERBOOK_RSP:
                        rsp_data = OrderbookRsp()
                        rsp_data.ParseFromString(rev_data.data)
                        json_rsp_data = json_format.MessageToJson(rsp_data)
                        # json_rsp_data = json_format.MessageToDict(rsp_data)
                        print("盘口数据:\n{0}".format(rsp_data))
                        file_path = txt_file_save_folder + "ORDERBOOK_dealer.txt"
                        with open(file_path, 'a') as f:
                            f.write("盘口数据:\n" + str(rsp_data))
                        sq.deal_new_record(rev_data.type, rsp_data, json_rsp_data)
                        print(json_rsp_data)
                        # for orderbook in json_rsp_data["orderbookInfos"]:
                        #     instrCode = Common().searchDicKV(orderbook, "instrCode")
                        #     print(instrCode)

                        returnFlag = True  
                        break



            if event[1] & zmq.POLLERR:
                print("error:{0},{1}".format(event[0], event[1]))

        if returnFlag == True:
            break
        await asyncio.sleep(delay=10)                                                   # 使用 asyncio.sleep(), 它返回的是一个可等待的对象


if __name__ == "__main__":
    if not os.path.exists(txt_file_save_folder):
        os.makedirs(txt_file_save_folder)
    asy = asyncio.get_event_loop()                                                   # 创建一个事件循环
    asy.run_until_complete(future=start('QUERY_RECOVERYDATA_REQ', us_stock_dealer_address))  # 执行事件队列, 直到最后的一个事件被处理完毕后结束
    # SYNC_INSTR_REQ：合约的    QUERY_RECOVERYDATA_REQ：（证券）静态的、经纪席位数据   SYNC_BASIC_REQ：（期货）静态的   SNAPSHOT_REQ：快照的
    # ORDERBOOK_REQ : 盘口