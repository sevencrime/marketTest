# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/9/10
# @Software: PyCharm

import zmq
import zmq.asyncio
from websocket_py3.ws_api.subscribe_api_for_second_phase import *
from common.common_method import Common
from http_request.market import MarketHttpClient
import json


class Check(object):
    def __init__(self):
        self.common = Common()
        self.logger = get_log()
        self.http = MarketHttpClient()
        self.market_token = self.http.get_market_token(
            self.http.get_login_token(phone=login_phone, pwd=login_pwd, device_id=login_device_id))
        self.new_loop = self.common.getNewLoop()
        asyncio.set_event_loop(self.new_loop)
        self.api = SubscribeApi(union_ws_url, self.new_loop)
        asyncio.get_event_loop().run_until_complete(future=self.api.client.ws_connect())
        asyncio.get_event_loop().run_until_complete(
            future=self.api.LoginReq(token=self.market_token))
        asyncio.run_coroutine_threadsafe(self.api.hearbeat_job(), self.new_loop)

    async def get_instrument(self, send_type, dealer_address):
        context = zmq.asyncio.Context(io_threads=5)
        dealer_socket = context.socket(socket_type=zmq.DEALER)
        dealer_socket.connect(dealer_address)
        poller = zmq.asyncio.Poller()
        poller.register(dealer_socket)
        send_flag = True
        json_rsp_data = None
        while True:
            for event in await poller.poll():
                if send_type == 'SYNC_INSTR_REQ':
                    if event[1] & zmq.POLLOUT and send_flag:
                        data_send = SyncInstrReq(type=SyncInstrMsgType.ALL_INSTR, date_time=20200408)  # ALL_INSTR 全量同步，INCREMENT_INSTR 增量同步
                        quote_msg = QuoteMsgCarrier(type=QuoteMsgType.SYNC_INSTR_REQ, data=data_send.SerializeToString())
                        quote_msg = quote_msg.SerializeToString()
                        await event[0].send(quote_msg)
                        send_flag = False

                    if event[1] & zmq.POLLIN:
                        data = event[0].recv().result()
                        rev_data = QuoteMsgCarrier()
                        rev_data.ParseFromString(data)
                        if rev_data.type == QuoteMsgType.SYNC_INSTR_RSP:
                            rsp_data = SyncInstrRsp()
                            rsp_data.ParseFromString(rev_data.data)
                            json_rsp_data = json_format.MessageToJson(rsp_data)
                            json_rsp_data = json.loads(json_rsp_data)
                            break
                    if event[1] & zmq.POLLERR:
                        print("error:{0},{1}".format(event[0], event[1]))
                await asyncio.sleep(delay=5)                                                   # 使用 asyncio.sleep(), 它返回的是一个可等待的对象
            if json_rsp_data:
                return json_rsp_data

    def get_mastr_code(self, exchange, product):
        start_time_stamp = int(time.time() * 1000)
        sub_type = SubscribeMsgType.SUB_WITH_PRODUCT
        base_info = [{'exchange': exchange, 'product_code': product}]
        rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.SubsQutoMsgReqApi(sub_type=sub_type, base_info=base_info,
                                              start_time_stamp=start_time_stamp))
        master_code = None
        open_interrest = 0
        for snapshot in rsp['before_snapshot_json_list']:
            if int(self.common.doDicEvaluate(snapshot['future'], 'openInterrest', 0)) >= open_interrest and \
                    'main' not in snapshot['commonInfo']['instrCode']:
                master_code = snapshot['commonInfo']['instrCode']
                open_interrest = int(self.common.doDicEvaluate(snapshot['future'], 'openInterrest', 0))
        rsp = asyncio.get_event_loop().run_until_complete(
            future=self.api.UnSubsQutoMsgReqApi(unsub_type=sub_type, unbase_info=base_info,
                                                start_time_stamp=start_time_stamp))
        return master_code

    def check_all_instr(self):
        instruments = asyncio.get_event_loop().run_until_complete(
            future=self.get_instrument('SYNC_INSTR_REQ', codegenerate_dealer_address))
        self.logger.debug(instruments)
        for instrument in instruments['instruments']:
            if 'main' in instrument['base']['instrCode']:
                self.logger.debug(instrument)
                product = instrument['proc']['code']
                exchange = instrument['base']['exchange']
                # product = 'CUS'
                # exchange = 'HKFE'
                master_code = self.get_mastr_code(exchange, product)
                api_master_code = instrument['future']['relatedInstr']
                assert master_code == api_master_code


if __name__ == "__main__":
    c = Check()
    c.check_all_instr()


