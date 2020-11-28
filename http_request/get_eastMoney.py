# -*- coding: utf-8 -*-
# !/usr/bin/python

##############################
## 从东财爬股票的币种
# f43 : 最新价
# f44 : 最高
# f45 : 最低
# f46 : 今开
# f47 : 成交量
# f48 : 成交额
# f50 : 量比
# f51 : 涨停
# f52 : 跌停
# f60 : 昨收
# f116 : 总市值
# f117 : 流通市值
# f162 : 市盈动
# f167 : 市净
# f12 : 名字
# f14 : 币种
###############3

import requests
import re
import json
import asyncio
import time

import aiohttp

from test_config import *
from common.common_method import Common

# 东财港股股票
eastMoney_StockApi = "http://68.push2.eastmoney.com/api/qt/clist/get?cb=jQuery112402946500145117943_1603423557503&pn={page}&pz={count}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:128+t:3,m:128+t:4,m:128+t:1,m:128+t:2&fields=f12,f14&_={timestamp}"
# 东财港股涡轮
eastMoney_WarrantApi = "http://20.push2.eastmoney.com/api/qt/clist/get?cb=jQuery112406107316826163705_1603674916003&pn={page}&pz={count}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:128+t:6&fields=f12,f14&_={timestamp}"
# 东财港股牛熊证
eastMoney_cbbcApi = "http://72.push2.eastmoney.com/api/qt/clist/get?cb=jQuery11240457030630924556_1603704174724&pn={page}&pz={count}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f6&fs=m:128+t:5&fields=f12,f14&_={timestamp}"
# 东财行情信息
eastMoney_currency_uri = r"http://push2.eastmoney.com/api/qt/stock/get?secid=116.{code}&fields=f172&_={timestamp}"

headers = {
    'content-type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
}


# 请求东财页面, 解析出币种信息
async def get(session, stock):
    uri = eastMoney_currency_uri.format(code=stock["code"], timestamp=int(time.time() * 1000))
    # print("正在请求 : {}".format(uri))

    async with session.get(uri, headers=headers) as response:
        if response.status != 200:
            response.raise_for_status()
        resp = await response.json()

    currency = resp["data"]["f172"]
    if currency not in ["HKD", "CNY", "USD"]:
        print("code : {}, 币种 : {}".format(stock["code"], currency))
    # stock["currency"] = currency if currency != "" else "HKD"
    stock["currency"] = currency
    return {stock["code"] : stock}

# 获取东财股票代码对应的币种
async def get_eastMoney_basic(stockList):
    stockBase = {}

    async with aiohttp.ClientSession() as session:
        tasks = [get(session, stock) for stock in stockList]
        doneSet, pendingSet = await asyncio.wait(tasks)

        print("成功个数", len(doneSet))
        print("失败个数", len(pendingSet))

        for doneInfo in doneSet:
            if doneInfo._result != None: # 因断连等原因导致返回为None时，这里过滤掉
                # print(doneInfo._result)
                stockBase.update(doneInfo._result)

        if pendingSet:
            print("失败了???")
            for pending in pendingSet:
                pending.cancel()

        file_path = txt_file_save_folder + "eastMoney.txt"
        with open(file_path, "a", encoding='utf-8') as f:
            f.write(str(Common().to_json(stockBase)))

        print(len(stockBase))

# 获取东财的股票代码
async def get_eastMoney_stockCode():
    stock_apiURI = eastMoney_StockApi.format(page=1, count=10000, timestamp=int(time.time() * 1000)).replace(" ", "")
    warrant_apiURI = eastMoney_WarrantApi.format(page=1, count=10000, timestamp=int(time.time() * 1000)).replace(" ", "")
    cbbc_apiURI = eastMoney_cbbcApi.format(page=1, count=10000, timestamp=int(time.time() * 1000)).replace(" ", "")

    print("东财港股股票的连接为 : {}".format(stock_apiURI))
    print("东财港股涡轮的连接为 : {}".format(warrant_apiURI))
    print("东财港股牛熊证的连接为 : {}".format(cbbc_apiURI))
    stockList = []
    async with aiohttp.request("get", stock_apiURI) as r:
        resp = await r.text()
        stock_fields = re.findall(r"{[^}[]*}", resp)
        for stock in stock_fields :
            stock = stock.replace("f12", "code").replace("f14", "name")
            stock = json.loads(stock)
            stock["product_code"] = "stock"
            stockList.append(stock)


    async with aiohttp.request("get", warrant_apiURI) as r:
        resp = await r.text()
        stock_fields = re.findall(r"{[^}[]*}", resp)
        for stock in stock_fields :
            stock = stock.replace("f12", "code").replace("f14", "name")
            stock = json.loads(stock)
            stock["product_code"] = "warrant"
            stockList.append(stock)


    async with aiohttp.request("get", cbbc_apiURI) as r:
        resp = await r.text()
        stock_fields = re.findall(r"{[^}[]*}", resp)
        for stock in stock_fields :
            stock = stock.replace("f12", "code").replace("f14", "name")
            stock = json.loads(stock)
            stock["product_code"] = "cbbc"
            stockList.append(stock)


    print(stockList.__len__())
    return stockList

loop = asyncio.get_event_loop()
stockList = loop.run_until_complete(get_eastMoney_stockCode())
loop.run_until_complete(get_eastMoney_basic(stockList))

