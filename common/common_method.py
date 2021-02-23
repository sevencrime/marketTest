# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/16
# @Software: PyCharm

from string import digits
import time
import datetime
import asyncio
import threading
import json

import xlrd
from pynput import keyboard

from common.basic_info import *
from common.pb_method import k_type_min
from common.test_log.ed_log import get_log
from common.basic_info import *
from pb_files.quote_type_def_pb2 import KLinePeriodType
from test_config import *


def excel_to_list(file_name):
    # 从Excel中读取参数
    get_list = []
    workbook = xlrd.open_workbook(file_name)
    sheet = workbook.sheet_by_index(0)
    for row in range(0, sheet.nrows):  # 从第一行开始取值，取到最后一行
        get_list.append(sheet.row_values(row))  # 将每行的数据存入大列表中，每行数据都是一个list
    return get_list


class MyThread(threading.Thread):
    def __init__(self, func, args):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)


class KeyboardListen(object):
    def __new__(cls, *args, **kwargs):
        # 单例模式
        if not hasattr(cls, 'instance'):
            cls.instance = super(KeyboardListen, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.key = None
        self.input_num = 0
        if sys.platform == 'win32':
            print('Please wait 10 seconds for keyboard listening to init in windows system.')

    def on_press(self, key):
        pass

    def on_release(self, key):
        try:
            # 因可能输入键不是主键盘信息，则char无值，此时取key.vk值替代
            self.key = key.char
            if self.key == None:
                self.key = str(key.vk)
            self.input_num += 1
        except Exception as e:
            print('Input error, please check: {}'.format(e))
            self.key = None

    def listen(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def start_listen(self):
        t1 = MyThread(func=self.listen, args=())
        t1.setDaemon(True)
        t1.start()  # 启动监控线程


class Common(object):
    def __new__(cls, *args, **kwargs):
        # 单例模式
        if not hasattr(cls, 'instance'):
            cls.instance = super(Common, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.logger = get_log()

    def getCurrentDayTimeStampInfo(self):
        now = time.localtime()
        todayBeginTimeStr = '%d.%d.%d_00:00:00' % (now.tm_year, now.tm_mon, now.tm_mday)
        todayBeginTimeStamp = int(time.mktime(time.strptime(todayBeginTimeStr, '%Y.%m.%d_%H:%M:%S')))
        todayEndTimeStamp = todayBeginTimeStamp + 60 * 60 * 24 - 1
        return {'todayBeginTimeStamp': todayBeginTimeStamp, 'todayEndTimeStamp': todayEndTimeStamp}

    def isTimeInToday(self, checkTime):
        currentDayTimeStampInfo = self.getCurrentDayTimeStampInfo()
        todayBeginTimeStamp = currentDayTimeStampInfo['todayBeginTimeStamp']
        todayEndTimeStamp = currentDayTimeStampInfo['todayEndTimeStamp']
        checkTime = int(str(checkTime)[:10])
        if checkTime >= todayBeginTimeStamp and checkTime < todayEndTimeStamp:
            return True
        else:
            return False

    def inToday(self, checkDay):
        today = str(datetime.date.today())
        if checkDay.replace('-0', '-', 2) == today.replace('-0', '-', 2):
            return True
        else:
            return False

    def inYesterday(self, checkDay):
        today = datetime.date.today()
        yesterday = str(today - datetime.timedelta(days=1))
        if checkDay.replace('-0', '-', 2) == yesterday.replace('-0', '-', 2):
            return True
        else:
            return False

    def isTomorrow(self, checkDay):
        today = datetime.date.today()
        yesterday = str(today + datetime.timedelta(days=1))
        if checkDay.replace('-0', '-', 2) == yesterday.replace('-0', '-', 2):
            return True
        else:
            return False

    def getYesterDayStampInfo(self):        # 为morningstar量身设计的时间校验方法
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        yesterday_start_time = int(time.mktime(time.strptime(str(yesterday), '%Y-%m-%d')))
        yesterday_end_time = (int(time.mktime(time.strptime(str(today), '%Y-%m-%d'))) - 1)
        return {'yesterDayBeginTimeStamp': yesterday_start_time, 'yesterDayEndTimeStamp': yesterday_end_time}

    def isTimeInYesterday(self, checkTime):
        YesterDayStampInfo = self.getYesterDayStampInfo()
        yesterBeginTimeStamp = YesterDayStampInfo['yesterDayBeginTimeStamp']
        yesterEndTimeStamp = YesterDayStampInfo['yesterDayEndTimeStamp']
        checkTime = int(str(checkTime)[:10])
        if checkTime >= yesterBeginTimeStamp and checkTime < yesterEndTimeStamp:
            return True
        else:
            return False

    def getTwelveHourStamp(self):
        today = datetime.date.today()
        todayhour=datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        twelvehour = todayhour + datetime.timedelta(hours=12)
        twelvehourstamp=int(time.mktime(time.strptime(str(twelvehour), '%Y-%m-%d %H:%M:%S')))
        return twelvehourstamp

    def getTodayHKFEStartStamp(self):
        today = datetime.date.today()
        todayhour = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        start = todayhour + datetime.timedelta(hours=17, minutes=15)
        todayHKFEStartStamp = int(time.mktime(time.strptime(str(start), '%Y-%m-%d %H:%M:%S')))
        return todayHKFEStartStamp

    def getTodayHKFEEndStamp(self):
        today = datetime.date.today()
        todayhour = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        start = todayhour + datetime.timedelta(hours=16, minutes=30)
        todayHKFEEndStamp = int(time.mktime(time.strptime(str(start), '%Y-%m-%d %H:%M:%S')))
        return todayHKFEEndStamp

    def getNextHKFEStartStamp(self):
        today = datetime.date.today()
        todayhour = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        start = todayhour + datetime.timedelta(hours=17, minutes=15)
        # 白天盘
        if self.getTodayHKFEStartStamp() > int(time.time()):
            nextHKFEStartStamp = int(time.mktime(time.strptime(str(start), '%Y-%m-%d %H:%M:%S')))
        # 夜盘
        else:
            nextHKFEStartStamp = int(time.mktime(time.strptime(str(start), '%Y-%m-%d %H:%M:%S'))) + 24 * 60 * 60
        return nextHKFEStartStamp

    def getTodayStamp(self, hours, minutes, seconds):
        today = datetime.date.today()
        today_time = datetime.datetime(today.year, today.month, today.day, hours, minutes, seconds)
        get_stamp = int(time.mktime(time.strptime(str(today_time), '%Y-%m-%d %H:%M:%S')))
        return get_stamp

    def changeStrTimeToStamp(self, input_str):
        input_str = str(input_str)[:-2]
        time_array = time.strptime(input_str, '%Y%m%d%H%M')
        return int(time.mktime(time_array) * 1000)

    def doDicEvaluate(self, dic, key, type=0):
        # type 表示key的类型，0表示整形（如果没找到对应的key则返回0），1表示字符串（如果没找到对应的key则返回''），2表示列表（如果没找到对应的key则返回[]），3表示返回None
        if key in dic.keys():
            return dic[key]
        else:
            if type == 0:
                return 0
            elif type == 1:
                return ''
            elif type == 2:
                return []
            elif type == 3:
                return None
            elif type == 4:
                return False

    def searchDicKV(self, dic, keyword):
        if isinstance(dic, dict):
            for x in range(len(dic)):
                temp_key = list(dic.keys())[x]
                temp_value = dic[temp_key]
                if temp_key == keyword:
                    return_value = temp_value
                    return return_value
                return_value = self.searchDicKV(temp_value, keyword)
                if return_value != None:
                    return return_value
        elif isinstance(dic, list):
            for d in dic:
                return self.searchDicKV(d, keyword)

    def searchDict_By_Value(self, dic, value):
        """ 通过value寻找dict """
        if isinstance(dic, dict):
            for x in range(len(dic)):
                temp_key = list(dic.keys())[x]
                temp_value = dic[temp_key]
                if temp_value == value:
                    return dic
                # 递归寻找下一层
                return_value = self.searchDict_By_Value(temp_value, value)
                if return_value != None:
                    return return_value
        elif isinstance(dic, list):
            for _d in dic:
                return_dic = self.searchDict_By_Value(_d, value)
                if return_dic:
                    return return_dic


    def fixIntNum(self, num, length):
        if str(num).__len__() < length:
            num = '0' + str(num)
            self.fixIntNum(num, length)
        return num

    def isInTradeTime(self, checkTimeStamp, tradeTimeList):
        for timeDic in tradeTimeList:
            start = str(self.fixIntNum(timeDic['start'], 6))
            end = str(self.fixIntNum(timeDic['end'], 6))
            now = time.localtime()
            timeStartStr = '%d.%d.%d_%s' % (now.tm_year, now.tm_mon, now.tm_mday, start)
            timeEndStr = '%d.%d.%d_%s' % (now.tm_year, now.tm_mon, now.tm_mday, end)
            timeStartStamp = int(time.mktime(time.strptime(timeStartStr, '%Y.%m.%d_%H%M%S')))
            timeEndStamp = int(time.mktime(time.strptime(timeEndStr, '%Y.%m.%d_%H%M%S')))
            if checkTimeStamp >= timeStartStamp and checkTimeStamp < timeEndStamp:
                return True
        return False

    def isDataBeforeSubscribe(self, exchange, is_delay, req_source_time, subscribe_time_stamp, tolerance_time=0):
        # 判断数据是否是前数据
        # 毫秒级别对比
        # 外期的source时间比北京时间晚12小时
        # if exchange == 'HKFE':      # 港期
        if ((not is_delay) and (int(int(req_source_time) / (pow(10, 6))) < (subscribe_time_stamp + tolerance_time)))\
            or \
                ((is_delay) and (int(int(req_source_time) / (pow(10, 6))) < (subscribe_time_stamp + tolerance_time - delay_minute * 60 * 1000))):
            return True
        # else:       # 外期
        #     if ((not is_delay) and (int(int(req_source_time) / (pow(10, 6)) + 12 * 60 * 60 * 1000) < (subscribe_time_stamp + tolerance_time))) \
        #             or \
        #             ((is_delay) and (int(int(req_source_time) / (pow(10, 6)) + 12 * 60 * 60 * 1000) < (subscribe_time_stamp + tolerance_time - delay_minute * 60 * 1000))):
        #         return True
        return False

    def getFutureBaseInfo(self, code):
        futureTypeList = allFuture.keys()
        for futureType in futureTypeList:
            if code in allFuture[futureType]['productInfo'].keys():
                lotSize = allFuture[futureType]['productInfo'][code]['lotSize']
                contractMultiplier = allFuture[futureType]['productInfo'][code]['contractMultiplier']
                EsunnyCode = allFuture[futureType]['productInfo'][code]['EsunnyCode']
                priceTick = allFuture[futureType]['productInfo'][code]['priceTick']
                fluctuation = allFuture[futureType]['productInfo'][code]['fluctuation']
                return {'lotSize': lotSize, 'contractMultiplier': contractMultiplier, 'EsunnyCode': EsunnyCode, 'priceTick': priceTick, 'fluctuation': fluctuation}
        return None

    def getNewLoop(self):
        if sys.platform == 'win32':
            new_loop = asyncio.ProactorEventLoop()
        else:
            new_loop = asyncio.new_event_loop()
        return new_loop

    def isJson(self, myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    def compareSubData(self, data1, data2):
        # used by delay market subscribing test comparing
        # data2 should be as list type. This function will return if data1 in data2
        data1['commonInfo'].pop('publisherRecvTime')
        data1['commonInfo'].pop('publisherSendTime')
        data1['commonInfo'].pop('collectorRecvTime')
        data1['commonInfo'].pop('collectorSendTime')
        # 如果是静态数据，因可能是采集器写入的update time，则不校验这个字段
        if 'updateTimestamp' in data1.keys():
            data1.pop('updateTimestamp')
        for data_check in data2:
            data_check['commonInfo'].pop('publisherRecvTime')
            data_check['commonInfo'].pop('publisherSendTime')
            data_check['commonInfo'].pop('collectorRecvTime')
            data_check['commonInfo'].pop('collectorSendTime')
            if 'updateTimestamp' in data_check.keys():
                data_check.pop('updateTimestamp')
            if data1 == data_check:
                return True
        self.logger.debug('Subscribe data comparing not match!\ndata1: {}\ndata2: {}'.format(data1, data2))
        return False

    def compareKData(self, data1, data2):
        # used by delay market subscribing test comparing, 校验分时、K线
        # data2 should be as list type. This function will return if data1 in data2
        for data_check in data2:
            if data1 == data_check:
                return True
        self.logger.debug('Subscribe data comparing not match!\ndata1: {}\ndata2: {}'.format(data1, data2))
        return False

    def checkFrequence(self, data_list, frequence):
        record_time = None
        count_num = 0
        if frequence in [0, None]:
            frequence = 9999  # 程序默认不限制
        for data in data_list:
            if 'tradeTick' in data.keys():
                source_time = int(int(self.searchDicKV(data, 'time')) / pow(10, 9))
            elif 'queueBuy' in data.keys():
                source_time = max(int(self.doDicEvaluate(data, 'timestampBuy', 0)),
                                  int(self.doDicEvaluate(data, 'timestampSell', 0)))
            else:
                source_time = int(int(self.searchDicKV(data, 'sourceUpdateTime')) / pow(10, 9))
            if record_time == None:
                record_time = source_time
                count_num = 1
            else:
                if source_time - record_time >= 1:  # 间隔时间大于一秒时
                    if count_num <= frequence + 1:  # 因sourcetime与本地时间可能存在误差，此处加一个误差
                        record_time = source_time
                        count_num = 1
                    else:
                        self.logger.debug('checkFrequence failed:{}'.format(data))
                        return False
                else:
                    count_num += 1
        return True

    def to_json(self, data):
        # json 格式化输出
        from json import JSONEncoder
        return json.dumps(data, sort_keys=False, indent=4, separators=(', ', ': '), cls=JSONEncoder, ensure_ascii=False)

    def current_date(self, x=0, datestr=None, dateformat="%Y%m%d"):
        '''
        获取时间字符串
        x : 距离当前时间的秒数
        datestr : 格式化后的时间字符
        dateformat : 返回的时间格式
        return : 格式化后的时间字符串
        '''
        if datestr:
            t = time.strptime(datestr, "%Y%m%d")
        else:
            t = time.localtime(int(time.time()) - int(x))

        return time.strftime(dateformat, t)

    def use_logging_trade_status(func):
        def wrapper(self, *args, **kwargs):
            if args.__len__() == 1:     # 如果code为空(股票), 添加一个空字符, 防止数据越界
                args += ("", )
            status = func(self, *args, **kwargs)
            if status == True:
                self.logger.debug("{}-{} 交易中".format(args[0], args[1]))
            elif status == False:
                self.logger.debug("{}-{} 休市中".format(args[0], args[1]))

            return status

        return wrapper

    @use_logging_trade_status
    def check_trade_status(self, exchange, code=None, curTime=None, peroidType="MINUTE", isgetTime=False, 
                           _fmt="%Y%m%d%H%M%S", _isSummerTime=isSummerTime, sub_quote_type=sub_quote_type):
        self.check_trade_status_sub(exchange=exchange, code=code, curTime=curTime, peroidType="MINUTE", isgetTime=False,
                           _fmt="%Y%m%d%H%M%S", _isSummerTime=isSummerTime, sub_quote_type=sub_quote_type)

    def check_trade_status_sub(self, exchange, code=None, curTime=None, peroidType="MINUTE", isgetTime=False,
                           _fmt="%Y%m%d%H%M%S", _isSummerTime=isSummerTime, sub_quote_type=sub_quote_type):
        '''
        判断品种在 curTime 时是否交易时间
        !!! 假期无法判断
        合约时间表 : basic_info.exchangeTradeTime

        :param exchange: 交易所
        :param code:    合约代码
        :param curTime: 返回日期所对应交易日, 默认当日
        :param peroidType: K线频率, 默认1分钟, 暂不支持日K线以上
        :param isgetTime: 返回curTime所对应的交易时间段列表
        :param _fmt: 返回list的时间格式, 默认%Y%m%d%H%M%S
        :param _isSummerTime: 控制夏令时/冬令时, 配置修改
        :return: bool or list
        '''

        # 处理coed
        if code:
            if "main" in code:
                code = code.replace("main", "")
            # 去掉code中的数字, 只保留品种代码
            code_lit = code[2:]
            code_lit = code_lit.translate(str.maketrans('', '', digits))
            code = code[:2] + code_lit
        else:
            code = ""

        # 获取对应品种的交易时间
        try:
            if exchange in ["ASE", "NYSE", "NASDAQ", "BATS", "IEX"]:    # 如果是美股,则获取美股交易时间
                trade_time = exchangeTradeTime["US_Stock"]      
            elif exchange == "Grey":                                    # 暗盘时间
                trade_time = exchangeTradeTime["Grey"]      
            elif exchange == "SEHK":
                trade_time = exchangeTradeTime["HK_Stock"]      
            else:
                trade_time = exchangeTradeTime["{}_{}".format(exchange, code)]
        except Exception as e:
            self.logger.error("没有此合约")
            raise e

        # 冬令时加一天
        if exchange not in ["HKFE", "SGX", "SEHK", "Grey"]:
            if not _isSummerTime:
                # 冬令时, 加一个小时
                flag_tradeTime = []
                for _time in trade_time:
                    t = datetime.datetime.strptime(str(datetime.datetime.now().date()) + _time, '%Y-%m-%d%H:%M')
                    # 冬令时加一个小时
                    t = t + datetime.timedelta(hours=1)
                    flag_tradeTime.append(datetime.datetime.strftime(t, "%H%M"))
                trade_time = flag_tradeTime

        strptimeFunc = lambda x, fmt="%Y%m%d%H%M%S":  datetime.datetime.strptime(x, fmt)    # str 转 detetime
        strftimeFunc = lambda x, fmt="%Y-%m-%d": datetime.datetime.strftime(x, fmt)  # datetime 转 str

        # 获取请求的时间
        if not curTime:
            curTime = datetime.datetime.now()  # 当前时间
            curDate = strftimeFunc(curTime)
        else:
            # 全掉curTime 中的字符, 保留%Y%m%d%H%M%S格式
            curTime = ''.join(e for e in curTime if e.isalnum())
            try:
                assert len(curTime) >= 8
                if len(curTime) > 14:
                    curTime = curTime[:14]
                # 后面添0, 构造成%Y%m%d%H%M%S
                curTime += "0" * int(14 - len(curTime))
            except AssertionError:
                self.logger.debug("传入时间 {} 错误".format(curTime))
                raise AssertionError

            curTime = strptimeFunc(curTime)
            curDate = strftimeFunc(curTime)

        if isinstance(peroidType, int):
            peroidType = KLinePeriodType.Name(peroidType)
        if k_type_min(peroidType) >= 24*60:
            return curDate

        ######################### 下面循环, 构造curTime所对应的交易日, 并判断 #############################
        _curTime = curTime      # 赋值一个变量
        isFlag = True   # 保证只能减少一个交易日
        tradeTimeList = []
        remainTime = None 
        us_start_time = None    # 记录美股竞价时间
        grey_start_time = None  # 记录暗盘
        for i in range(0, len(trade_time), 2):
            _temp = trade_time[i: i + 2]

            # 处理交易时间中的符号, 防止时间中出现符号
            _temp[0] = ''.join(e for e in _temp[0] if e.isalnum())
            _temp[1] = ''.join(e for e in _temp[1] if e.isalnum())

            # 范围时间
            startTime = strptimeFunc(curDate + _temp[0], '%Y-%m-%d%H%M')
            endTime = strptimeFunc(curDate + _temp[1], '%Y-%m-%d%H%M')

            # 延时行情(判断交易状态时), 每个时间段加15分钟
            if sub_quote_type == "DELAY_QUOTE_MSG" and not isgetTime:
                startTime = startTime + datetime.timedelta(minutes=15)
                endTime = endTime + datetime.timedelta(minutes=15)


            # 当开始时间大于发起请求的时间, 说明是上一个交易日时间
            if startTime > _curTime and isFlag:
                isFlag = False
                # startTime 小于 endTime, 代表是同一天, 一起减一个交易日
                if startTime < endTime :
                    endTime = endTime - datetime.timedelta(days=1)
                    curDate = strftimeFunc(strptimeFunc(curDate, '%Y-%m-%d') - datetime.timedelta(days=1))
                    _curTime = _curTime - datetime.timedelta(days=1)

                # startTime减一个交易日
                startTime = startTime - datetime.timedelta(days=1)

                if i == 0:
                    # 当周一请求时候, 遇到周六, 周日, 减少一天
                    while startTime.weekday() in [5, 6]:
                        startTime = startTime - datetime.timedelta(days=1)
                        endTime = endTime - datetime.timedelta(days=1)
                        curDate = strftimeFunc(strptimeFunc(curDate, '%Y-%m-%d') - datetime.timedelta(days=1))

            # 当开始时间段大于结束时间段时, 代表endTime是第二天, endTime增加一个交易
            if startTime > endTime:
                # 加一天
                endTime = endTime + datetime.timedelta(days=1)
                # curDate也增加一个交易日, 目的是第二次循环时, 保留最新的一天
                curDate = strftimeFunc(strptimeFunc(curDate, '%Y-%m-%d') + datetime.timedelta(days=1))
                _curTime = _curTime + datetime.timedelta(days=1)

            # 当周五请求时, 判断第二个时间段是周六开盘还是下周一开盘
            if tradeTimeList:
                try:
                    if int(strftimeFunc(strptimeFunc(tradeTimeList[0], _fmt), fmt="%H")) > 12:
                        while startTime.weekday() in [5, 6]:
                            startTime = startTime + datetime.timedelta(days=1)
                            endTime = endTime + datetime.timedelta(days=1)
                            curDate = strftimeFunc(strptimeFunc(curDate, '%Y-%m-%d') + datetime.timedelta(days=1))
                except Exception as e:
                    if k_type_min(peroidType) < 24*60: 
                        raise e

            # 分时和K线最小单位为1分钟, 故第一根数据的时间加一分钟
            # tradeTimeList.append(strftimeFunc(startTime + datetime.timedelta(minutes=1), "%Y%m%d%H%M%S"))   
            # tradeTimeList.append(strftimeFunc(endTime, "%Y%m%d%H%M%S"))

            # _fmt = "%Y%m%d%H%M%S"
            _start = startTime      # copy一个新变量, 防止时间改变
            _end = endTime          # copy一个新变量, 防止时间改变

            # 如果是获取美股的K线时间, 开始时间需变成整点, 因为美股的K线从盘前竞价开始算
            if isgetTime and exchange in ["ASE", "NYSE", "NASDAQ", "BATS", "IEX"]:
                pass
                # us_start_time = _start      
                # _start -= datetime.timedelta(hours=5.5)     # 美股K线从17点(竞价)开始计算
            elif isgetTime and exchange == "Grey":
                grey_start_time 

            while _start <= _end:
                # 增加超过时间                
                if remainTime:
                    _start += remainTime
                    if _start < _end:
                        tradeTimeList.append(strftimeFunc(_start, _fmt))
                    else:
                        tradeTimeList.append(strftimeFunc(_end, _fmt))

                    remainTime = None

                _start += datetime.timedelta(minutes=k_type_min(peroidType))

                if _start > _end:
                    remainTime = _start - _end    # 记录剩余时间
                    break

                if us_start_time:
                    if _start >= us_start_time:
                        tradeTimeList.append(strftimeFunc(_start, _fmt))
                else:
                    tradeTimeList.append(strftimeFunc(_start, _fmt))


            # 添加交易日收盘时刻K线
            if i+2 == len(trade_time) and strptimeFunc(tradeTimeList[-1], _fmt) != _end:
                tradeTimeList.append(strftimeFunc(_end, _fmt))

            if tradeTimeList:
                # 当交易日的开盘时间为周末时, 是休市
                if strptimeFunc(tradeTimeList[0], _fmt).weekday() in [5, 6]:
                    # print("周六周日休市")
                    return False

            if isgetTime:
                continue
            else:
                # 判断当前时间是否在范围时间内
                if curTime >= startTime and curTime <= endTime:
                    return True

        if isgetTime:
            return tradeTimeList

        return False


    def get_fiveDays(self, exchange, code=None, curTime=None, is_init=None):
        '''获取五个交易日时间, 用于五日分时校验 (无法判断节假日)'''
        fiveDaysList = []
        strptimeFunc = lambda x, fmt="%Y%m%d%H%M%S":  datetime.datetime.strptime(x, fmt)    # str 转 detetime
        strftimeFunc = lambda x, fmt="%Y%m%d": datetime.datetime.strftime(x, fmt)  # datetime 转 str

        # 获取请求的时间
        if not curTime:
            curTime = datetime.datetime.now()  # 当前时间
        else:
            # 去掉掉curTime 中的字符, 保留%Y%m%d%H%M%S格式
            curTime = ''.join(e for e in str(curTime) if e.isalnum())
            try:
                assert len(curTime) >= 8
                if len(curTime) > 14:
                    curTime = curTime[:14]
                # 后面添0, 构造成%Y%m%d%H%M%S
                curTime += "0" * int(14 - len(curTime))
            except AssertionError:
                self.logger.debug("传入时间 {} 错误".format(curTime))
                raise AssertionError

            curTime = strptimeFunc(curTime)

        _tradeTime = self.check_trade_status(exchange, code, isgetTime=True, curTime=str(curTime))

        if is_init and strftimeFunc(curTime, fmt="%H%M%S") < _tradeTime[0][8:]:
            curTime += datetime.timedelta(days=1)

        _tradeTime = self.check_trade_status(exchange, code, isgetTime=True, curTime=str(curTime))

        if exchange in ["HKFE"]:
            days = strptimeFunc(_tradeTime[-1])
        else:
            days = strptimeFunc(_tradeTime[0])

        n = 0
        for i in range(5):
            _d = days - datetime.timedelta(days=n)

            # 如果周末, 则持续减少一天
            while _d.weekday() in [5, 6]:
                n += 1
                _d = _d - datetime.timedelta(days=1)

            fiveDaysList.append(strftimeFunc(_d))
            n += 1 

        return list(reversed(fiveDaysList))


    def to_LowerCamelcase(self, snake_str):
        # Snake Case转换为Lower camelcase, 针对protobuf标准输出格式
        # Og: product_group ==> productGroup
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def getProc(self, code):
        # 获得每个品种的 品种类型、品种简体简称、品种英文简称
        return procDict[code]

    def new_round(self, _float, _len=0):
        # 四舍五入, 解决round 遇5不进问题
        if isinstance(_float, float):
            if str(_float)[::-1].find('.') <= _len:
                return(_float)
            if str(_float)[-1] == '5':
                return(round(float(str(_float)[:-1]+'6'), _len))
            else:
                return(round(_float, _len))
        else:
            return(round(_float, _len))

    def formatStamp(self, timestamp, fmt="%Y-%m-%d %H:%M:%S.%f"):
        timestamp = int(str(timestamp)[:13])
        d = datetime.datetime.fromtimestamp(timestamp/1000)
        return d.strftime(fmt)

if __name__ == '__main__':
    now = time.localtime()

    common = Common()
    # a = common.check_trade_status("SEHK", "00700", isgetTime=True)
    # print(a.__len__())

    print(common.get_fiveDays("SEHK", "00700", is_init=True, curTime=20210206095500))
