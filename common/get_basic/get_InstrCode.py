#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio
import datetime
import re
import json
import threading
import time

import requests

from common.common_method import Common
from common.test_log.ed_log import get_log
from pb_files.quote_type_def_pb2 import *
from py_sqlite.market import MarketSqliteDBClient
from test_config import *
from zmq_py3.router_dealer.dealer import start

sq = MarketSqliteDBClient()
logger = get_log()
common = Common()

# 获取所有合约
def get_all_instrCode():
    instrCodeList = []
    check_info = sq.get_deal_json_records(QuoteMsgType.SYNC_INSTR_RSP, 100)
    # 拿第一个
    for info in check_info:
        json_info = json.loads(info[0])
        instruments = json_info['instruments']
        for instrument in instruments:
            base = instrument['base']
            proc = instrument['proc']
            exchange = base['exchange']
            instrCode = base['instrCode']
            producttype = common.searchDicKV(instrument, "producttype")

            categoryType = proc["categoryType"]


            # if producttype not in  ["IPO", "GREY_MARKET"] and categoryType == "STOCKS" :
            #     instrCodeList.append(tuple([exchange, instrCode]))

            if categoryType == "FUTURE":
                expireDate = instrument["future"]["expireDate"]   # 到期日
                print("合约 : {}, 到期日: {}".format(instrCode, expireDate))

    return instrCodeList

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def update_instar():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    # loop.run_until_complete(future=start('SYNC_INSTR_REQ', codegenerate_dealer_address))
    await start('SYNC_INSTR_REQ', codegenerate_dealer_address)
    logger.debug("码表更新成功", time.time())


async def get_instr_API(code):    # API服务用
    # 传入code 从码表返回信息
    currentDayTimeStampInfo = common.getCurrentDayTimeStampInfo()
    start_stamp = currentDayTimeStampInfo['todayBeginTimeStamp']
    end_stamp = currentDayTimeStampInfo['todayEndTimeStamp']
    sql = "select json_info, record_time from deal_router_info where data_type = '10' and record_time >= {} and record_time < {} ORDER BY id DESC LIMIT 2;".format(start_stamp, end_stamp)
    check_info = sq.multi_select(sql)
    if not check_info:
        loop = asyncio.new_event_loop()  # 创建一个事件循环
        t = threading.Thread(target=start_loop, args=(loop,))
        t.start()

        # asyncio.run_coroutine_threadsafe(start('SYNC_INSTR_REQ', codegenerate_dealer_address), loop)
        asyncio.run_coroutine_threadsafe(update_instar(), loop)
        logger.debug("码表正在更新, 请20秒后再访问")
        return "码表正在更新, 请20秒后再访问, 更新阶段请不要操作, 谢谢!!!", "更新中"


    for info in check_info:
        instr_update_stamp = datetime.datetime.fromtimestamp(info[1]).strftime("%Y-%m-%d %H:%M:%S.%f")
        logger.debug("码表的更新时间为 : {}".format(instr_update_stamp))
        json_info = json.loads(info[0])
        instruments = json_info['instruments']
        base = common.searchDict_By_Value(instruments, code)
        if base and base.get("instrCode") != code:
            logger.debug("合约代码不是唯一的, 请检查合约代码 -- 《{}》".format(code))
            return "合约代码不是唯一的, 请检查合约代码 -- 《{}》".format(code)

        instr = common.searchDict_By_Value(instruments, base)
        if not instr:
            logger.debug("没有找到合约, 请检查合约代码 -- 《{}》".format(code))
            return "没有找到合约, 请检查合约代码 -- 《{}》".format(code)

        print(common.to_json(instr))

        # return instr
        # return {"码表更新时间": instr_update_stamp, "码表信息": instr}
        return instr_update_stamp, instr

def get_001(): # 调试方法
    import os
    path = r"D:\\Test\\marketTest\\report\\allure\\allure_report\\time_20201216181949\\data\\test-cases"  # 文件夹目录
    files = os.listdir(path)  # 得到文件夹下的所有文件名称
    s = []
    for file in files:  # 遍历文件夹
        if not os.path.isdir(file):  # 判断是否是文件夹，不是文件夹才打开
            f = open(path + "/" + file, "r", encoding="utf-8");  # 打开文件
            iter_f = iter(f);  # 创建迭代器
            str = ""
            for line in iter_f:  # 遍历文件，一行行遍历，读取文本
                str = str + line
            resultdict = json.loads(str)
            if resultdict["status"] != "passed":
                logger.error("########################################")
                logger.error("uid : {}".format(resultdict["uid"]))
                logger.error("标题 : {}".format(resultdict["description"]))
                if "昨收价不一致" in resultdict["statusMessage"]:
                    logger.error(resultdict["statusMessage"])
                # logger.error(resultdict["statusTrace"])
                logger.error("########################################\n\n")



if __name__ == "__main__":
    # code = get_all_instrCode()
    # print(code)
    # print(code.__len__())

    loop = asyncio.get_event_loop()
    a = loop.run_until_complete(future=get_instr_API("11477"))
    print(a)