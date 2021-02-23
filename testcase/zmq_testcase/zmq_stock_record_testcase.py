# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/9/1
# @Software: PyCharm
import datetime
import re
import unittest
from decimal import Decimal

import math
# from curses.ascii import isalpha, isdigit

# from py_rocksdb.market import MarketRocksDBClient
from py_sqlite.market import *
from common.test_log.ed_log import get_log
from common.pb_method import k_type_convert, exchange_convert
from common.common_method import Common
from pb_files.common_type_def_pb2 import *


class CheckZMQ(unittest.TestCase):
    def __init__(self, methodName='runTest', check_json_list=None, is_before_data=False, sub_time=None, start_time=None,
                 instr_code=None, exchange=None, peroid_type=None, is_delay=False):
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
        self.is_delay = is_delay

    @classmethod
    def setUpClass(cls):
        cls.sq = MarketSqliteDBClient()
        cls.common = Common()

    @classmethod
    def tearDownClass(cls):
        cls.sq.exit()

    def test_stock_01_01_QuoteSnapshot(self):  # dealer模式下请求返回的静态数据
        check_info = self.sq.get_deal_json_records(QuoteMsgType.SNAPSHOT_RSP, 100000)
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            record_time = info[1]
            json_info = json.loads(info[0])
            retResult = json_info['retResult']
            retCode = retResult['retCode']
            self.assertTrue(retCode == 'SUCCESS')  # 校验接口返回状态
            dealer_snap_shot_list = json_info['snapshotInfos']
            self.test_stock_01_QuoteSnapshot(dealer_snap_shot_list, record_time)

    def test_stock_01_QuoteSnapshot(self, dealer_snap_shot_list=None, dealer_record_time=None):  # 股票-快照
        if dealer_snap_shot_list == None:
            if self.check_json_list is None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_SNAPSHOT, 100000)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_snap_shot_list

        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {'instrCodeList': []}
        # check_info = [json.loads(i[0]) for i in check_info]
        preclose_list = []
        callputType_list = []
        riseFall_list = []
        rFRatio_list = []
        leverageRatio_list = []
        conversion_price_list = []
        conversion_ratio_list = []
        amplitude_list = []
        last_list = []
        premium_list = []
        distance_upper_price_list = []
        distance_lower_price_list = []
        potential_profit_list = []
        potential_loss_list = []
        dist_call_price_list = []
        dist_decimal_price_list = []
        outstanding_list = []
        high_open_low_list = []
        sourceUpdateTime_List = []
        collectorRecvTime_list = []
        collectorSendTime_list = []
        data_type_list = []
        strikeprice_list = []
        sourceUTime_subTime_list = []
        index_List = []

        for info in check_info:
            if dealer_snap_shot_list == None:
                if self.check_json_list is None:
                    record_time = info[1]
                    json_info = json.loads(info[0])
                else:
                    record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                    json_info = info
            else:
                record_time = dealer_record_time
                json_info = info

            self.logger.debug(json_info)
            # ---------------校验快照数据中的行情头 --------------------------
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            productCode = commonInfo['productCode']
            instrCode = commonInfo['instrCode']
            # 检查是否如期过滤掉了上证指数
            if instrCode in ['000016', '000021', '000010', '000009', '000066', '000001', '000015', '000043', '000044',
                             '000065']:
                index_List.append(instrCode)

            precision = self.common.doDicEvaluate(commonInfo, 'precision')
            if 'collectorRecvTime' in commonInfo:
                collectorRecvTime = commonInfo['collectorRecvTime']    #BUG: 没有返回数据, HQZX-410
            else:
                collectorRecvTime_list.append(instrCode)

            if 'collectorSendTime' in commonInfo:
                collectorSendTime = commonInfo['collectorSendTime']    #BUG: 没有返回数据
            else:
                collectorSendTime_list.append(instrCode)
            # self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            if self.check_json_list is not None:
                publisherRecvTime = commonInfo['publisherRecvTime']
                publisherSendTime = commonInfo['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间

            # ----------------校验行情-快照中的数据 --------------------------
            if 'last' in json_info:
                last = int(json_info['last'])     # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-452
            else:
                last_list.append(instrCode)

            if "open" in json_info.keys() and "high" in json_info.keys() and "low" in json_info.keys():
                open = int(json_info['open'])
                high = int(json_info['high'])
                low = int(json_info['low'])
                volume = int(json_info.get("volume") or 0)
                turnover = int((json_info.get("turnover") or 0))
                if int(high) >= int(open) >= int(low):
                    pass
                else:
                    high_open_low_list.append(instrCode)
                # self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
                # self.assertTrue(int(high) >= int(last) >= int(low))  # BUG: low > last, http://jira.eddid.com.cn:18080/browse/HQZX-641

            average = int(json_info.get("average") or 0)   # 当日均价
            riseFall = int(json_info.get("riseFall") or 0)
            rFRatio = int(json_info.get("rFRatio") or 0)
            sourceUpdateTime = int(json_info['sourceUpdateTime'])

            if "dataType" in json_info:
                data_type = json_info["dataType"]
            else:
                data_type_list.append(instrCode)
                continue
            preclose = ''
            if data_type == 'EX_TRST':                                   # 信托产品
                trst = json_info['trst']                # BUG : http://jira.eddid.com.cn:18080/browse/HQZX-447
                if "preclose" in trst:
                    preclose = trst["preclose"]                             # 昨收价
                else:
                    preclose_list.append(instrCode)
                # 因BUG 临时注释
                #amplitude = trst.get("amplitude")                       # 振幅
                committee = trst.get("committee")                       # 委比
                # quantity_ratio = trst["quantityRatio"]                  # 量比, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-416
                # turnover_rate = trst["turnoverRate"]                    # 换手率, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-416
                dividend_ttm = trst.get("dividendTtm")                  # 股息(TTM]
                dividend_ratio_ttm = trst.get("dividendRatioTtm")       # 股息率(TTM]
                # highest52weeks_price = trst["highest52weeksPrice"]      # 52周最高   BUG: http://jira.eddid.com.cn:18080/browse/HQZX-416
                # lowest52weeks_price = trst["lowest52weeksPrice"]        # 52周最低
                # ey_ratio = trst["eyRatio"]                              # 收益率
                # net_asset = trst["netAsset"]                            # 资产净值
                # release_day = trst["releaseDay"]                        # 发布日期
                # expense_price = trst["expensePrice"]                    # 费用比率
                # currency = trst["tradeCurrency"]                        # 交易币种

                # ----------------------------------------------------------------------
                # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
                # assert int(amplitude) == (high - low) / int(preclose)

            elif data_type == 'EX_STOCK':                                     # 股票
                stock = json_info['stock']
                if "preclose" in stock:
                    preclose = stock["preclose"]                              # 昨收价, BUG: http://jira.eddid.com.cn:18080/browse/HQZX-415
                else:
                    preclose_list.append(instrCode)
                amplitude = stock.get("amplitude")                         # 振幅
                committee = stock.get("committee")                             # 委比
                quantity_ratio = stock.get("quantityRatio")                 # 量比
                total_market_val = stock.get("totalMarketVal")              # 总市值
                circular_market_val = stock.get("circularMarketVal")        # 市值
                turnover_rate = stock.get("turnoverRate")                   # 换手率
                pe_ratio = stock.get("peRatio")                             # 静态市盈率
                pe_ttm_ratio = stock.get('peTtmRatio')                      # 滚动市盈率
                pb_ratio = stock.get('pbRatio')                             # 市净率
                dividend_ttm = stock.get('dividendTtm')                     # 股息TTM
                dividend_lfy = stock.get('dividendLfy')                     # 股息LFY
                dividend_ratio_ttm = stock.get("dividendRatioTtm")          # 股息率TTM
                dividend_ratio_lfy = stock.get("dividendRatioLfy")          # 股息率LFY
                highest52weeks_price = stock.get("highest52weeksPrice")     # 52周最高
                lowest52weeks_price = stock.get("lowest52weeksPrice")       # 52周最高

                # ----------------------------------------------------------------------
                # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
                # assert int(amplitude) == (high - low) / int(preclose)

            elif data_type == 'EX_INDEX':     # 指数 # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-585
                index = json_info['index']
                # indexstatus = index['indexstatus']      # 指数状态
                if 'preclose' in index:
                    preclose = index['preclose']            # 昨收价
                else:
                    preclose_list.append(instrCode)
                # easvalue = index['easvalue']            # 预估结算值
                if 'amplitude' in index:
                    amplitude = index['amplitude']          # 振幅
                else:
                    amplitude_list.append(instrCode)
                # highest52weeks_price = index['highest52weeksPrice']     # 52周最高
                # lowest52weeks_price = index['lowest52weeksPrice']       # 52周最低
                # advance = index['advance']                          # 上涨家数
                # decline = index['decline']                          # 下跌家数
                # flat_flate = index['flatFlate']                     # 平盘家数

                # ----------------------------------------------------------------------
                # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
                if 'preclose' in index:
                    if amplitude and int(amplitude) != (high - low) / int(preclose):
                        amplitude_list.append(instrCode)
                # assert int(amplitude) == (high - low) / int(preclose)

            elif data_type == 'EX_WARRANT':     # 权证
                warrant = json_info['warrant']
                if 'preclose' in warrant:
                    preclose = warrant['preclose']          # 昨收价
                else:
                    preclose_list.append(instrCode)
                if 'strikeprice' in warrant:
                    strikeprice = warrant['strikeprice']                    # 行使价, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446
                else:
                    strikeprice_list.append(instrCode)
                # premium = warrant["premium"]                         # 溢价, BUG:富途有数据
                # leverage_ratio = warrant['leverageRatio']               # 杠杆比率, BUG:个别合约没有数据
                # make_point = warrant["makePoint"]                   # 打和点, BUG: http://jira.eddid.com.cn:18080/browse/HQZX-446
                # effective_leverage = warrant['effectiveLeverage']       # 有效杠杆, BUG: 个别合约没有数据
                if 'conversionPrice' in warrant:
                    conversion_price = warrant['conversionPrice']           # 换股价, BUG:富途有数据
                else:
                    conversion_price_list.append(instrCode)
                if 'callputType' in warrant:
                    callput = warrant['callputType']                        # 认购认沽标识, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446
                else:
                    callputType_list.append(instrCode)
                # maturity_date = warrant['maturityDate']                 # 到期日, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446
                if 'conversionRatio' in warrant:
                    conversion_ratio = warrant['conversionRatio']           # 换股比率, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446
                else:
                    conversion_ratio_list.append(instrCode)
                outstanding_quantity = warrant.get("outstandingQuantity")   # 街货量
                outstanding_ratio = warrant.get("outstandingRatio")         # 接货比
                if not outstanding_quantity:
                    # 街货量和接货比同时为空
                    if outstanding_quantity != outstanding_ratio:
                        outstanding_list.append(instrCode)
                    # assert outstanding_quantity == outstanding_ratio    # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-446
                    pass

                implied_volatility = warrant.get("impliedVolatility")       # 引申波幅, 快照实时更新
                hedge_value = warrant.get("hedgeValue")                     # 对冲值, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446
                warrentType = warrant.get("warrentType")                    # 涡轮类型， BUG:http://jira.eddid.com.cn:18080/browse/HQZX-446

            elif data_type == 'EX_CBBC':
                cbbc = json_info['cbbc']
                preclose = cbbc.get("preclose") or 0
                if not preclose:
                    preclose_list.append(instrCode)
                strikeprice = cbbc['strikeprice']                   # 行使价, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                # premium = cbbc['premium']                           # 溢价, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                if 'leverageRatio' not in cbbc:
                    leverageRatio_list.append(instrCode)
                else:
                    leverage_ratio = cbbc['leverageRatio']              # 杠杆比率, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                # make_point = cbbc['makePoint']                      # 打和点, BUG: http://jira.eddid.com.cn:18080/browse/HQZX-445
                if 'distCallPrice' in cbbc:
                    dist_call_price = cbbc['distCallPrice']             # 距回收价, BUG: 富途有数据
                else:
                    dist_call_price_list.append(instrCode)

                if 'distDecimalPrice' in cbbc:
                    dist_decimal_price = cbbc['distDecimalPrice']       # 距回收价小数位
                else:
                    dist_decimal_price_list.append(instrCode)

                # conversion_price = cbbc['conversionPrice']          # 换股价, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                callput = cbbc.get("callputType")                       # 认购认沽标识
                # maturity_date = cbbc['maturityDate']                # 到期日, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                if 'conversionRatio' in cbbc:
                    conversion_ratio = cbbc['conversionRatio']          # 换股比率, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                else:
                    conversion_ratio_list.append(instrCode)
                # outstanding_quantity = cbbc['outstandingQuantity']  # 街货量, 个别合约没有数据
                # outstanding_ratio = cbbc['outstandingRatio']        # 街货比, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                # in_out_price = cbbc['inOutPrice']                   # 价内/价外, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445
                # last_tradedate = cbbc['lastTradedate']              # 最后交易日, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-445

            elif data_type == 'EX_INNER':
                inner = json_info['inner']
                if 'preclose' in inner:
                    preclose = inner["preclose"]
                else:
                    preclose_list.append(instrCode)

                if 'premium' in inner:
                    premium = inner['premium']                              # 溢价, BUG: 富途有数据
                else:
                    premium_list.append(instrCode)
                if 'leverageRatio' in inner:
                    leverage_ratio = inner['leverageRatio']                 # 杠杆比率
                else:
                    leverageRatio_list.append(instrCode)
                # conversion_ratio = inner['conversionRatio']             # 换股比率, BUG:富途有数据
                # outstanding_quantity = inner.get("outstandingQuantity")     # 街货量
                # outstanding_ratio = inner['outstandingRatio']           # 接货比, BUG: 富途有数据
                # effective_leverage = inner['effectiveLeverage']         # 有效杠杆, BUG: 富途有数据
                # implied_volatility = inner.get("impliedVolatility")         # 引申波幅, BUG: 富途有数据
                # hedge_value = inner['hedgeValue']                       # 对冲, BUG: 富途有数据
                # in_out_ner = inner['inOutNer']                          # 界内/界外
                # upper_price = inner['upperPrice']                       # 上限价
                # lower_price = inner['lowerPrice']                       # 下限价
                if 'distanceUpperPrice' in inner:
                    distance_upper_price = inner['distanceUpperPrice']      # 距上限, BUG: 富途有数据
                else:
                    distance_upper_price_list.append(instrCode)

                if 'distanceLowerPrice' in inner:
                    distance_lower_price = inner['distanceLowerPrice']      # 距下限, BUG: 富途有数据
                else:
                    distance_lower_price_list.append(instrCode)

                if 'potentialProfit' in inner:
                    potential_profit = inner['potentialProfit']             # 潜在回报
                else:
                    potential_profit_list.append(instrCode)

                if 'potentialLoss' in inner:
                    potential_loss = inner['potentialLoss']                 # 潜在亏损
                else:
                    potential_loss_list.append(instrCode)

                # assert leverage_ratio == 1/last     # 界内证,杠杆比率=1/最新价

            else:
                self.logger.error("品种代码未定义, 请检查数据")
                raise ValueError



            # ------------------校验涨/跌额涨跌幅 ----------------------
            if preclose:
                if riseFall != last - int(preclose):
                    riseFall_list.append(instrCode)
                if rFRatio != int(self.common.new_round((riseFall / int(preclose)) * 10000)):
                    rFRatio_list.append(instrCode)

                # assert riseFall == last - int(preclose)     # BUG
                # assert rFRatio == int(self.common.new_round((riseFall / int(preclose)) * 10000))     # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-524


            # self.assertTrue(self.common.ibbsTimeInToday(sourceUpdateTime))  # 判断更新时间为当天的数据
            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                sourceUTime = int(sourceUpdateTime) / (pow(10, 6)) + 8000
                if self.is_delay is True:  # 延时行情
                    sourceUTime = sourceUTime + 15*60*1000 + 8000

                if not self.is_before_data:  # 实时数据
                    ###################
                    # 回放数据时, sourceUpdateTime 小于 订阅时间
                    ###################
                    if sourceUTime < int(self.sub_time):# 订阅服务时用来判断订阅时间与源时间
                        sourceUTime_subTime_list.append(instrCode)

                    # self.assertTrue(sourceUTime >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                # else: 前数据在接收时已经判断过了，此处不再判断
                #     pass
                #     self.assertTrue(sourceUTime <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            # 更新时间有序递增
            if not self.is_before_data:
                # self.logger.info(int(sourceUpdateTime))
                if exchange + '_sourceUpdateTime' in assert_json.keys():
                    if(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime'])):
                        pass
                    else:
                        sourceUpdateTime_List.append(instrCode)
                    # self.assertTrue(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime']))
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
                else:
                    assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
            else:
                pass
        self.logger.debug('快照检查结果 昨收价 缺少preclose_list:{}'.format(preclose_list))
        self.logger.debug('快照检查结果 认购认沽标识 缺少callputType_list:{}'.format(callputType_list))
        self.logger.debug('快照检查结果 涨跌 异常rFRatio_list:{}'.format(rFRatio_list))
        self.logger.debug('快照检查结果 涨跌幅 异常riseFall_list:{}'.format(riseFall_list))
        self.logger.debug('快照检查结果 杠杆比率 异常leverageRatio_list:{}'.format(leverageRatio_list))
        self.logger.debug('快照检查结果 换股价 异常conversion_price_list:{}'.format(conversion_price_list))
        self.logger.debug('快照检查结果 换股比率 异常conversion_ratio_list:{}'.format(conversion_ratio_list))
        self.logger.debug('快照检查结果 振幅 异常amplitude_list:{}'.format(amplitude_list))
        self.logger.debug('快照检查结果 最新价 异常last_list:{}'.format(last_list))
        self.logger.debug('快照检查结果 溢价 异常premium_list:{}'.format(premium_list))

        self.logger.debug('快照检查结果 距上限 异常distance_upper_price_list:{}'.format(distance_upper_price_list))
        self.logger.debug('快照检查结果 距下限 异常distance_lower_price_list:{}'.format(distance_lower_price_list))
        self.logger.debug('快照检查结果 潜在回报 异常potential_profit_list:{}'.format(potential_profit_list))
        self.logger.debug('快照检查结果 潜在亏损 异常potential_loss_list:{}'.format(potential_loss_list))
        self.logger.debug('快照检查结果 距回收价 异常dist_call_price_list:{}'.format(dist_call_price_list))
        self.logger.debug('快照检查结果 距回收价小数位 异常dist_decimal_price_list:{}'.format(dist_decimal_price_list))
        self.logger.debug('快照检查结果 街货量和接货比 不一致outstanding_list:{}'.format(outstanding_list))
        self.logger.debug('快照检查结果 开盘价未在最高价最低价之间 high_open_low_list:{}'.format(high_open_low_list))
        self.logger.debug('快照检查结果 快照未按sourceUpateTime排序 sourceUpdateTime_List:{}'.format(sourceUpdateTime_List))
        self.logger.debug('快照检查结果 缺少数据采集接收到数据的时间戳 collectorRecvTime_list:{}'.format(collectorRecvTime_list))
        self.logger.debug('快照检查结果 数据采集器发送数据的时间戳 collectorSendTime_list:{}'.format(collectorSendTime_list))
        self.logger.debug('快照检查结果 缺少数据结构类型 data_type_list:{}'.format(data_type_list))
        self.logger.debug('快照检查结果 缺少行使价 strikeprice_list:{}'.format(strikeprice_list))
        self.logger.debug('快照检查结果 源时间在订阅时间之前  sourceUTime_subTime_list:{}'.format(sourceUTime_subTime_list))
        self.logger.debug('快照检查结果 异常存在的上证指数  index_List:{}'.format(index_List))

    def test_stock_02_01_QuoteOrderBookData(self):  # dealer模式下请求返回的盘口数据
        check_info = self.sq.get_deal_json_records(QuoteMsgType.ORDERBOOK_RSP, 100)
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            record_time = info[1]
            json_info = json.loads(info[0])
            retResult = json_info['retResult']
            retCode = retResult['retCode']
            self.assertTrue(retCode == 'SUCCESS')  # 校验接口返回状态
            dealer_orderbook_info_list = json_info['orderbookInfos']
            self.test_stock_02_QuoteOrderBookData(dealer_orderbook_info_list, record_time)

    def test_stock_02_QuoteOrderBookData(self, dealer_orderbook_info_list=None, dealer_record_time=None):  # 推送的盘口数据
        if dealer_orderbook_info_list == None:
            if self.check_json_list is None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_ORDER_BOOK, 100000)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_orderbook_info_list

        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {'instrCodeList': []}

        sourceUpdateTime_list = []
        upperAskPrice_list = []
        upperBidPrice_list = []
        askPriceDiff_List = []
        bidPriceDiff_List = []

        for info in check_info:
            if dealer_orderbook_info_list == None:
                if self.check_json_list is None:
                    record_time = info[1]
                    json_info = json.loads(info[0])
                else:
                    record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                    json_info = info
            else:
                record_time = dealer_record_time
                json_info = info

            self.logger.debug(json_info)
            # ----------------行情公共头 ------------------------
            commonInfo = json_info['commonInfo']
            exchange = commonInfo['exchange']
            if exchange in [HK_exchange, NYMEX_exchange, COMEX_exchange, CBOT_exchange, CME_exchange, SGX_exchange]:
                continue
            # productCode = commonInfo['productCode']     # BUG: 没有返回此字段 http://jira.eddid.com.cn:18080/browse/HQZX-425
            instrCode = commonInfo['instrCode']
            # 有些精度为0时，无返回
            precision = self.common.doDicEvaluate(commonInfo, 'precision')
            collectorRecvTime = commonInfo['collectorRecvTime']     # BUG: 没有返回此字段
            collectorSendTime = commonInfo['collectorSendTime']     # BUG: 没有返回此字段
            # if self.check_json_list is not None and (productCode not in ['GIPO']):  # 暗盘没这两个字段
            #     publisherRecvTime = commonInfo['publisherRecvTime']
            #     publisherSendTime = commonInfo['publisherSendTime']
            #     self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间

            orderBook = json_info['orderBook']
            sourceUpdateTime = json_info['sourceUpdateTime']      # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-425
            # self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是今天的数据
            if self.common.isTimeInToday(sourceUpdateTime) is False:
                sourceUpdateTime_list.append(instrCode)
                continue

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))

                if not self.is_before_data:  # 实时数据
                    self.assertTrue(int(sourceUpdateTime) / (pow(10, 6))+1000 >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    pass
                    # if not self.common.check_trade_status(exchange, instrCode):
                    #     self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    # else:
                    #     self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间

                    self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(self.sub_time))

            self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            askVolInData, bidVolInData, upperAskPrice, upperBidPrice = 0, 0, 0, 0
            if 'askVol' in orderBook.keys():
                askVol = int(orderBook['askVol'])
                asksData = orderBook['asksData']
                # self.assertTrue(asksData.__len__() == 10)  # 卖盘10层深度, 不活跃股票没有十挡数据
                priceDiff = 0
                for ask in asksData:
                    if ask != {}:
                        askPrice = int(ask['price'])
                        askVolume = ask.get("volume")
                        askOrderCount = ask.get("orderCount")
                        askVolInData = askVolInData + (int((askVolume or 0)))
                        if upperAskPrice:
                            self.assertTrue(int(askPrice) > int(upperAskPrice))  # 深度价格校验（卖1价格应低于卖2价格）
                            if not priceDiff:
                                priceDiff = int(askPrice) - int(upperAskPrice)
                            else:
                                try:
                                    assert priceDiff == int(askPrice) - int(upperAskPrice)
                                except AssertionError:
                                    askPriceDiff_List.append(instrCode)

                        upperAskPrice = askPrice    # 记录上一个价格

                self.assertEqual(int(askVol), askVolInData)  # 校验卖盘数量和, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-426

            if 'bidVol' in orderBook.keys():
                bidVol = int(orderBook['bidVol'])
                bidsData = orderBook['bidsData']
                # self.assertTrue(bidsData.__len__() == 10)  # 买盘10层深度, 不活跃股票没有十挡数据
                priceDiff = 0
                for bid in bidsData:
                    if bid != {}:
                        bidPrice = int(bid['price'])
                        bidVolume = bid.get("volume")
                        bidOrderCount = bid.get("orderCount")
                        bidVolInData = bidVolInData + int((bidVolume or 0))
                        if upperBidPrice:
                            self.assertTrue(int(bidPrice) < int(upperBidPrice))  # 深度价格校验（买1价格应高于买2价格）
                            if not priceDiff:
                                priceDiff = int(upperBidPrice) - int(bidPrice)
                            else:
                                try:
                                    assert priceDiff == int(upperBidPrice) - int(bidPrice)
                                except AssertionError:
                                    bidPriceDiff_List.append(instrCode)

                        upperBidPrice = bidPrice
                self.assertEqual(int(bidVol), bidVolInData)  # 校验买盘数量和, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-426

        self.logger.debug('盘口数据 检查结果,sourceUpdateTime非今天的合约列表 sourceUpdateTime_list:{}'.format(sourceUpdateTime_list))
        self.logger.debug('盘口数据 检查结果,深度价格校验（卖1价格应低于卖2价格）不通过的合约列表 upperAskPrice_list:{}'.format(upperAskPrice_list))
        self.logger.debug('盘口数据 检查结果,深度价格校验（买1价格应高于买2价格）不通过的合约列表 upperBidPrice_list:{}'.format(upperBidPrice_list))
        self.logger.debug('盘口数据 检查结果,卖盘价差校验 不通过的合约列表 askPriceDiff_List:{}'.format(askPriceDiff_List))
        self.logger.debug('盘口数据 检查结果,买盘价差校验 不通过的合约列表 bidPriceDiff_List:{}'.format(bidPriceDiff_List))


    def test_stock_03_QuoteBasicInfo(self, dealer_basic_info_list=None, dealer_record_time=None):  # 推送的静态数据
        if dealer_basic_info_list == None:
            if self.check_json_list == None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_BASIC, 100)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_basic_info_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))

        sourceUpdateTime_list = []
        lasttradeday_list = []
        releaseday_list = []

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
            self.assertTrue(exchange in ['SEHK', 'ASE', 'NASDAQ', 'NYSE', 'BATS', 'IEX'])

            productCode = commonInfo['productCode']
            # 证券目前填写: "BOND"(债券); "EQTY"(股票); "TRST"(信托产品); "WRNT"(权证); "INDEX"(指数)
            self.assertTrue(productCode in ['BOND', 'EQTY', 'TRST', 'WRNT', 'INDEX', 'GIPO'])

            instrCode = commonInfo['instrCode']

            sourceUpdateTime = int(json_info['updateTimestamp'])
            precision = self.common.doDicEvaluate(commonInfo, 'precision', 0)  # 有些精度为0时，无返回
            if exchange == 'SEHK':  # 港股精确到3位
                self.assertTrue(precision == 3)
            else:  # 美股精确到4位
                self.assertTrue(precision == 4)
            # 因部分数据没这些,暂不检查 2020.11.26
            # collectorRecvTime = commonInfo['collectorRecvTime']
            # collectorSendTime = commonInfo['collectorSendTime']
            # if self.check_json_list != None:
            #     publisherRecvTime = commonInfo['publisherRecvTime']
            #     publisherSendTime = commonInfo['publisherSendTime']
            #     self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间

            # 产品已经确认，这个字段未被使用,2020.11.26
            # if (instrCode not in ['ARYBU', 'ARYBW', 'ARYB']) and (productCode != 'INDEX'):
            #     type = json_info['type']
            #     self.assertTrue(type in ['EQUITY_ORDINARY_SHARES', 'EQUITY_PREFERENCE_SHARES', 'GREY_MARKET',
            #                              'EQUITY_DEPOSITORY_RECEIPT_ORDINARY_SHARES',
            #                              'EQUITY_DEPOSITORY_RECEIPT_PREFERENCE_SHARES', 'EQUITY_RIGHTS',
            #                              'WARRANT_EQUITY_WARRANT', 'WARRANT_DERIVATIVE_WARRANT',
            #                              'WARRANT_EQUITY_LINKED_INSTRUMENT', 'WARRANT_CALLABLE_BULL_BEAR_CONTRACT',
            #                              'BOND_DEBT_SECURITY', 'TRUST_EXCHANGE_TRADED_FUND',
            #                              'TRUST_REAL_ESTATE_INVESTMENT_TRUST', 'TRUST_OTHER_UNIT_TRUSTS',
            #                              'TRUST_LEVERAGED_AND_INVERSE_PRODUCT', 'OTHERS_NONE_OF_THE_ABOVE','EQUITY_US_I',
            #                              'WARRANT_INLINE_WARRANT', 'EQUITY_RIGHTS', 'EQUITY_US_C', 'STOCK_US_FIU',
            #                              'EQUITY_US_A', 'EQUITY_US_B', 'EQUITY_US_O', 'EQUITY_US_N', 'EQUITY_US_T',
            #                              'EQUITY_US_V', 'EQUITY_US_W', 'EQUITY_US_Q'])

            # 因产品已经确认暂未用到，注释掉 2020.11.3
            # tradindDay = json_info['tradindDay']
            # if exchange == 'SEHK' and record_time >= self.common.getTodayHKFEStartStamp():
            #     self.assertTrue(self.common.isTomorrow(tradindDay))
            # elif exchange == 'SEHK' and record_time < self.common.getTodayHKFEStartStamp():
            #     self.assertTrue(self.common.inToday(tradindDay))
            # else:
            #     self.assertTrue(self.common.inToday(tradindDay))  # 观察外期的数据反馈，这里做优化
            # 已经终止交易的不需要判断,因BUG,注释掉
            # if exchange == 'SEHK' and (type not in ['WARRANT_DERIVATIVE_WARRANT', 'WARRANT_INLINE_WARRANT']) and (instrCode not in ['52929','40371','48140','20268','52665']):  # add by Betty
            #因异常合约太多,改成记录模式,2020.11.26
            if self.common.isTimeInToday(sourceUpdateTime) is False:
                sourceUpdateTime_list.append(instrCode)
                continue
            # self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 更新时间是否是当天的数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                self.assertTrue(int(sourceUpdateTime) / (pow(10, 6)) <= int(
                    self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            # 已经确认，用合约里的这两个字段，而不是这两个，2020.11.26
            # instrName = json_info['instrName']
            # instrEnName = json_info['instrEnName']

            # 已经确认， INDEX 类的静态数据，没有stock,2020.11.26
            if productCode == 'INDEX':
                continue

            stock = json_info['stock']

            # 港股、美股都需要
            lot_size = stock['lotSize']
            # 检查总股本 ，美股因BUG,暂时不检查,已停牌的合约不检查
            # if exchange == 'SEHK' and (productCode not in ['BOND', 'WRNT', 'INDEX', 'GIPO']) and (instrCode not in ['00498','04338','07302','08304']):
            #     issued_shares = stock['issuedShares']

            # 检查流通股，美股因BUG,暂时不检查,已停牌的合约不检查
            # if exchange == 'SEHK' and (productCode not in ['BOND', 'TRST', 'WRNT', 'INDEX', 'GIPO']) and (instrCode not in ['00498','04338','07302','08304']):
            #     outstanding_shares = stock['outstandingShares']

            # 债券很多没有交易币种 ，暗盘需要交易货币，但因BUG，临时屏蔽
            if productCode not in ['BOND']:
                trade_currency = stock['tradeCurrency']

            # 股票静态数据
            if exchange == 'SEHK' and (json_info.get('type') not in ['GREY_MARKET']):  # 港股 且 非暗盘
                casflag = stock['casflag']
                vcmflag = stock['vcmflag']

            #仅对港股供股权有效; 涡轮、牛熊证、界内证有效，已经终止交易的不需要判断,因BUG,注释掉
            lasttradedayFlag = False

            if exchange == 'SEHK':
                if productCode in ['WRNT']:  # 涡轮、牛熊证、界内证
                    lasttradedayFlag = True

                if 'type' in json_info:
                    type = json_info['type']
                    if type in ['EQUITY_RIGHTS']:  # 股权
                        lasttradedayFlag = True

                if lasttradedayFlag is True:
                    if 'lasttradeday' in stock:
                        lasttradeday = stock['lasttradeday']
                    else:
                        lasttradeday_list.append(instrCode)


            # 暗盘没有到期日
            if exchange == 'SEHK' and (productCode not in ['EQTY', 'TRST', 'WRNT', 'BOND', 'GIPO']):  # 非股票，才检测 到期日 && 回收价，因停止交易的牛熊证，缺少这个字段，才不检查 2020.11.20
                maturity_date = stock['maturityDate']

                # if type in ['WARRANT_CALLABLE_BULL_BEAR_CONTRACT']:  # 回收价(牛熊证) ，暂不检查，因停止交易的牛熊证，缺少这个字段 2020.11.20
                #     call_price = stock['callPrice']
                    # 使用另外的小数约定规则，因此不检查该字段
                    #decimal_price = stock['decimalPrice']  #回收价小数位(牛熊证)(港股)

            # 房地产基金 TRUST_REAL_ESTATE_INVESTMENT_TRUST #因BUG,注释掉
            if exchange == 'SEHK' and ('type' in json_info):
                    type = json_info['type']  # 房地产基金 没资产净值，不需要发布日期
                    if type in ['TRUST_EXCHANGE_TRADED_FUND', 'TRUST_OTHER_UNIT_TRUSTS', 'TRUST_LEVERAGED_AND_INVERSE_PRODUCT']:
                        if 'release_day' in stock:
                            release_day = stock['releaseday']  # 发布日期(基金有效)(港股)
                        else:
                            releaseday_list.append(instrCode)
            # 产品已经确认，暗盘 这个字段未被使用
            if exchange == 'SEHK' and (json_info.get('type') not in ['GREY_MARKET']):
                listingdate = stock['listingdate']
            # 未使用
            # delistingdate = stock['delistingdate']

            #港股、美股都需要
            exchangeInstr = json_info['exchangeInstr']
            self.assertTrue(exchangeInstr == instrCode)
            # 部分股票不满足这个规则，比如：'instrCode': '16864'，因此注释掉，2010.11.13
            # self.assertTrue(exchangeInstr == instrName)

            # 产品已经确认，此四个字段暂不验证
            # marketStatus = json_info['marketStatus']
            # instrStatus = json_info['instrStatus']
            # upperLimit = json_info['upperLimit']
            # lowerLimit = json_info['lowerLimit']
            # 已经终止交易的不需要判断，因BUG，临时屏蔽
            if 'type' in json_info:
                type = json_info['type']
                if type not in ['EQUITY_ORDINARY_SHARES', 'EQUITY_PREFERENCE_SHARES', 'GREY_MARKET',
                                         'EQUITY_DEPOSITORY_RECEIPT_ORDINARY_SHARES',
                                         'EQUITY_DEPOSITORY_RECEIPT_PREFERENCE_SHARES', 'EQUITY_RIGHTS',
                                         'WARRANT_EQUITY_WARRANT', 'WARRANT_DERIVATIVE_WARRANT',
                                         'WARRANT_EQUITY_LINKED_INSTRUMENT', 'WARRANT_CALLABLE_BULL_BEAR_CONTRACT',
                                         'BOND_DEBT_SECURITY', 'TRUST_EXCHANGE_TRADED_FUND',
                                         'TRUST_REAL_ESTATE_INVESTMENT_TRUST', 'TRUST_OTHER_UNIT_TRUSTS',
                                         'TRUST_LEVERAGED_AND_INVERSE_PRODUCT', 'OTHERS_NONE_OF_THE_ABOVE','EQUITY_US_I',
                                         'WARRANT_INLINE_WARRANT', 'EQUITY_RIGHTS']:  # 非暗盘、#港股、美股都需要
                    preClose = json_info['preClose']
                    source = json_info['source']

            #因BUG，暂不验证，2020.11.26
            # self.assertTrue(int(collectorSendTime) >= int(collectorRecvTime))  # 采集发出时间大于采集接受时间

        self.logger.debug('静态数据 检查结果,sourceUpdateTime非今天的合约列表 sourceUpdateTime_list:{}'.format(sourceUpdateTime_list))
        self.logger.debug('静态数据检查结果,缺少lasttradeday的合约列表 lasttradeday_list:{}'.format(lasttradeday_list))
        self.logger.debug('静态数据检查结果,缺少release_day的合约列表 releaseday_list:{}'.format(releaseday_list))


    def test_stock_03_01_QuoteBasicInfo(self):  # dealer模式下请求返回的静态数据
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
            self.test_stock_03_QuoteBasicInfo(dealer_basic_info_list, record_time)

    def test_stock_04_QuoteTradeData(self):  # 逐笔成交数据
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
                pass
                # productCode = commonInfo['productCode']     # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-437
                collectorRecvTime = commonInfo['collectorRecvTime']     # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-520
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
            stock = tradeTick.get("stock")      # 港股成交类型
            sourceUpdateTime = json_info['sourceUpdateTime']

            if self.sub_time:
                self.assertTrue(self.common.isTimeInToday(sourceUpdateTime))  # 订阅时, 更新时间是当天数据

            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                sourceUTime = int(sourceUpdateTime) / (pow(10, 6)) + 8000
                if self.is_delay is True:  # 延时行情
                    sourceUTime = sourceUTime + 15 * 60 * 8000

                if not self.is_before_data:  # 实时数据
                    if exchange != 'HKFE':
                        self.assertTrue(sourceUTime >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    else:
                        self.assertTrue(sourceUTime >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    self.assertTrue(sourceUTime <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

            # 同一个交易所, 数据有序更新
            if not assert_json.get(exchange + '_sourceUpdateTime'):
                assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
            else:
                try:
                    assert int(sourceUpdateTime) >= assert_json[exchange + '_sourceUpdateTime']
                except AssertionError:
                    # 更新时间小于上个数据更新时间时, 校验误差不超过一秒
                    timeLag = lambda x, y : datetime.datetime.fromtimestamp(x/pow(10, 9)) - datetime.datetime.fromtimestamp(y/pow(10, 9))
                    Lag = timeLag(int(sourceUpdateTime), int(assert_json[exchange + '_sourceUpdateTime']))  # 获取时间差
                    assert abs(Lag.total_seconds()) <= 1        # 更新时间误差一秒

                assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)

            if instrCode in assert_json['instrCodeList']:   # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-438
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


    def test_stock_04_APP_BeforeQuoteTradeData(self):
        check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        if not self.exchange:
            exchange = 'noExchange' 
        else:
            exchange = self.exchange
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
            # 交易成交量不为0
            assert vol > 0

            if self.exchange:
                # 当req_hisdata_type=CUR_TRADEDATE_DATA时, 逐笔数据的时间为当天
                timelist = self.common.check_trade_status(exchange, isgetTime=True)
                # 获取开盘时间的时间戳
                _startTime = timeStamp = int(time.mktime(time.strptime(timelist[0], "%Y%m%d%H%M%S")))
                assert _startTime < trade_time      # 判断逐笔数据的时间为当天数据


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

# -----------------------------------------------------------------------------------------------
# 未上市股票合约字段: 简体名称、繁体名称、英文名称，交易所、每手股数、上市日期
# -----------------------------------------------------------------------------------------------
    def test_stock_05_InstrumentInfo(self):
        if self.check_json_list == None:
            check_info = self.sq.get_deal_json_records(QuoteMsgType.SYNC_INSTR_RSP, 100)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))

        # settle_currency_list = []
        tc_simple_name_list = []
        cn_simple_name_list = []
        index_List = []

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
                if exchange in ['CME', 'NYMEX', 'CBOT', 'COMEX', 'SGX', 'HKFE']:  # 如果是港期 和外期，不检查
                    continue

                instrCode = base['instrCode']

                # 检查是否如期过滤掉了上证指数
                if instrCode in ['000016','000021','000010','000009','000066','000001','000015','000043','000044','000065']:
                    index_List.append(instrCode)

                proc = instrument['proc']
                categoryType = proc['categoryType']

                # 因BUG，临时屏蔽，2010.11.19
                if categoryType not in ['INDEX']:  # 临时增加条件，因INDEX类BUG ,2020.11.19
                    # 检查中文名称，2020.11.19
                    if 'cnSimpleName' in base:
                        cn_simple_name = base['cnSimpleName']
                    else:
                        cn_simple_name_list.append(instrCode)

                    # 产品已经确认，下个版本才需要繁体，2010.11.19
                    if 'tcSimpleName' in base:
                        tc_simple_name = base['tcSimpleName']
                    else:
                        tc_simple_name_list.append(instrCode)
                    en_simple_name = base['enSimpleName']
                    # 产品已经确认，暂不需要这三个字段,2020.11.17
                    # cn_full_name = base['cnFullName']
                    # tc_full_name = base['tcFullName']
                    # en_full_name = base['enFullName']

                if categoryType != 'STOCKS' and categoryType != 'INDEX':   #  非证券、非指数时，检查；证券和指数，在下面的条件判断里检查
                    settle_currency = base['settleCurrency']
                    trade_currency = base['tradeCurrency']

                # productType = proc['productType']  # 证券暂时不用
                self.assertTrue(categoryType in ['STOCKS', 'FOREX', 'OPT', 'SPOT_TRANS', 'SPOT', 'EFP', 'INDEX'])

                timespin = proc['timespin']
                callMarket = self.common.doDicEvaluate(proc, 'callMarket', 2)  # 集合竞价时间片,有的品种没有集合竞价
                trade = proc['trade']  # 交易时间片
                lotSizePrecision = int(self.common.doDicEvaluate(instrument, 'lotSizePrecision', 0))

                if categoryType != 'INDEX' and 'status' in instrument:  # 指数类的不检查状态 && 未上市股票不检查装
                    status = instrument['status']
                    self.assertTrue(status in ['STARTED', 'TRADING', 'PAUSE', 'DELIVERY', 'EXPIRED', 'DELISTING',
                                               'SUSPEND', 'LOCKED', 'FUSING', 'SUSPENSION', 'RESUMPTION'])

                if categoryType == 'OPT':  # 期权合约特定信息
                    opt = instrument['opt']
                    underlying_code = opt['underlyingcode']
                    underlying_exchange = opt['underlyingexchange']

                    margin_rate_type = opt['marginratetype']
                    long_margin = opt['longmargin']
                    short_margin = opt['shortmargin']

                    market_order_qty = opt['marketorderqty']
                    limit_order_qty = opt['limitorderqty']
                    contract_multiplier = opt['contractmultiplier']

                    deliver_year = opt['deliveryear']
                    deliver_month = opt['delivermonth']
                    is_enable = opt['isenable']

                    last_trade_date = opt['lasttradedate']
                    notify_date = opt['notifydate']
                    expire_date = opt['expiredate']
                    expire_month = opt['expiremonth']

                    begin_deliver_date = opt['begindeliverdate']
                    end_deliver_date = opt['enddeliverdate']
                elif categoryType == 'INDEX':  # 指数特定信息
                    #指数的合约编号 有的是纯字母，有的是字母和数字 ，有的是淳数字
                    #self.assertTrue(instrCode.isalnum())
                    # 产品已经确认，前端未用到结算币种，2021.2.1
                    # if 'settleCurrency' in base:
                    #     settle_currency = base['settleCurrency']
                    # else:
                    #     settle_currency_list.append(instrCode)

                    index = instrument['index']
                    self.assertTrue(exchange == index['exchange'])
                    # 产品已经确认不需要，因此屏蔽
                    # indexsource = index['indexsource']
                    # self.assertTrue(indexsource in ['C', 'S', 'H', 'T'])
                    # 因BUG，临时屏蔽
                    # currency = index['currency']
                    # self.assertTrue(settle_currency == currency)

                elif categoryType == 'STOCKS':  # 证券特定信息
                    if exchange == 'SEHK':
                        self.assertTrue(len(instrCode) == 5)
                        self.assertTrue(instrCode.isdigit())
                        # 因BUG，临时屏蔽
                    # else:
                        # self.assertTrue(instrCode.isalpha())

                    stock = instrument['stock']
                    self.assertTrue(exchange == stock['exchange'])

                    # 因 SEHK_MAIN=0
                    if 'marketcode' in stock:
                        marketcode = stock['marketcode']
                    else:
                        marketcode = 'SEHK_MAIN'

                    if exchange == 'SEHK':
                        self.assertTrue(marketcode in ['SEHK_MAIN', 'SEHK_GEM', 'SEHK_ETS', 'SEHK_NASD'])
                    else:
                        self.assertTrue(marketcode in ['NASDAQ_Q', 'NASDAQ_G', 'NASDAQ_S', 'NASDAQ_N', 'NASDAQ_A',
                                                       'NASDAQ_P', 'NASDAQ_Z', 'NASDAQ_V', 'NASDAQ_O'])

                    # 产品已经确认APP用的是静态数据和快照数据中的昨收价，这个暂不验证，2020.11.19
                    #preclose = stock['preclose']
                    lotsize = stock['lotsize']

                    if exchange == 'SEHK':
                        # 产品已经确认，isincode 暂未使用，不验证，2020.11.19
                        # isincode = stock['isincode']

                        # 临时注销，待股票的状态正确后再判断
                        # instrumentCode = stock['instrument']
                        # self.assertTrue(instrumentCode in ['BOND', 'EQTY', 'TRST', 'WRNT'])

                        # 非今天的暗盘 producttype字段为'IPO'，今天的暗盘 producttype字段为'GreyMarket'
                        producttype = stock['producttype']
                        self.assertTrue(producttype in ['EQUITY_ORDINARY_SHARES', 'EQUITY_PREFERENCE_SHARES',
                                                        'EQUITY_DEPOSITORY_RECEIPT_ORDINARY_SHARES',
                                                        'EQUITY_DEPOSITORY_RECEIPT_PREFERENCE_SHARES', 'EQUITY_RIGHTS',
                                                        'WARRANT_EQUITY_WARRANT', 'WARRANT_DERIVATIVE_WARRANT',
                                                        'WARRANT_EQUITY_LINKED_INSTRUMENT',
                                                        'WARRANT_CALLABLE_BULL_BEAR_CONTRACT',
                                                        'BOND_DEBT_SECURITY', 'TRUST_EXCHANGE_TRADED_FUND',
                                                        'TRUST_REAL_ESTATE_INVESTMENT_TRUST', 'TRUST_OTHER_UNIT_TRUSTS',
                                                        'TRUST_LEVERAGED_AND_INVERSE_PRODUCT', 'OTHERS_NONE_OF_THE_ABOVE',
                                                        'WARRANT_INLINE_WARRANT', 'IPO', 'GREY_MARKET'])

                        if producttype != 'BOND_DEBT_SECURITY':  # 因债券，部分没这两个字段，因此，不检查
                            settle_currency = base['settleCurrency']
                            trade_currency = base['tradeCurrency']

                        if producttype not in ['IPO', 'GREY_MARKET']:  # 上市股票
                            spread = stock['spread']
                            vcmflag = stock['vcmflag']
                            shortsell = stock['shortsell']
                            casflag = stock['casflag']
                            ccassflag = stock['ccassflag']
                            dummyflag = stock['dummyflag']
                            testflag = stock['testflag']
                            stampdutyflag = stock['stampdutyflag']

                        listingdate = stock['listingdate']
                        if producttype not in ['IPO', 'GREY_MARKET']:  # 上市股票
                            delistingdate = stock['delistingdate']
                            freetext = stock['freetext']
                            enfflag = stock['enfflag']
                        # 产品确认暂不需要，2010.10.21
                        # accured = stock['accured']
                        # couponrate = stock['couponrate']
                        # counversionratio = stock['counversionratio']
                        # strikeprice1 = stock['strikeprice1']
                        # strikeprice2 = stock['strikeprice2']
                        if producttype not in ['IPO', 'GREY_MARKET']:  # 上市股票
                            maturitydate = stock['maturitydate']
                            callput = stock['callput']
                            style = stock['style']
                            warrenttype = stock['warrenttype']
                        # 产品确认暂不需要，2010.10.21
                        # callprice = stock['callprice']
                        # decimalprice = stock['decimalprice']
                        # entitlement = stock['entitlement']
                        # decimalentitlement = stock['decimalentitlement']
                        if producttype not in ['IPO', 'GREY_MARKET']:  # 上市股票
                            nowarrants = stock['nowarrants']
                            nounderlying = stock['nounderlying']
                    else:
                        type = stock['type']
                        subtype = stock['subtype']
                        etf = stock['etf']
                        kind = stock['kind']
                        state = stock['state']
                        tradedate = stock['tradedate']
                else:
                    self.logger.debug('categoryType:={} '.format(categoryType))

                timespin = timespin.rstrip(' ')
                timespinList = re.findall('(\d+-\d+) ?', timespin)
                assert_list = trade + callMarket  # timespin字段是由交易时间和竞价时间组合得到的
                start_list = [assert_list[j]['start'] for j in range(assert_list.__len__())]
                end_list = [assert_list[k]['end'] for k in range(assert_list.__len__())]

                self.assertTrue(end_list.__len__()==end_list.__len__())

                for i in range(start_list.__len__()):  # 校验时间片与交易时间、竞价时间的匹配性
                    startFlag = False
                    endFlag = False
                    for j in range(timespinList.__len__()):
                        if str(start_list[i]) in str(timespinList[j]):
                            startFlag = True

                        if str(end_list[i]) in str(timespinList[j]):
                            endFlag = True

                    self.assertTrue(startFlag is True)
                    self.assertTrue(endFlag is True)

        # self.logger.debug('合约检查，缺少结算币种的合约列表settle_currency_list:={}'.format(settle_currency_list))
        self.logger.debug('合约检查，缺少合约简体简称的合约列表cn_simple_name_list:={}'.format(cn_simple_name_list))
        self.logger.debug('合约检查，缺少合约繁体简称的合约列表tc_simple_name_list:={}'.format(tc_simple_name_list))
        self.logger.debug('合约检查，异常存在的上证指数 index_List:={}'.format(index_List))

    def test_stock_06_PushKLineMinData(self):
        # 推送分时K线
        peroidType = 'MIN'
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_KLINE_MIN, 1000000)
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

            # 当开, 高, 低 没有时, 可能是未来合约, 还没有人交易
            if data.get("open") and data.get("high") and data.get("low"):
                high = int(data['high'])
                open = int(data['open'])
                low = int(data['low'])
                close = int(data['close'])
                average = int(data.get("average") or 0)  # 均价有可能为0
                vol = int(data.get("vol") or 0)  # 成交量, 可能为0
                riseFall = int(self.common.doDicEvaluate(data, 'riseFall'))
                rFRatio = int(self.common.doDicEvaluate(data, 'rFRatio'))
                updateDateTime = data['updateDateTime']
                settlementPrice = int(data.get("settlementPrice") or 0)  # 昨收价, BUG: http://jira.eddid.com.cn:18080/browse/HQZX-677

                # high, open, low, close基本校验
                self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
                self.assertTrue(int(high) >= int(close) >= int(low))  # 收盘价在最高价最低价之间

                # 校验当日昨收相等
                if "{}_{}_settlementPrice".format(exchange, code) not in assert_json.keys():
                    assert_json["{}_{}_settlementPrice".format(exchange, code)] = settlementPrice
                    # 记录updateDateTime, 年月日
                    assert_json["{}_{}_updateDateTime".format(exchange, code)] = updateDateTime[:8]
                else:
                    # 判断同一交易日, 结算价相等
                    self.assertTrue(settlementPrice == assert_json["{}_{}_settlementPrice".format(exchange, code)])

                if settlementPrice:
                    # 涨跌额 = 当前价格 - 结算价
                    assert abs(riseFall - (close - settlementPrice)) <= 1
                    # assert riseFall == close - settlementPrice
                    # # # 涨跌幅 = (涨跌额 / 昨收价), 涨跌幅返回的数据为百分比数据, 故 涨跌幅/100 == (涨跌额/昨收价) * 100
                    # # # assert abs(rFRatio - int((riseFall / settlementPrice) * 100 * 100)) <= 1      # float精度有误, 故加上误差1
                    assert rFRatio == int(self.common.new_round(float(Decimal(str(riseFall)) / Decimal(str(settlementPrice)) * 100 * 100)))  # Decimal处理float精度问题

                updateDateTimeStamp = int(time.mktime(time.strptime(updateDateTime, "%Y%m%d%H%M%S"))) * 1000
                if self.is_before_data:
                    self.assertTrue(int(updateDateTimeStamp) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    self.assertTrue(int(updateDateTimeStamp) >= int(self.start_time))  # 订阅服务时用来判断APP开始时间与源时间


    def test_stock_07_PushKLineData(self):
        # 推送K线数据
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_KLINE, 1000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)

        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {}
        tradeTimelist = []
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
                peroidType = json_info['peroidType']
                kData = json_info['kData']
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


            latest_time_stamp = int(time.mktime(time.strptime(latest_time, "%Y%m%d%H%M%S"))) * 1000
            high = int(kData['high'])
            open = int(kData['open'])
            low = int(kData['low'])
            close = int(kData['close'])
            currVol = int((kData.get("currVol") or 0))                  # 当前这笔K线的成交量
            vol = int((kData.get("vol") or 0))                  # # 累计到当前这一笔K线的总成交量
            openInterest = int(kData.get("openInterest") or 0)                   # 持仓量, BUG:http://jira.eddid.com.cn:18080/browse/HQZX-458
            amount = int(kData.get("amount") or 0)     # 成交额可能为0
            riseFall = int(self.common.doDicEvaluate(kData, 'riseFall'))
            rFRatio = int(self.common.doDicEvaluate(kData, 'rFRatio'))
            preClose = int(self.common.doDicEvaluate(kData, 'preClose'))
            peroidTypeInt = k_type_convert(peroidType)  # 频率
            if peroidTypeInt in [KLinePeriodType.DAY, KLinePeriodType.WEEK, KLinePeriodType.MONTH,
                                 KLinePeriodType.SEASON, KLinePeriodType.YEAR]:  # 日K级别及以上类型才有下面字段
                settlementPrice = kData.get("settlementPrice")      # 昨结价
                # preSettlement = kData['preSettlement']        # 昨结
                # preClose = kData['preClose']                  # 昨收, 期货上一根K线 的收盘价

            updateDateTime = kData['updateDateTime']
            KLineKey = kData['KLineKey']
            totalAmount = int(kData.get("totalAmount") or 0)      # 总成交金额, 期货不需要成交金额

            # 获取第一根K线所对应的交易时间
            if check_info.index(info) == 0 and peroidTypeInt < 18:
                tradeTimelist = self.common.check_trade_status(exchange, code, curTime=updateDateTime, isgetTime=True, peroidType=peroidType)
                self.logger.debug(tradeTimelist)

            self.assertTrue(int(high) >= int(open) >= int(low))  # 开盘价在最高价最低价之间
            self.assertTrue(int(high) >= int(close) >= int(low))  # 收盘价在最高价最低价之间

            if ('{}_{}_current_time'.format(code, peroidType) in assert_json.keys()):
                # 代表同一根K线上的更新
                if KLineKey == assert_json['{}_{}_current_time'.format(code, peroidType)]:
                    self.assertTrue(open == assert_json['{}_{}_current_open'.format(code, peroidType)])  # 同一根K线, 开盘价不变
                    # 保存同一根K线最高价和最低价
                    self.assertTrue(currVol >= assert_json['{}_{}_currVol'.format(code, peroidType)])  # 同一根K线, 成交量大于等于上一刻成交量
                    self.assertTrue(vol >= assert_json['{}_{}_last_vol'.format(code, peroidType)])  # 同一根K线, 总成交量大于等于上一刻总成交量

                    # 第二根K线与第一根K线的对比, 校验涨跌额和涨跌幅
                    if KLineKey != assert_json['{}_{}_first_check_time'.format(code, peroidType)]:
                        # 涨跌额 = 收盘价 - 上一根K线收盘价
                        self.assertTrue(riseFall == close - assert_json['{}_{}_lastclose'.format(code, peroidType)])
                        # 涨跌幅 = 涨跌额 / 上一根K线收盘价
                        # assert rFRatio == int(self.common.new_round(10000 * riseFall / (assert_json['{}_{}_lastclose'.format(code, peroidType)])))
                        assert rFRatio == int(10000 * riseFall / (assert_json['{}_{}_lastclose'.format(code, peroidType)]))

                        # 当前一笔K线成交量 = 总成交量 - 上一笔K线成交量
                        self.assertTrue(currVol == vol - assert_json['{}_{}_lastKline_vol'.format(code, peroidType)])

                else:  # K线更新, 校验涨跌和成交量, 初始化数据
                    self.assertTrue(int(KLineKey) > int(assert_json['{}_{}_current_time'.format(code, peroidType)]))
                    # 涨跌额 = 收盘价 - 上次收盘价
                    ### self.assertTrue(riseFall == close - assert_json['{}_{}_close'.format(code, peroidType)])  # BUG
                    assert riseFall == close - preClose
                    # 涨跌幅 = 涨跌额 / 上次收盘价
                    ### assert rFRatio == int(10000 * riseFall / (assert_json['{}_{}_close'.format(code, peroidType)]))
                    assert rFRatio == int(riseFall / preClose * 100 * 100)

                    # 当日总成交量递增, 日K以下校验
                    if peroidTypeInt not in [KLinePeriodType.DAY, KLinePeriodType.WEEK, KLinePeriodType.MONTH,
                                         KLinePeriodType.SEASON, KLinePeriodType.YEAR]:  # 日K级别及以上类型才有下面字段
                        pass
                        if updateDateTime in tradeTimelist:     # 同一天
                            self.assertTrue(vol >= assert_json['{}_{}_last_vol'.format(code, peroidType)])
                            # 当日 currVol = vol - 上一根vol
                            # self.assertTrue(currVol == vol - assert_json['{}_{}_last_vol'.format(code, peroidType)])  # BUG, 数据不是实时存
                        else:   # 更新交易日
                            tradeTimelist = self.common.check_trade_status(exchange, code, curTime=updateDateTime, isgetTime=True, peroidType=peroidType)

                        assert KLineKey in tradeTimelist

                    # 更新 新K线数据
                    assert_json['{}_{}_current_time'.format(code, peroidType)] = KLineKey  # 新K线日期
                    assert_json['{}_{}_current_open'.format(code, peroidType)] = open  # 新K线初始开盘价
                    assert_json['{}_{}_lastKline_vol'.format(code, peroidType)] = assert_json['{}_{}_last_vol'.format(code, peroidType)]  # 上一根K线的成交量
                    assert_json['{}_{}_lastclose'.format(code, peroidType)] = assert_json['{}_{}_close'.format(code, peroidType)]  # 记录上一根K线的收盘价

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
                self.assertTrue(int(self.start_time) <= int(updateDateTimeStamp) <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间

    def test_stock_10_01_PushBrokerSnapshot(self):  # dealer模式下请求返回的经纪席位数据
        check_info = self.sq.get_deal_json_records(QuoteMsgType.PUSH_BROKER_SNAPSHOT, 100)
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        for info in check_info:
            record_time = info[1]
            json_info = json.loads(info[0])
            retResult = json_info['retResult']
            retCode = retResult['retCode']
            self.assertTrue(retCode == 'SUCCESS')  # 校验接口返回状态
            pushBrokerSnapshot_info_List = json_info['brokerSnapshotInfos']
            self.test_stock_10_PushBrokerSnapshot(pushBrokerSnapshot_info_List, record_time)


    def test_stock_10_PushBrokerSnapshot(self, dealer_brokerSnapshot_list=None, dealer_record_time=None):
        # 推送经纪席位数据
        if dealer_brokerSnapshot_list == None:
            if self.check_json_list == None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_BROKER_SNAPSHOT, 100)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_brokerSnapshot_list

        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))

        sell_number_list = []
        buy_number_list = []
        sell_position_list = []
        buy_position_list = []

        for info in check_info:
            if dealer_brokerSnapshot_list == None:
                if self.check_json_list == None:
                    record_time = info[1]
                else:
                    record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                    json_info = info
            else:
                record_time = dealer_record_time
                json_info = info

            self.logger.debug(json_info)
            if 'exchange' in json_info:
                exchange = json_info['exchange']
                self.assertTrue(exchange == 'SEHK')
            else:
                break

            code = json_info['code']
            #判断是否是暗盘
            if code in [SEHK_greyMarketCode1, SEHK_greyMarketCode2]:
                greyFlag = True
            else:
                greyFlag = False

            data = json_info['data']
            code_inside = data['code']
            self.assertTrue(code_inside == code)
            timestamp = max(int(self.common.doDicEvaluate(data, 'timestampBuy', 0)),
                            int(self.common.doDicEvaluate(data, 'timestampSell', 0)))
            queue_sell = data['queueSell']
            queue_buy = data['queueBuy']

            t= int(code)
            if t == 52497:
                t = 1
            for i in range(queue_sell.__len__()):
                sell_info = queue_sell[i]
                position = int(sell_info['position'])
                # self.logger.debug('check 卖盘 经纪席位 position====:{}'.format(position))
                # self.logger.debug('check 卖盘 经纪席位 i=======：{}'.format(i))
                if position != i + 1:
                    sell_position_list.append(code)
                # self.assertTrue(position == i + 1)
                if 'brokes' in sell_info:  # 部分买盘/卖盘无经济席位
                    for brokes in sell_info['brokes']:
                        broker_code = brokes['brokerCode']
                        #经济席位编码只能是4位
                        if len(broker_code) != 4:
                            sell_number_list.append(code)

                        if greyFlag is False: #非暗盘，暗盘的经济席位一般没编码
                            broker_name = brokes['brokerName']

                        # V2.22: 修复经纪id为三位数的经纪名称没有正常显示的问题
                        if broker_code[0] == "0":
                            # self.logger.debug("0开头的经济席位")
                            self.logger.debug(broker_code)
                            assert brokes['brokerName'] != "--"

            for j in range(queue_buy.__len__()):
                buy_info = queue_buy[j]
                position = int(buy_info['position'])
                # self.logger.debug('check 买盘 经纪席位 position====:{}'.format(position))
                # self.logger.debug('check 买盘 经纪席位 i=======：{}'.format(j))
                if position != j + 1:
                    buy_position_list.append(code)
                # self.assertTrue(position == j + 1)
                if 'brokes' in buy_info:  # 部分买盘/卖盘无经济席位
                    for brokes in buy_info['brokes']:
                        broker_code = brokes['brokerCode']
                        # 经济席位编码只能是4位
                        if len(broker_code) != 4:
                            buy_number_list.append(code)

                        if greyFlag is False:  # 非暗盘，暗盘的经济席位一般没编码
                            broker_name = brokes['brokerName']

                        # V2.22: 修复经纪id为三位数的经纪名称没有正常显示的问题
                        if broker_code[0] == "0":
                            # self.logger.debug("0开头的经济席位")
                            assert brokes['brokerName'] != "--"

            self.assertTrue(code == code_inside)
            if self.sub_time:
                self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                if not self.is_before_data:  # 实时数据
                    self.assertTrue(int(timestamp) / (pow(10, 6)) >= int(
                        self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    self.assertTrue(int(timestamp) / (pow(10, 6)) <= int(
                        self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
            else:
                pass

        self.logger.debug('check 经纪席位 异常买盘经纪席位is:{}'.format(buy_number_list))
        self.logger.debug('check 经纪席位 异常卖盘经纪席位is:{}'.format(sell_number_list))
        self.logger.debug('check 经纪席位 异常买盘经纪席位positon:{}'.format(buy_position_list))
        self.logger.debug('check 经纪席位 异常卖盘经纪席位positon:{}'.format(sell_position_list))

    def test_stock_11_NewsharesQuoteSnapshot(self):
        # 推送已上市新股行情快照数据
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_NEW_SHARES_SNAPSHOT, 1000)
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
            self.logger.debug(json_info)
            common_info = json_info['commonInfo']
            exchange = common_info['exchange']
            self.assertTrue(exchange in ['SEHK', 'ASE', 'NYSE', 'NASDAQ', 'BATS', 'IEX'])
            
            product_code = common_info['productCode']
            instr_code = common_info['instrCode']
            precision = common_info['precision']
            if exchange == 'SEHK':
                precision = 3
            else:
                precision = 4
            #因BUG，临时注释
            # collectorRecvTime = common_info['collectorRecvTime']
            # collectorSendTime = common_info['collectorSendTime']
            # publisherRecvTime = common_info['publisherRecvTime']
            # publisherSendTime = common_info['publisherSendTime']
            # 因BUG，临时注释
            # self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            if self.check_json_list is not None:
                publisherRecvTime = common_info['publisherRecvTime']
                publisherSendTime = common_info['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间
            
            last = json_info['last']
            # 因BUG，临时注释
            # grey_market_rise_fall = json_info['greyMarketRiseFall']
            # grey_market_r_f_ratio = json_info['greyMarketRFRatio']
            # first_rise_fall = json_info['firstRiseFall']
            # first_r_f_ratio = json_info['firstRfRatio']
            # 因BUG，临时注释
            # highest20days_rise_fall = json_info['highest20daysRiseFall']
            # highest20days_r_f_ratio = json_info['highest20daysRFRatio']
            # 因BUG，临时注释
            # tophighestfromyesr_rise_fall = json_info['tophighestfromyesrRiseFall']
            # tophighestfromyesr_r_f_ratio = json_info['tophighestfromyesrRFRatio']
            source_update_time = json_info['sourceUpdateTime']

    def test_stock_12_GreyMarketQuoteSnapshot(self):
        # 推送暗盘行情快照数据
        if self.check_json_list == None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_GREY_MARKET_SNAPSHOT, 1000)
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
            self.logger.debug(json_info)
            common_info = json_info['commonInfo']
            exchange = common_info['exchange']
            self.assertTrue(exchange in ['SEHK', 'ASE', 'NYSE', 'NASDAQ', 'BATS', 'IEX'])

            product_code = common_info['productCode']
            instr_code = common_info['instrCode']
            precision = common_info['precision']
            if exchange == 'SEHK':
                precision = 3
            else:
                precision = 4

            collectorRecvTime = common_info['collectorRecvTime']
            collectorSendTime = common_info['collectorSendTime']

            publisherRecvTime = common_info['publisherRecvTime']
            publisherSendTime = common_info['publisherSendTime']
            #  因BUG，屏蔽
            self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
            if self.check_json_list is not None:
                publisherRecvTime = common_info['publisherRecvTime']
                publisherSendTime = common_info['publisherSendTime']
                self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间

            last = json_info['last']
            rise_fall = json_info['riseFall']
            r_f_ratio = json_info['rFRatio']
            source_update_time = json_info['sourceUpdateTime']

    def test_stock_13_QuoteEquipriceData(self, dealer_quipriceData_info_list=None, dealer_record_time=None):  # 推送的平衡价格
        if dealer_quipriceData_info_list == None:
            if self.check_json_list == None:
                check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_EQUIPRRCE, 100)
            else:
                check_info = self.check_json_list
        else:
            check_info = dealer_quipriceData_info_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))

        iep_list = []
        iev_List = []
        index_List = []

        for info in check_info[0]['eData']:
            if dealer_quipriceData_info_list == None:
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
            self.assertTrue(exchange in ['SEHK', 'ASE', 'NASDAQ', 'NYSE', 'BATS', 'IEX'])

            productCode = commonInfo['productCode']
            # 证券目前填写: "BOND"(债券); "EQTY"(股票); "TRST"(信托产品); "WRNT"(权证); "INDEX"(指数)
            self.assertTrue(productCode in ['BOND', 'EQTY', 'TRST', 'WRNT', 'INDEX', 'GIPO'])

            instrCode = commonInfo['instrCode']

            # 检查是否如期过滤掉了上证指数
            if instrCode in ['000016', '000021', '000010', '000009', '000066', '000001', '000015', '000043', '000044',
                             '000065']:
                index_List.append(instrCode)

            precision = self.common.doDicEvaluate(commonInfo, 'precision', 0)  # 有些精度为0时，无返回
            if exchange == 'SEHK':  # 港股精确到3位
                self.assertTrue(precision == 3)
            else:  # 美股精确到4位
                self.assertTrue(precision == 4)

            if 'iep' in json_info:
                iep = int(json_info['iep'])
            else:
                iep_list.append(instrCode)

            if 'iev' in json_info:
                iev = int(json_info['iev'])
            else:
                iev_List.append(instrCode)

        self.logger.debug('平衡价格 检查结果,缺少成交量iev的合约列表 iev_List:{}'.format(iev_List))
        self.logger.debug('平衡价格 检查结果,缺少成交价iep的合约列表 iep_list:{}'.format(iep_list))
        self.logger.debug('平衡价格 检查结果，异常存在的上证指数 index_List:={}'.format(index_List))



    # 单独校验股票快照
    def test_stock_15_QuoteSnapshot(self):
        if self.check_json_list is None:
            check_info = self.sq.get_pub_json_records(QuoteMsgType.PUSH_SNAPSHOT, 100000)
        else:
            check_info = self.check_json_list
        self.assertTrue(check_info.__len__() >= 1)
        self.logger.debug('{} items to check!'.format(check_info.__len__()))
        assert_json = {'instrCodeList': []}
        # check_info = [json.loads(i[0]) for i in check_info]
        preclose_list = []
        callputType_list = []

        for info in check_info:
            if self.check_json_list is None:
                record_time = info[1]
                json_info = json.loads(info[0])
            else:
                record_time = int(time.time())  # 因是实时传入，所以可以取当前时间
                json_info = info
            data_type = json_info["dataType"]
            if data_type == 'EX_STOCK':
                self.logger.debug(json_info)
                # ---------------校验快照数据中的行情头 --------------------------
                commonInfo = json_info['commonInfo']
                exchange = commonInfo['exchange']
                productCode = commonInfo['productCode']
                instrCode = commonInfo['instrCode']
                precision = self.common.doDicEvaluate(commonInfo, 'precision')
                collectorRecvTime = commonInfo['collectorRecvTime']    #BUG: 没有返回数据, HQZX-410
                collectorSendTime = commonInfo['collectorSendTime']    #BUG: 没有返回数据
                self.assertTrue(int(collectorRecvTime) < int(collectorSendTime))  # 采集发出时间大于采集接受时间
                if self.check_json_list is not None:
                    publisherRecvTime = commonInfo['publisherRecvTime']
                    publisherSendTime = commonInfo['publisherSendTime']
                    self.assertTrue(int(publisherSendTime) >= int(publisherRecvTime))  # 订阅服务发出时间大于采集接受时间

                # ----------------校验行情-快照中的数据 --------------------------
                last = int(json_info['last'])     # BUG: http://jira.eddid.com.cn:18080/browse/HQZX-452
                if "open" in json_info.keys() and "high" in json_info.keys() and "low" in json_info.keys():
                    open = int(json_info['open'])
                    high = int(json_info['high'])
                    low = int(json_info['low'])
                    assert int(high) >= int(open) >= int(low)            # 开盘价在最高价最低价之间
                    assert int(high) >= int(last) >= int(low)         # BUG: low > last, http://jira.eddid.com.cn:18080/browse/HQZX-641

                volume = int(json_info.get("volume") or 0)
                turnover = int((json_info.get("turnover") or 0))    # 成交金额
                average = int(json_info.get("average") or 0)   # 当日均价
                riseFall = int(json_info.get("riseFall") or 0)
                rFRatio = int(json_info.get("rFRatio") or 0)
                sourceUpdateTime = int(json_info['sourceUpdateTime'])

                # 校验股票快照均价, 均价 == 成交额 / 成交量, 判断误差小于1
                assert abs(average - turnover / volume) < 1

                stock = json_info['stock']
                preclose = stock["preclose"]                              # 昨收价, BUG: http://jira.eddid.com.cn:18080/browse/HQZX-415
                amplitude = stock.get("amplitude")                         # 振幅
                committee = stock.get("committee")                             # 委比
                quantity_ratio = stock.get("quantityRatio")                 # 量比
                total_market_val = stock.get("totalMarketVal")              # 总市值
                circular_market_val = stock.get("circularMarketVal")        # 市值
                turnover_rate = stock.get("turnoverRate")                   # 换手率
                pe_ratio = stock.get("peRatio")                             # 静态市盈率
                pe_ttm_ratio = stock.get('peTtmRatio')                      # 滚动市盈率
                pb_ratio = stock.get('pbRatio')                             # 市净率
                dividend_ttm = stock.get('dividendTtm')                     # 股息TTM
                dividend_lfy = stock.get('dividendLfy')                     # 股息LFY
                dividend_ratio_ttm = stock.get("dividendRatioTtm")          # 股息率TTM
                dividend_ratio_lfy = stock.get("dividendRatioLfy")          # 股息率LFY
                highest52weeks_price = stock.get("highest52weeksPrice")     # 52周最高
                lowest52weeks_price = stock.get("lowest52weeksPrice")       # 52周最高

                # ----------------------------------------------------------------------
                # 振幅=(当日最高点的价格-当日最低点得到价格)/昨天收盘价*100%
                # assert int(amplitude) == (high - low) / int(preclose)


                # ------------------校验涨/跌额涨跌幅 ----------------------
                if preclose:
                    assert riseFall == last - int(preclose)     # BUG
                    assert rFRatio == int(self.common.new_round((riseFall / int(preclose)) * 10000))     # BUG:http://jira.eddid.com.cn:18080/browse/HQZX-524


                # self.assertTrue(self.common.ibbsTimeInToday(sourceUpdateTime))  # 判断更新时间为当天的数据
                if self.sub_time:
                    self.logger.debug('check sub_time is:{}'.format(self.sub_time))
                    sourceUTime = int(sourceUpdateTime) / (pow(10, 6)) + 8000
                    if self.is_delay is True:  # 延时行情
                        sourceUTime = sourceUTime + 15*60*1000 + 8000

                    if not self.is_before_data:  # 实时数据
                        ###################
                        # 回放数据时, sourceUpdateTime 小于 订阅时间
                        ###################
                        if exchange != 'SEHK':
                            self.assertTrue(sourceUTime >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                        else:
                            self.assertTrue(sourceUTime >= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                    # else: 前数据在接收时已经判断过了，此处不再判断
                    #     pass
                    #     self.assertTrue(sourceUTime <= int(self.sub_time))  # 订阅服务时用来判断订阅时间与源时间
                else:
                    pass

                # 更新时间有序递增
                if not self.is_before_data:
                    # self.logger.info(int(sourceUpdateTime))
                    if exchange + '_sourceUpdateTime' in assert_json.keys():
                        self.assertTrue(int(sourceUpdateTime) >= int(assert_json[exchange + '_sourceUpdateTime']))
                        assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
                    else:
                        assert_json[exchange + '_sourceUpdateTime'] = int(sourceUpdateTime)
                else:
                    pass
        self.logger.debug('快照检查结果 昨收价 缺少preclose_list:{}'.format(preclose_list))
        self.logger.debug('快照检查结果 认购认沽标识 缺少callputType_list:{}'.format(callputType_list))






#
#
#
# import pytest
# pytest.main(["-v", "-s",
#              "zmq_stock_record_testcase.py",
#              "-k test_stock_04_QuoteTradeData",
#              "--show-capture=stderr",
#              ])

if __name__ == '__main_':
    unittest.main()

