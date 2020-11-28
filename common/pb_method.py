# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/6/22
# @Software: PyCharm


from pb_files.quote_type_def_pb2 import *
from pb_files.common_type_def_pb2 import *
from common.test_log.ed_log import get_log

logger = get_log()

def k_type_convert(input_str):
    if isinstance(input_str, int):
        return input_str
    try:
        return KLinePeriodType.Value(input_str)
    except:
        logger.error('Error klinePeriodType: {}'.format(input_str))


def exchange_convert(input_str):
    try:
        return ExchangeType.Value(input_str)
    except:
        logger.error('Error exchange: {}'.format(input_str))


def k_type_min(peroid):
    # 返回K线频率对应的分钟数
    if peroid == 'MINUTE' or int(peroid) == 8:
        return 1
    elif peroid == 'THREE_MIN' or int(peroid) == 10:
        return 3
    elif peroid == 'FIVE_MIN' or int(peroid) == 11:
        return 5
    elif peroid == 'FIFTEEN_MIN' or int(peroid) == 13:
        return 15
    elif peroid == 'THIRTY_MIN' or int(peroid) == 14:
        return 30
    elif peroid == 'HOUR' or int(peroid) == 15:
        return 60
    elif peroid == 'TWO_HOUR' or int(peroid) == 16:
        return 2*60
    elif peroid == 'FOUR_HOUR' or int(peroid) == 17:
        return 4*60
    elif peroid == 'DAY' or int(peroid) == 18:
        return 24*60
    elif peroid == 'WEEK' or int(peroid) == 19:
        return 24*60*7
    elif peroid == 'MONTH' or int(peroid) == 20:
        return 24*60*30
    else:
        logger.debug("不支持的K线频率")