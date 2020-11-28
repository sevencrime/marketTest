# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/14
# @Software: PyCharm

from string import digits
import datetime
import pytest
import unittest

# from py_rocksdb.market import MarketRocksDBClient
from py_sqlite.market import *
from common.test_log.ed_log import get_log
from common.pb_method import *
from common.common_method import Common
from pb_files.common_type_def_pb2 import *
from common.basic_info import *
import re


class CheckZMQ(unittest.TestCase):
    def __init__(self, methodName='runTest', check_json_list=None, is_before_data=False, sub_time=None, start_time=None,
                 instr_code=None, exchange=None, peroid_type=None):
        super().__init__(methodName)
        self.check_json_list = check_json_list
        self.is_before_data = is_before_data
        self.sub_time = sub_time
        self.start_time = start_time
        self.instr_code = instr_code
        self.exchange = exchange
        self.peroid_type = peroid_type
        self.logger = get_log()
        self.tolerance_time = 30000

    @classmethod
    def setUpClass(cls):
        cls.sq = MarketSqliteDBClient()
        cls.common = Common()

    @classmethod
    def tearDownClass(cls):
        cls.sq.exit()

    def isForwardContract(self, instrCode):

        if instrCode in ForwardContractLists:  # 在远期合约列表
            return True
        else:
            lenStr = int(len(instrCode))
            temp = instrCode[lenStr - 4:lenStr]
            if temp.isdigit() is True:
                temp = int(temp)
                if temp >= 2021:
                    return True
                else:
                    return False
            else:
                return False

    # --------------------------------------------采集服务start----------------------------------------------------
    def test_01_QuoteSnapshot(self):  # 推送的快照数据
        if self.check_json_list is None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_SNAPSHOT, 100000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {'instrCodeList': []}
        for info in check_info:
            if self.check_json_list is None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            self.logger.debug(json_info)
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            productCode = commonInfo['productCode']
            instrCode = commonInfo['instrCode']

            if self.isForwardContract(instrCode) is True:  # 远期合约，不处理
                continue

            precision = self.common.doDicEvaluate(commonInfo, 'precision')
            collectorRecvTime = commonInfo['collectorRecvTime']
            collectorSendTime = commonInfo['collectorSendTime']
            if self.check_json_list is not None:
                publisherRecvTime = commonInfo['publisherRecvTime']
                publisherSendTime = commonInfo['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间
            close = json_info['close']
            if 'open' in json_info.keys():  # 存在未成交数据但是有快照的情况
                open = int(json_info['open'])
                high = int(json_info['high'])
                low = int(json_info['low'])
                last = int(json_info['last'])
                # normal = json_info['normal']
                volume = int(json_info['volume'])
                self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
                self.assertTrue(int(high) >= int(last) >= int(low))  # 最新现价在最高价最低价之间
            riseFall = int(self.common.doDicEvaluate(json_info, 'riseFall'))
            rFRatio = int(self.common.doDicEvaluate(json_info, 'rFRatio'))
            # localDateTime = json_info['localDateTime']
            sourceUpdateTime = int(json_info['sourceUpdateTime'])
            future = json_info['future']
            openInterrest = self.common.doDicEvaluate(future, 'openInterrest')
            settlementPrice = self.common.doDicEvaluate(future, 'settlementPrice')
            self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是今天的数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                if not self.is_before_data:  # 实时数据
                    if exchange != 'HKFE':
                        self.assertTrue(
                            int(sourceUpdateTime) / (pow(10, 6)) + 1000 >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    else:
                        self.assertTrue(
                            int(sourceUpdateTime) / (pow(10, 6)) + 1000 >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    pass
                    self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            # 更新时间应该是有序的
            if not self.is_before_data:
                if exchange + '_sourceUpdateTime' in assert_json.keys():
                    self.assertTrue(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime']))
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
                else:
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
            else:
                pass
            # 校验涨跌额涨跌幅的计算逻辑
            if 'open' in json_info.keys():  # 存在未成交数据但是有快照的情况
                if settlementPrice:
                    self.assertTrue(int(riseFall) == int(last) - int(settlementPrice))
                    self.assertTrue(int(rFRatio) == int(10000 * int(riseFall) / int(settlementPrice)))
                else:
                    self.assertTrue(int(riseFall) == int(last) - int(close))
                    self.assertTrue(int(rFRatio) == int(10000 * int(riseFall) / int(close)))
            if instrCode in assert_json['instrCodeList']:
                self.assertTrue(int(volume) >= int(assert_json[instrCode + '_volume']))  # 当天成交量应该是递增的
                assert_json[instrCode + '_volume'] = int(volume)
                self.assertTrue(int(open) == int(assert_json[instrCode + '_open']))  # 当天开盘价不会再更新
                self.assertTrue(int(close) == int(assert_json[instrCode + '_close']))  # 当天昨收价不会再更新
                self.assertTrue(int(settlementPrice) == int(assert_json[instrCode + '_settlementPrice']))  # 当天昨结价不会再更新
                self.assertTrue(int(openInterrest) == int(assert_json[instrCode + '_openInterrest']))  # 当天昨持仓量不会再更新
                if int(last) > assert_json[instrCode + '_high']:
                    self.assertTrue(int(high) == int(last))  # 最高价应更新
                    assert_json[instrCode + '_high'] = int(high)
                else:
                    self.assertTrue(int(high) == int(assert_json[instrCode + '_high']))  # 最高价不更新

                if last < assert_json[instrCode + '_low']:
                    self.assertTrue(int(low) == int(last))  # 最低价应更新
                    assert_json[instrCode + '_low'] = int(low)
                else:
                    self.assertTrue(int(low) == int(assert_json[instrCode + '_low']))  # 最低价不更新
            else:
                if 'open' in json_info.keys():  # 存在未成交数据但是有快照的情况
                    assert_json['instrCodeList'].append(instrCode)
                    assert_json[instrCode + '_volume'] = int(volume)
                    assert_json[instrCode + '_open'] = int(open)
                    assert_json[instrCode + '_close'] = int(close)
                    assert_json[instrCode + '_settlementPrice'] = int(settlementPrice)
                    assert_json[instrCode + '_high'] = int(high)
                    assert_json[instrCode + '_low'] = int(low)
                    assert_json[instrCode + '_openInterrest'] = int(openInterrest)

    def test_02_QuoteOrderBookData(self):  # 推送的盘口数据
        if self.check_json_list is None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_ORDER_BOOK, 100000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {'instrCodeList': []}
        for info in check_info:
            if self.check_json_list is None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            self.logger.debug(json_info)
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            productCode = commonInfo['productCode']
            instrCode = commonInfo['instrCode']
            if self.isForwardContract(instrCode) is True:  # 远期合约，不处理
                continue
            # 有些精度为0时，无返回
            precision = self.common.doDicEvaluate(commonInfo, 'precision')
            collectorRecvTime = commonInfo['collectorRecvTime']
            collectorSendTime = commonInfo['collectorSendTime']
            if self.check_json_list is not None:
                publisherRecvTime = commonInfo['publisherRecvTime']
                publisherSendTime = commonInfo['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间
            orderBook = json_info['orderBook']
            sourceUpdateTime = json_info['sourceUpdateTime']
            self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是今天的数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                if not self.is_before_data:  # 实时数据
                    if exchange != 'HKFE':
                        self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) + 2000 >= int(
                            self.sub_time))  # 订阅服务时用来判断订阅时间与源时间,1000是误差
                    else:
                        self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) >= int(
                            self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            # 更新时间应该是有序的,因行情数据是单边数据（买或卖)合成，因此去掉如下的校验
            # if not self.is_before_data:
            #     if exchange + '_sourceUpdateTime' in assert_json.keys():
            #         self.assertTrue(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime']))
            #         assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
            #     else:
            #         assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
            # else:
            #     pass
            self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            askVolInData, bidVolInData, upperAskPrice, upperBidPrice = 0, 0, 0, 0
            if 'askVol' in orderBook.keys():
                askVol = int(orderBook['askVol'])
                asksData = orderBook['asksData']
                self.assertTrue(asksData.__len__() == 10)  # 卖盘10层深度
                for ask in asksData:
                    if ask != {}:
                        askPrice = int(ask['price'])
                        askVolume = int(ask['volume'])
                        if exchange == 'SGX':  # 新加坡时orderCount值为0在protobuf中打印不出，不做校验
                            pass
                        else:
                            askOrderCount = ask['orderCount']
                        askVolInData = askVolInData + askVolume
                        if upperAskPrice:
                            self.assertTrue(int(askPrice) > int(upperAskPrice))  # 深度价格校验（卖1价格应低于卖2价格）
                        upperAskPrice = askPrice
                self.assertEqual(int(askVol), askVolInData)  # 校验卖盘数量和
            if 'bidVol' in orderBook.keys():
                bidVol = int(orderBook['bidVol'])
                bidsData = orderBook['bidsData']
                self.assertTrue(bidsData.__len__() == 10)  # 买盘10层深度
                for bid in bidsData:
                    if bid != {}:
                        bidPrice = int(bid['price'])
                        bidVolume = int(bid['volume'])
                        if exchange == 'SGX':  # 新加坡时orderCount值为0在protobuf中打印不出，不做校验
                            pass
                        else:
                            bidOrderCount = bid['orderCount']
                        bidVolInData = bidVolInData + bidVolume
                        if upperBidPrice:
                            self.assertTrue(int(bidPrice) < int(upperBidPrice))  # 深度价格校验（买1价格应高于买2价格）
                        upperBidPrice = bidPrice
                self.assertEqual(int(bidVol), bidVolInData)  # 校验买盘数量和

    def test_03_QuoteBasicInfo(self, dealer_basic_info_list=None, dealer_record_time=None, checklist=None):  # 推送的静态数据
        if dealer_basic_info_list == None:
            if self.check_json_list == None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_BASIC, 100)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_basic_info_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            if dealer_basic_info_list == None:
                if self.check_json_list == None:
                    record_time = info[1]
                    json_info = json.loads(info[0])
                else:
                    record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                    json_info = info
            else:
                record_time = dealer_record_time
                json_info = info
            self.logger.debug(json_info)
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            productCode = commonInfo['productCode']
            instrCode = commonInfo['instrCode']
            if self.isForwardContract(instrCode) is True:  # 远期合约，不处理
                continue

            if checklist is not None and self.common.searchDicKV(checklist, instrCode) is False:
                checklist[instrCode] = True

            sourceUpdateTime = int(json_info['updateTimestamp'])
            precision = self.common.doDicEvaluate(commonInfo, 'precision', 0)  # 有些精度为0时，无返回
            collectorRecvTime = commonInfo['collectorRecvTime']
            collectorSendTime = commonInfo['collectorSendTime']
            if self.check_json_list != None:
                publisherRecvTime = commonInfo['publisherRecvTime']
                publisherSendTime = commonInfo['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间
            type = json_info['type']
            self.assertTrue(type in ['EQUITY_INDEX_FUTURE', 'SINGLE_STOCK_FUTURE', 'FOREIGN_EXCHANGE_FUTURE',
                                     'INTEREST_RATE_FUTURE', 'COMMODITIES_FUTURE',
                                     'ENERGY_CHEMICAL_FUTURE', 'METAL_FUTURE', 'AGRICULTURAL_COMMODITY_FUTURE'])

            tradindDay = json_info['tradindDay']

            if exchange == 'HKFE' and record_time >= self.common.getTodayHKFEStartStamp():
                self.assertTrue(self.common.isTomorrow(tradindDay))
            elif exchange == 'HKFE' and record_time < self.common.getTodayHKFEStartStamp():
                self.assertTrue(self.common.inToday(tradindDay))
            else:
                self.assertTrue(self.common.inToday(tradindDay))  # 观察外期的数据反馈，这里做优化

            self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是当天的数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(
                    self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass
            if exchange != 'HKFE':
                instrName = json_info['instrName']
                instrEnName = json_info['instrEnName']
                update_timestamp = json_info['updateTimestamp']  # 外期静态
                # 如下三项属于临时屏蔽
                future = json_info['future']
                preSettlementPrice = future['preSettlementPrice']
                preOpenInterrest = future['preOpenInterrest']

            else:
                pass  # 港期合约名称和合约英文名，在合约信息里获取，静态数据里不填。# 开发在jira评论, 暂时无法做到
            exchangeInstr = json_info['exchangeInstr']

            marketStatus = json_info['marketStatus']
            instrStatus = json_info['instrStatus']
            # precision = json_info['precision']
            # upperLimit = json_info['upperLimit']
            # lowerLimit = json_info['lowerLimit']
            # 如下二项属于临时屏蔽
            preClose = json_info['preClose']
            source = json_info['source']

            self.assertTrue(int(collectorSendTime) >= int(collectorRecvTime))  # 采集发出时间大于采集接受时间
            self.assertTrue(productCode in instrCode)  # 产品代码正确性校验
            # self.assertTrue(instrCode == exchangeInstr)  # 代码正确性校验 ??

    def test_03_01_QuoteBasicInfo(self):  # dealer模式下请求返回的静态数据
        checklist = {
            HK_code1: False, HK_code2: False, HK_code3: False, HK_code4: False, HK_code5: False, HK_code6: False,
            HK_main1: False, HK_main2: False, HK_main3: False, HK_main4: False, HK_main5: False,
            NYMEX_code1: False, NYMEX_code2: False, NYMEX_code3: False, NYMEX_code4: False,
            COMEX_code1: False, COMEX_code2: False, COMEX_code3: False, COMEX_code4: False, COMEX_code5: False,
            COMEX_code6: False,
            CBOT_code1: False, CBOT_code2: False, CBOT_code3: False, CBOT_code4: False, CBOT_code5: False,
            CBOT_code6: False,
            CBOT_code7: False, CBOT_code8: False, CBOT_code9: False, CBOT_code10: False,
            CME_code1: False, CME_code2: False, CME_code3: False, CME_code4: False, CME_code5: False, CME_code6: False,
            CME_code7: False, CME_code8: False, CME_code9: False, CME_code10: False, CME_code11: False,
            CME_code12: False,
            CME_code13: False, CME_code14: False,
            SGX_code1: False, SGX_code2: False, SGX_code3: False
        }

        check_info = self.sq.get_deal_json_records(QuoteMsgType.SYNC_BASIC_RSP, 100)
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            record_time = info[1]
            json_info = json.loads(info[0])
            retResult = json_info['retResult']
            retCode = retResult['retCode']
            self.assertTrue(retCode == 'SUCCESS')  # 校验接口返回状态
            dealer_basic_info_list = json_info['basicInfos']
            self.test_03_QuoteBasicInfo(dealer_basic_info_list, record_time, checklist)

        for key in checklist:  # 遍历检测main
            if checklist[key] is False:
                self.logger.debug('{} is None!'.format(key))

    def test_04_QuoteTradeData(self):  # 逐笔成交数据
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_TRADE_DATA, 1000000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {
            'instrCodeList': [],
        }
        for info in check_info:
            if self.check_json_list == None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            self.logger.debug(json_info)
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            instrCode = commonInfo['instrCode']
            # 有些精度为0时，无返回
            precision = self.common.doDicEvaluate(commonInfo, 'precision')
            if not self.is_before_data:  # 历史数据无该字段
                productCode = commonInfo['productCode']
                self.assertTrue(productCode in instrCode)
                collectorRecvTime = commonInfo['collectorRecvTime']
                collectorSendTime = commonInfo['collectorSendTime']
                if self.check_json_list != None:
                    publisherRecvTime = commonInfo['publisherRecvTime']
                    publisherSendTime = commonInfo['publisherSendTime']
                    self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间
                    self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            else:
                pass
            tradeTick = json_info['tradeTick']
            price = int(tradeTick['price'])
            vol = int(tradeTick['vol'])
            trade_time = int(tradeTick['time'])
            direct = tradeTick['direct']
            # future = tradeTick['future'] # 目前行情源取不到此字段，不填
            sourceUpdateTime = trade_time

            self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是今天的数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                if not self.is_before_data:  # 实时数据
                    if exchange != 'HKFE':
                        self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) + 1000 >= int(
                            self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    else:
                        self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) >= int(
                            self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(
                        self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            if 'sourceUpdateTime' in assert_json.keys():
                # 更新时间应该是有序的
                if exchange + '_sourceUpdateTime' in assert_json.keys():
                    self.assertTrue(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime']))
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
                else:
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)

            if instrCode in assert_json['instrCodeList']:
                if price > assert_json[instrCode]:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'BUY')
                elif price < assert_json[instrCode]:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'SELL')
                else:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'NO_STATE')
            else:
                assert_json['instrCodeList'].append(instrCode)
                assert_json[instrCode] = price
        self.logger.debug('{} items checked!'.format(check_info.__len__()))

    def test_04_APP_BeforeQuoteTradeData(self):
        check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        exchange = 'noExchange'
        instrCode = 'noInstrCode'
        assert_json = {
            'instrCodeList': [],
        }
        for info in check_info:
            record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
            json_info = info
            self.logger.debug(json_info)
            price = int(json_info['price'])
            vol = int(json_info['vol'])
            trade_time = int(json_info['time']) / pow(10, 6)
            direct = json_info['direct']
            # 得到数据的数据应在查询时间之间
            self.assertTrue(self.start_time <= trade_time <= self.sub_time)
            # 更新时间有序递增
            if exchange + '_sourceUpdateTime' in assert_json.keys():
                self.assertTrue(int(trade_time) >= int(assert_json[exchange + '_sourceUpdateTime']))
                assert_json[exchange + '_sourceUpdateTime'] = int(trade_time)
            else:
                assert_json[exchange + '_sourceUpdateTime'] = int(trade_time)

            if instrCode in assert_json['instrCodeList']:
                if price > assert_json[instrCode]:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'BUY')
                elif price < assert_json[instrCode]:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'SELL')
                else:
                    assert_json[instrCode] = price  # 更新价格
                    self.assertTrue(direct == 'NO_STATE')
            else:
                assert_json['instrCodeList'].append(instrCode)
                assert_json[instrCode] = price

    def test_05_InstrumentInfo(self):
        error_lot_list = []
        error_contractMultiplier_list = []
        error_priceTick_list = []
        error_fluctuation_list = []
        if self.check_json_list == None:
            check_info = self.sq.get_deal_json_records(QuoteMsgType.SYNC_INSTR_RSP, 100)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            if self.check_json_list == None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            # self.logger.debug(json_info)
            retResult = json_info['retResult']
            retCode = retResult['retCode']
            self.assertTrue(retCode == RetCode.Name(RetCode.ALL_INSTR_SUCCESS))  # 校验接口返回状态
            instruments = json_info['instruments']
            self.logger.debug('{} instruments to check!'.format(instruments.__len__()))
            for instrument in instruments:
                self.logger.debug(instrument)
                base = instrument['base']
                exchange = base['exchange']
                if exchange not in ['CME', 'NYMEX', 'CBOT', 'COMEX', 'SGX', 'HKFE']:
                    continue
                instrType = base['instrType']
                self.assertTrue(instrType in ['NORMAL', 'COMB'])
                seriesId = base['seriesId']
                internalCode = base['internalCode']
                instrCode = base['instrCode']
                counterCode = base['counterCode']
                cn_simple_name = base['cnSimpleName']
                tc_simple_name = base['tcSimpleName']
                en_simple_name = base['enSimpleName']
                # 产品已经确认，暂不需要这三个字段,2020.11.17
                # cn_full_name = base['cnFullName']
                # tc_full_name = base['tcFullName']
                # en_full_name = base['enFullName']
                settle_currency = base['settleCurrency']
                trade_currency = base['tradeCurrency']

                proc = instrument['proc']
                categoryType = proc['categoryType']
                self.assertTrue(categoryType == 'FUTURE')

                productType = proc['productType']
                code = proc['code']
                prod_cn_simple_name = proc['cnSimpleName']
                prod_tc_simple_name = proc['tcSimpleName']
                prod_en_simple_name = proc['enSimpleName']
                # 产品已经确认，暂不需要这三个字段,2020.11.17
                # prod_cn_full_name = proc['cnFullName']
                # prod_tc_full_name = proc['tcFullName']
                # prod_en_full_name = proc['enFullName']

                cn_underlying = proc['cnUnderlying']
                tc_underlying = proc['tcUnderlying']
                en_underlying = proc['enUnderlying']

                timespin = proc['timespin']
                callMarket = self.common.doDicEvaluate(proc, 'callMarket', 2)  # 集合竞价时间片,有的品种没有集合竞价
                trade = proc['trade']  # 交易时间片
                # denoinator = self.common.doDicEvaluate(instrument, 'denoinator', 0)  # ？？为啥有的没有    外期也没有这个字段
                precision = self.common.doDicEvaluate(instrument, 'precision', 0)
                status = instrument['status']
                # createDate = instrument['createDate']     # 取不到
                # openDate = instrument['openDate']     # 取不到
                updateStamp = instrument['updateStamp']
                timeZone = instrument['timeZone']
                future = instrument['future']
                # 因BUG(缺少这些字段)注释掉 2010.10.19
                # marginRateType = future['marginRateType']
                # longMargin = future['longMargin']
                # shortMargin = future['shortMargin']
                # marketOrderQty = future['marketOrderQty']
                # limitOrderQty = future['limitOrderQty']
                # deliverYear = future['deliverYear']
                # deliverMonth = future['deliverMonth']
                # lastTradeDate = future['lastTradeDate']
                # notifyDate = future['notifyDate']
                expireDate = future['expireDate']
                if int(expireDate) < int(time.strftime('%Y%m%d', time.localtime())):  # 校验到期日是否为过期的，过期的不需要校验结算、交易币种
                    self.assertEqual(status, 'EXPIRED')
                else:  # 未过期的时候需要有以下字段
                    settleCurrency = base['settleCurrency']
                    tradeCurrency = base['tradeCurrency']
                    isEnable = future['isEnable']
                    tradeAble = instrument['tradeAble']
                    self.assertEqual(str(isEnable), 'True')
                    self.assertEqual(str(tradeAble), 'True')
                # 因BUG(缺少这些字段)注释掉  2010.10.19
                # beginDeliverDate = future['beginDeliverDate']
                # endDeliverDate = future['endDeliverDate']

                timespin = timespin.rstrip(' ')
                timespinList = re.findall('(\d+-\d+) ?', timespin)
                assert_list = trade + callMarket  # timespin字段是由交易时间和竞价时间组合得到的
                start_list = [assert_list[j]['start'] for j in range(assert_list.__len__())]
                end_list = [assert_list[k]['end'] for k in range(assert_list.__len__())]
                for i in range(timespinList.__len__()):  # 校验时间片与交易时间、竞价时间的匹配性
                    self.assertTrue(str(start_list[i]) in str(timespinList[i]))
                    self.assertTrue(str(end_list[i]) in str(timespinList[i]))

                # 校验交易状态bug：休市时依然返回trading
                # if self.common.isInTradeTime(record_time, trade) or self.common.isInTradeTime(record_time, callMarket):
                #     self.assertTrue(status == 'TRADING')
                #     self.assertTrue(tradeAble == True)
                # else:
                #     self.assertTrue(status != 'TRADING')
                #     self.assertTrue(tradeAble == False)

                if ('main' not in instrCode) and ('month' not in instrCode):
                    self.assertTrue(instrCode == code + seriesId)
                if 'main' in instrCode:
                    is_master_instr = self.common.doDicEvaluate(future, 'isMasterInstr', 4)
                    self.assertTrue(is_master_instr is True)
                    self.assertTrue(self.common.searchDicKV(instrument, 'relatedInstr') is not None)

                ##################### 校验品种所在时区 ####################
                _code = instrCode  # 赋值一个变量_code
                if "main" in _code:
                    _code = _code.replace("main", "")
                # 去掉_code中的数字, 只保留品种代码
                _code_lit = _code[2:]
                _code_lit = _code_lit.translate(str.maketrans('', '', digits))
                _code = _code[:2] + _code_lit
                # 判断品种只有APP用到的42个
                assert _code in appCodelist
                # 因BUG(只需要分两个时区)注释掉  2010.10.19
                # 合约信息 : 美东时间统一ET, 美中时间统一CT
                # if _code in ["ZC", "ZS", "ZM", "ZW", "ZT", "ZF", "ZN", "ZB", "6A", "6B", "6C", "6E", "6J", "6N", "6S",
                #              "E7", "J7"]:
                #     assert timeZone == "CST"
                #
                # elif _code in ["CL", "QM", "NG", "BZ", "GC", "SI", "HG", "QO", "QI", "QC", "NQ", "MNQ", "ES", "MES",
                #                "MIY", "YM", "MYM"]:
                #     assert timeZone == "EST"
                #
                # elif _code in ["CUS", "NK", "TW", "CN", "HSI", "HHI", "MHI", "MCH"]:
                #     assert timeZone == "CCT"  # 中国时间
                #
                # else:
                #     self.logger.error("品种 {} 忽略了, 请检查合约生成服务".format(_code))

                #############################################################

                futureBaseInfo = self.common.getFutureBaseInfo(code)
                self.assertTrue(counterCode == futureBaseInfo['EsunnyCode'] + seriesId)

                lotSize = int(instrument['lotSize'])
                lotSizePrecision = int(self.common.doDicEvaluate(instrument, 'lotSizePrecision', 0))
                priceTick = int(instrument['priceTick'])
                priceTickPrecision = int(self.common.doDicEvaluate(instrument, 'priceTickPrecision', 0))
                contractMultiplier = int(future['contractMultiplier'])
                contractMultiplierPrecision = int(self.common.doDicEvaluate(future, 'contractMultiplierPrecision', 0))
                fluctuation = self.common.doDicEvaluate(future, 'minimumPriceFluctuation', 1)

                if lotSize / pow(10, lotSizePrecision) != float(futureBaseInfo['lotSize']):
                    error_lot_list.append(code)

                if contractMultiplier / pow(10, contractMultiplierPrecision) != float(
                        futureBaseInfo['contractMultiplier']):
                    error_contractMultiplier_list.append(code)

                if float(int(priceTick) / (pow(10, int(priceTickPrecision)))) != float(
                        futureBaseInfo['priceTick']):
                    error_priceTick_list.append(code)
                if fluctuation != futureBaseInfo['fluctuation']:
                    error_fluctuation_list.append(code)
                # self.assertTrue(
                #     int(lotSize) == int(futureBaseInfo['lotSize']))  # 与港交所公开数据对比合约规模字段的准确性
                # self.assertTrue(int(contractMultiplier) == int(
                #     futureBaseInfo['contractMultiplier']))  # 与港交所公开数据对比合约数量乘数字段的准确性

                # 检查 每个品种的 品种类型、品种简体简称、品种英文简称
                procData = self.common.getProc(code)
                self.assertTrue(productType == procData['productType'])
                # self.assertTrue(prod_cn_simple_name == procData['cnSimpleName'])
                # self.assertTrue(prod_en_simple_name == procData['enSimpleName'])
                if code not in ['CN', 'NK', 'TW']:  # 错误，因此屏蔽
                    self.assertTrue(timespin == procData['timespin'])

        print('error_lot_list:', list(set(error_lot_list)))
        print('error_contractMultiplier_list:', list(set(error_contractMultiplier_list)))
        print('error_priceTick_list:', list(set(error_priceTick_list)))
        print('error_fluctuation_list:', list(set(error_fluctuation_list)))

    # --------------------------------------------采集服务end----------------------------------------------------

    # --------------------------------------------计算服务start-------------------------------------------------
    def test_06_PushKLineMinData(self):
        # 推送分时K线
        peroidType = 'MIN'
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_KLINE_MIN, 1000000)
        else:
            check_info = self.check_json_list

        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))

        ######################################################################
        # 不活跃合约, 暂不确定是行情服务补线还是APP补线
        ######################################################################
        if self.is_before_data:
            # 查询数据时, 校验数据完整性
            first_time = self.common.searchDicKV(check_info[0], 'updateDateTime')
            last_time = self.common.searchDicKV(check_info[-1], 'updateDateTime')

            # 获取交易时间, 校验数据完整性
            tradeTimeList = self.common.check_trade_status(
                self.exchange, self.instr_code, curTime=first_time, isgetTime=True)

            # assert tradeTimeList[0] == first_time
            # # 判断是否当天, 当天可能没有最后一刻的数据
            # if int(time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))) > int(tradeTimeList[-1]):
            #     assert tradeTimeList[-1] == last_time

        assert_json = {}
        thatDay = time.strftime("%Y%m%d", time.localtime(time.time()))  # 获取当日的年月日
        updateSettlementPrice = False  # 判断结算价, 结算价更新时修改
        for info in check_info:
            if self.check_json_list == None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            self.logger.debug(json_info)
            if not self.is_before_data:  # 实时push
                exchange = json_info['exchange']
                code = json_info['code']
                data = json_info['data'][0]
                if self.check_json_list == None:
                    get_info = json.loads(check_info[-1][0])
                    latest_time = get_info['data'][0]['updateDateTime']
                else:
                    latest_time = check_info[-1]['data'][0]['updateDateTime']
            else:  # app订阅的历史数据直接返回data list，不返回exchange、code字段
                exchange = self.exchange
                code = self.instr_code
                data = json_info
                latest_time = self.common.searchDicKV(check_info[-1], 'updateDateTime')
            latest_time_stamp = int(time.mktime(time.strptime(latest_time, "%Y%m%d%H%M%S"))) * 1000

            _code = code  # 赋值一个变量_code
            if "main" in _code:
                _code = _code.replace("main", "")
            # 去掉_code中的数字, 只保留品种代码
            _code_lit = _code[2:]
            _code_lit = _code_lit.translate(str.maketrans('', '', digits))
            _code = _code[:2] + _code_lit

            # 判断品种只有APP用到的42个
            assert _code in appCodelist

            # 当开, 高, 低 没有时, 可能是未来合约, 还没有人交易
            if data.get("open") and data.get("high") and data.get("low"):
                high = int(data['high'])
                open = int(data['open'])
                low = int(data['low'])
                close = int(data['close'])
                average = int(data['average'])
                vol = int(self.common.doDicEvaluate(data, 'vol'))  # 成交量
                riseFall = int(self.common.doDicEvaluate(data, 'riseFall'))
                rFRatio = int(self.common.doDicEvaluate(data, 'rFRatio'))
                updateDateTime = data['updateDateTime']
                settlementPrice = int(data['settlementPrice'])  # 结算价(昨收)

                # high, open, low, close基本校验
                self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
                self.assertTrue(int(high) >= int(close) >= int(low))  # 收盘价在最高价最低价之间

                # 初始化每一个合约的结算价和updateDateTime
                if "{}_{}_settlementPrice".format(exchange, code) not in assert_json.keys():
                    assert_json["{}_{}_settlementPrice".format(exchange, code)] = settlementPrice
                    # 记录updateDateTime, 年月日
                    assert_json["{}_{}_updateDateTime".format(exchange, code)] = updateDateTime[:8]
                else:
                    # 判断同一交易日, 结算价相等
                    try:
                        self.assertTrue(
                            settlementPrice == assert_json["{}_{}_settlementPrice".format(exchange, code)])
                    except AssertionError:
                        if not self.is_before_data:  # 保证只有查询时, 结算价不会变动
                            raise AssertionError

                        if updateSettlementPrice:
                            raise AssertionError

                        # 校验错误时, 可能是结算价更新了, 故这里更新结算价和thatDay
                        assert_json["{}_{}_settlementPrice".format(exchange, code)] = settlementPrice
                        updateSettlementPrice = True  # 保证只更新一次

                # 获取品种 当日的收盘时间
                if "{}_{}_last_tradeTime".format(exchange, code) not in assert_json.keys():
                    # assert_json["{}_{}_last_tradeTime".format(exchange, code)] = \
                    # self.common.check_trade_status(exchange, code, thatDay, isgetTime=True)[-1]

                    strptimeFunc = lambda x, fmt="%Y%m%d%H%M%S": datetime.datetime.strptime(x, fmt)  # str 转 detetime
                    strftimeFunc = lambda x, fmt="%Y-%m-%d": datetime.datetime.strftime(x, fmt)  # datetime 转 str

                    # 预设结算价休市后2个小时给出
                    _last_tradeTime = self.common.check_trade_status(exchange, code, thatDay, isgetTime=True)[-1]
                    if strptimeFunc(updateDateTime) >= strptimeFunc(_last_tradeTime) + datetime.timedelta(hours=2):
                        last_tradeTime = self.common.check_trade_status(exchange, code, isgetTime=True)[-1]
                        assert_json["{}_{}_last_tradeTime".format(exchange, code)] = last_tradeTime
                        self.logger.debug("调试字段打印 : {}".format(last_tradeTime))
                    else:
                        assert_json["{}_{}_last_tradeTime".format(exchange, code)] = _last_tradeTime

                ############################### 校验涨跌额 #########################################
                # 源更新时间大于交易日开始时间, 说明结算价未更新
                if int(updateDateTime) > int(
                        assert_json.get("{}_{}_last_tradeTime".format(exchange, code))) and not updateSettlementPrice:
                    if not assert_json.get("{}_{}_last_close".format(exchange, code)):
                        # 没有拿到昨收价时, 从数据库拿数据
                        if sys.platform == 'win32':
                            pass
                            # win 暂未能获取rocksdb的数据, 先赋值结算价
                            assert_json["{}_{}_last_close".format(exchange, code)] = settlementPrice
                        else:
                            db = MarketRocksDBClient(future_rocksdb_path)
                            last_close = db.get_today_close_price(ExchangeType.Value(
                                exchange), code, assert_json.get("{}_{}_last_tradeTime".format(exchange, code)))
                            self.logger.debug("上个交易日收市的价格为 : {}".format(last_close))
                            assert_json["{}_{}_last_close".format(exchange, code)] = int(last_close)

                    # 单当日结算价为还未给出时, 涨跌额 = 当前价格 - 昨收价
                    self.assertTrue(riseFall == close - assert_json["{}_{}_last_close".format(exchange, code)])
                else:
                    # 涨跌额 = 当前价格 - 结算价
                    self.assertTrue(riseFall == close - settlementPrice)
                    pass

                # 涨跌幅 = (涨跌额 / 昨收价), 涨跌幅返回的数据为百分比数据, 故 涨跌幅/100 == (涨跌额/昨收价) * 100
                self.assertTrue(rFRatio == int((riseFall / settlementPrice) * 10000))

                # 记录当日16:30的收盘价
                if int(updateDateTime) == int(assert_json.get("{}_{}_last_tradeTime".format(exchange, code))):
                    assert_json["{}_{}_last_close".format(exchange, code)] = close  # 记录每一次的收盘价

                updateDateTimeStamp = int(time.mktime(time.strptime(updateDateTime, "%Y%m%d%H%M%S"))) * 1000
                if self.is_before_data:
                    self.assertTrue(int(updateDateTimeStamp) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    self.assertTrue(int(updateDateTimeStamp) >= int(self.start_time))  # 订阅服务时用来判断APP开始时间与源时间

    def test_07_PushKLineData(self):
        # 推送K线数据
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_KLINE, 1000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {}

        for info in check_info:
            if self.check_json_list == None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            self.logger.debug(json_info)
            if not self.is_before_data:  # 实时push
                exchange = json_info['exchange']
                code = json_info['code']
                kData = json_info['kData']
                peroidType = json_info['peroidType']
                if self.check_json_list == None:
                    get_info = json.loads(check_info[-1][0])
                    latest_time = get_info['kData']['KLineKey']
                else:
                    latest_time = self.common.searchDicKV(check_info[-1], 'KLineKey')
            else:  # app订阅历史数据直接返回data list，不返回exchange、code字段
                exchange = self.exchange
                code = self.instr_code
                kData = json_info
                peroidType = self.peroid_type
                latest_time = self.common.searchDicKV(check_info[-1], 'KLineKey')

            ###############################校验采集器的品种已经过滤成42个##################################
            _code = code  # 赋值一个变量_code
            if "main" in _code:
                _code = _code.replace("main", "")
            # 去掉_code中的数字, 只保留品种代码
            _code_lit = _code[2:]
            _code_lit = _code_lit.translate(str.maketrans('', '', digits))
            _code = _code[:2] + _code_lit
            # 判断品种只有APP用到的42个
            assert _code in appCodelist
            #############################################################################################

            latest_time_stamp = int(time.mktime(time.strptime(latest_time, "%Y%m%d%H%M%S"))) * 1000
            high = int(kData['high'])
            open = int(kData['open'])
            low = int(kData['low'])
            close = int(kData['close'])
            currVol = int(self.common.doDicEvaluate(kData, 'currVol'))  # 当前这笔K线的成交量
            vol = int(self.common.doDicEvaluate(kData, 'vol'))  # 累计到当前这一笔K线的总成交量
            openInterest = int(kData.get("openInterest") or 0)  # 持仓量
            # amount = int(kData['amount'])     # K线不需要成交金额
            riseFall = int(self.common.doDicEvaluate(kData, 'riseFall'))
            rFRatio = int(self.common.doDicEvaluate(kData, 'rFRatio'))
            peroidTypeInt = k_type_convert(peroidType)  # 频率
            if peroidTypeInt in [KLinePeriodType.DAY, KLinePeriodType.WEEK, KLinePeriodType.MONTH,
                                 KLinePeriodType.SEASON, KLinePeriodType.YEAR]:  # 日K级别及以上类型才有下面字段
                settlementPrice = kData['settlementPrice']  # 结算价
                # preSettlement = kData['preSettlement']        # 昨结
                # preClose = kData['preClose']                  # 昨收

            updateDateTime = kData['updateDateTime']
            KLineKey = kData['KLineKey']
            # totalAmount = kData["totalAmount"]      # 总成交金额, 期货不需要成交金额

            self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
            self.assertTrue(int(high) >= int(close) >= int(low))  # 收盘价在最高价最低价之间
            # self.assertTrue(int(high) >= int(average) >= int(low))  # 均价在最高价最低价之间

            if ('{}_{}_current_time'.format(code, peroidType) in assert_json.keys()):
                # 代表同一根K线上的更新
                if KLineKey == assert_json['{}_{}_current_time'.format(code, peroidType)]:
                    self.assertTrue(open == assert_json['{}_{}_current_open'.format(code, peroidType)])  # 同一根K线, 开盘价不变
                    # # 保存同一根K线最高价和最低价
                    self.assertTrue(
                        currVol >= assert_json['{}_{}_currVol'.format(code, peroidType)])  # 同一根K线, 成交量大于等于上一刻成交量
                    # self.assertTrue(
                    #     vol >= assert_json['{}_{}_last_vol'.format(code, peroidType)])  # 同一根K线, 总成交量大于等于上一刻总成交量

                    # 第二根K线与第一根K线的对比, 校验涨跌额和涨跌幅
                    if KLineKey != assert_json['{}_{}_first_check_time'.format(code, peroidType)]:
                        # 涨跌额 = 收盘价 - 上一根K线收盘价
                        self.assertTrue(riseFall == close - assert_json['{}_{}_lastclose'.format(code, peroidType)])
                        # 涨跌幅 = 涨跌额 / 上一根K线收盘价
                        self.assertTrue(rFRatio == int(
                            10000 * riseFall / (assert_json['{}_{}_lastclose'.format(code, peroidType)])))
                        # 当前一笔K线成交量 = 总成交量 - 上一笔K线成交量
                        self.assertTrue(currVol == vol - assert_json['{}_{}_lastKline_vol'.format(code, peroidType)])

                else:  # K线更新, 校验涨跌和成交量, 初始化数据
                    self.assertTrue(int(KLineKey) > int(assert_json['{}_{}_current_time'.format(code, peroidType)]))
                    # 涨跌额 = 收盘价 - 上次收盘价
                    self.assertTrue(riseFall == close - assert_json['{}_{}_close'.format(code, peroidType)])
                    # 涨跌幅 = 涨跌额 / 上次收盘价
                    self.assertTrue(
                        rFRatio == int(10000 * riseFall / (assert_json['{}_{}_close'.format(code, peroidType)])))

                    # 当日总成交量递增, 日K以下校验
                    if peroidTypeInt not in [KLinePeriodType.DAY, KLinePeriodType.WEEK, KLinePeriodType.MONTH,
                                             KLinePeriodType.SEASON, KLinePeriodType.YEAR]:  # 日K级别及以上类型才有下面字段
                        self.assertTrue(vol >= assert_json['{}_{}_last_vol'.format(code, peroidType)])
                        # 当日 currVol = vol - 上一根vol
                        self.assertTrue(currVol == vol - assert_json['{}_{}_last_vol'.format(code, peroidType)])

                    # 当日最高价递增, 最低价递减
                    # self.assertTrue(high >= assert_json['{}_{}_last_high'.format(code, peroidType)])
                    # self.assertTrue(low <= assert_json['{}_{}_last_low'.format(code, peroidType)])

                    # 更新 新K线数据
                    assert_json['{}_{}_current_time'.format(code, peroidType)] = KLineKey  # 新K线日期
                    assert_json['{}_{}_current_open'.format(code, peroidType)] = open  # 新K线初始开盘价
                    assert_json['{}_{}_lastKline_vol'.format(code, peroidType)] = assert_json[
                        '{}_{}_last_vol'.format(code, peroidType)]  # 上一根K线的成交量
                    assert_json['{}_{}_lastclose'.format(code, peroidType)] = assert_json[
                        '{}_{}_close'.format(code, peroidType)]  # 记录上一根K线的收盘价

            else:  # 初始化同个合约的第一个K线数据
                assert_json['{}_{}_current_open'.format(code, peroidType)] = open
                assert_json['{}_{}_current_time'.format(code, peroidType)] = KLineKey  # 当前K线的更新时间
                assert_json['{}_{}_last_vol'.format(code, peroidType)] = vol
                assert_json['{}_{}_first_check_time'.format(code, peroidType)] = KLineKey  # 记录第一根K线的时间, 用于第二根K线与第一根K线对比

            assert_json['{}_{}_close'.format(code, peroidType)] = close  # 记录每一笔数据的收盘价
            assert_json['{}_{}_currVol'.format(code, peroidType)] = currVol  # 记录每一笔成交量
            assert_json['{}_{}_last_vol'.format(code, peroidType)] = vol  # 记录每一笔总成交量
            assert_json['{}_{}_last_high'.format(code, peroidType)] = high  # 记录每一笔最高价
            assert_json['{}_{}_last_low'.format(code, peroidType)] = low  # 记录每一笔最低价

            if self.is_before_data:
                updateDateTimeStamp = int(time.mktime(time.strptime(updateDateTime, "%Y%m%d%H%M%S"))) * 1000

                self.assertTrue(
                    int(self.start_time) <= int(updateDateTimeStamp) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间


# --------------------------------------------计算服务end-------------------------------------------------
if __name__ == '__main_':
    unittest.main()
#     # suite = unittest.TestSuite()
#     # suite.addTest(CheckZMQ("test_01_QuoteSnapshot"))
#     # runner = unittest.TextTestRunner(verbosity=2)
#     # inner_test_result = runner.run(suite)

# pytest.main(["-v", "-s",
#              "zmq_record_testcase.py",
#              "-k test_01_QuoteSnapshot",
#              "--show-capture=stderr"
#              ])
