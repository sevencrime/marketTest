# -*- coding: utf-8 -*-# !/usr/bin/python# @Author: WX# @Create Time: 2020/6/16# @Software: PyCharmimport unittestfrom py_rocksdb.market import MarketRocksDBClient, DBMethodfrom py_redis.market import MarketRedisDBClientfrom common.common_method import excel_to_listfrom common.pb_method import *from test_config import *import timefrom parameterized import parameterizedtest_instr_info = SETUP_DIR + '/test_HKFuture_instr_info.xlsx'class CheckDbData(unittest.TestCase):    @classmethod    def setUpClass(cls):        cls.rdb_client = MarketRocksDBClient(future_rocksdb_path)        cls.rdb_method = DBMethod()        cls.redis_client = MarketRedisDBClient(host=future_redis_host, port=future_redis_port)        cls.common = cls.rdb_method.common    def do_kline_check(self, kline_info, minute_info_list):        """校验K线的高开低手成交量与对应的分时数据，是否匹配"""        self.common.logger.debug('kline_info: {}'.format(kline_info))        self.common.logger.debug('minute_info_list: {}'.format(minute_info_list))        kline_open = int(kline_info['open'])        kline_close = int(kline_info['close'])        kline_high = int(kline_info['high'])        kline_low = int(kline_info['low'])        kline_vol = int(self.common.doDicEvaluate(kline_info, 'currVol'))        minute_open = int(minute_info_list[0]['open'])        minute_close = int(minute_info_list[-1]['close'])        minute_high = max([int(minute_info['high']) for minute_info in minute_info_list])        minute_low = min([int(minute_info['low']) for minute_info in minute_info_list])        minute_vol = sum([int(self.common.doDicEvaluate(minute_info, 'vol')) for minute_info in minute_info_list])        self.assertTrue(kline_open == minute_open)        self.assertTrue(kline_close == minute_close)        self.assertTrue(kline_high == minute_high)        self.assertTrue(kline_low == minute_low)        self.assertTrue(kline_vol == minute_vol)    def do_minute_check(self, minute_info, trade_data_list, exchange, code):        """校验分时线的高开低收成交量与对应的逐笔数据，是否匹配"""        self.common.logger.debug('minute_info: {}'.format(minute_info))        self.common.logger.debug('trade_data_list: {}'.format(trade_data_list))        minute_open = int(minute_info['open'])        minute_close = int(minute_info['close'])        minute_high = int(minute_info['high'])        minute_low = int(minute_info['low'])        minute_average = int(minute_info['average'])        minute_vol = int(minute_info['vol'])        minute_rf = int(self.common.doDicEvaluate(minute_info, 'riseFall'))        minute_rfr = int(self.common.doDicEvaluate(minute_info, 'rFRatio'))        minute_settle_price = int(minute_info['settlementPrice'])        trade_data_open = int(trade_data_list[0]['price'])        trade_data_close = int(trade_data_list[-1]['price'])        trade_data_high = max([int(trade_data['price']) for trade_data in trade_data_list])        trade_data_low = min([int(trade_data['price']) for trade_data in trade_data_list])        trade_data_vol = sum([int(self.common.doDicEvaluate(trade_data, 'vol')) for trade_data in trade_data_list])        minute_time = minute_info['updateDateTime']        minute_time_stamp = int(time.mktime(time.strptime(minute_time, "%Y%m%d%H%M%S")))        if exchange == 'HKFE':            # 白天盘            if self.common.getTodayHKFEStartStamp() > minute_time_stamp:                start = self.common.getTodayStamp(hours=17, minutes=15, seconds=0) - 24 * 60 * 60            # 夜盘            else:                start = self.common.getTodayStamp(hours=17, minutes=15, seconds=0)        start = start * 1000        end = minute_time_stamp * 1000        all_day_tick_list = self.redis_client.get_trade_data(exchange, code, start, end)        all_day_av_sum, all_day_vol_sum = 0, 0        for tick in all_day_tick_list:            all_day_av_sum += int(tick['price']) * int(tick['vol'])            all_day_vol_sum += int(tick['vol'])        all_day_av_price = int(all_day_av_sum / all_day_vol_sum)        self.assertTrue(minute_rf == minute_close - minute_settle_price)        self.assertTrue(minute_rfr == int((minute_rf / minute_settle_price) * 10000))        self.assertTrue(trade_data_open == minute_open)        self.assertTrue(trade_data_close == minute_close)        self.assertTrue(trade_data_high == minute_high)        self.assertTrue(trade_data_low == minute_low)        self.assertTrue(trade_data_vol == minute_vol)        self.assertTrue(all_day_av_price == minute_average)    # @parameterized.expand(excel_to_list(test_instr_info))    def test_001_RedisCheckMinute(self, exchange=HK_exchange, instr_code=HK_code1):        """检查最近一个小时里面的分时数据"""        peroid_type = 'HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        recent_time_stamp = recent_time_stamp_list[-1]        # recent_time_stamp = 1600251300        minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)        minute_info_list = self.rdb_client.get_multi_value(minute_keys)        for minute_info in minute_info_list:            minute_time = minute_info['updateDateTime']            minute_time_stamp = time.mktime(time.strptime(minute_time, "%Y%m%d%H%M%S")) * 1000            start, end = self.redis_client.get_minute_interval(minute_time_stamp)            trade_data_list = self.redis_client.get_trade_data(exchange, instr_code, start, end)            self.do_minute_check(minute_info=minute_info, trade_data_list=trade_data_list, exchange=exchange, code=instr_code)    @parameterized.expand(excel_to_list(test_instr_info))    def test_001_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查3分钟K线的数据"""        peroid_type = 'THREE_MIN'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_002_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查5分钟K线的数据"""        peroid_type = 'FIVE_MIN'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_003_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查15分钟K线的数据"""        peroid_type = 'FIFTEEN_MIN'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_004_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查30分钟K线的数据"""        peroid_type = 'THIRTY_MIN'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_005_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查1小时K线的数据"""        peroid_type = 'HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_006_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查2小时K线的数据"""        peroid_type = 'TWO_HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_007_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查4小时K线的数据"""        peroid_type = 'FOUR_HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_008_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查日K线的数据"""        peroid_type = 'DAY'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_009_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查周K线的数据"""        peroid_type = 'WEEK'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_010_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查月K线的数据"""        peroid_type = 'MONTH'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_time_stamp_list = self.rdb_method.get_recent_stamp_list(peroid_type_int, exchange_int)        self.assertTrue(recent_time_stamp_list.__len__() > 0)        for recent_time_stamp in recent_time_stamp_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(recent_time_stamp))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys(instr_code=instr_code, exchange=exchange_int, peroid_type=peroid_type_int, kline_key_stamp=recent_time_stamp)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_011_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查非连续区间组成的k线: 30分钟K线的数据"""        peroid_type = 'THIRTY_MIN'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_interval_list = self.rdb_method.get_recent_interval_list(peroid_type_int, exchange_int)        self.assertTrue(recent_interval_list.__len__() > 0)        for start, end in recent_interval_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(end))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys_by_time(instr_code=instr_code, exchange=exchange_int, start_time_stamp=start, end_time_stamp=end)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_012_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查非连续区间组成的k线: 1小时K线的数据"""        peroid_type = 'HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_interval_list = self.rdb_method.get_recent_interval_list(peroid_type_int, exchange_int)        self.assertTrue(recent_interval_list.__len__() > 0)        for start, end in recent_interval_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(end))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys_by_time(instr_code=instr_code, exchange=exchange_int, start_time_stamp=start, end_time_stamp=end)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_013_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code1):        """检查非连续区间组成的k线: 2小时K线的数据"""        peroid_type = 'TWO_HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_interval_list = self.rdb_method.get_recent_interval_list(peroid_type_int, exchange_int)        self.assertTrue(recent_interval_list.__len__() > 0)        for start, end in recent_interval_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(end))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys_by_time(instr_code=instr_code, exchange=exchange_int, start_time_stamp=start, end_time_stamp=end)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)    @parameterized.expand(excel_to_list(test_instr_info))    def test_014_RocksDBCheckKline(self, exchange=HK_exchange, instr_code=HK_code5):        """检查非连续区间组成的k线: 4小时K线的数据"""        peroid_type = 'FOUR_HOUR'        peroid_type_int = k_type_convert(peroid_type)        exchange_int = exchange_convert(exchange)        recent_interval_list = self.rdb_method.get_recent_interval_list(peroid_type_int, exchange_int)        self.assertTrue(recent_interval_list.__len__() > 0)        for start, end in recent_interval_list:            kline_key = ('KLINE_{}_{}_{}_{}'.format(exchange_int, instr_code, peroid_type_int, time.strftime("%Y%m%d%H%M%S", time.localtime(end))))            self.common.logger.debug('kline_key: {}'.format(kline_key))            kline_info = self.rdb_client.get_single_value(kline_key)            minute_keys = self.rdb_method.get_minute_keys_by_time(instr_code=instr_code, exchange=exchange_int, start_time_stamp=start, end_time_stamp=end)            minute_info_list = self.rdb_client.get_multi_value(minute_keys)            self.do_kline_check(kline_info=kline_info, minute_info_list=minute_info_list)if __name__ == '__main__':    rb = CheckDbData()    # rb.get_recent_time(10)    rb.test_001_RocksDBCheckKline()