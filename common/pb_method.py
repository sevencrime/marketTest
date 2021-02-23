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
    if peroid == 'MINUTE':
        return 1
    elif peroid == 'THREE_MIN':
        return 3
    elif peroid == 'FIVE_MIN':
        return 5
    elif peroid == 'FIFTEEN_MIN':
        return 15
    elif peroid == 'THIRTY_MIN':
        return 30
    elif peroid == 'HOUR':
        return 60
    elif peroid == 'TWO_HOUR':
        return 2*60
    elif peroid == 'FOUR_HOUR':
        return 4*60
    elif peroid == 'DAY':
        return 24*60
    elif peroid == 'WEEK':
        return 24*60*7
    elif peroid == 'MONTH':
        return 24*60*30
    else:
        logger.debug("不支持的K线频率")