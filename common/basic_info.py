# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/17
# @Software: PyCharm


stockFutureInfo = {
    'SHK': {'lotSize': 1000, 'contractMultiplier': 1000},
    'GAH': {'lotSize': 5000, 'contractMultiplier': 5000},
    'FOS': {'lotSize': 10000, 'contractMultiplier': 10000},
    'TWR': {'lotSize': 10000, 'contractMultiplier': 10000},
    'LNK': {'lotSize': 1000, 'contractMultiplier': 1000},
    'SMC': {'lotSize': 5000, 'contractMultiplier': 5000},
    'CTB': {'lotSize': 20000, 'contractMultiplier': 20000},
    'SOA': {'lotSize': 10000, 'contractMultiplier': 10000},
    'ABC': {'lotSize': 10000, 'contractMultiplier': 10000},
    'AIA': {'lotSize': 1000, 'contractMultiplier': 1000},
    'NCL': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CDA': {'lotSize': 5000, 'contractMultiplier': 5000},
    'CRR': {'lotSize': 10000, 'contractMultiplier': 10000},
    'MIU': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CGN': {'lotSize': 10000, 'contractMultiplier': 10000},
    'BUD': {'lotSize': 1000, 'contractMultiplier': 1000},
    'SUN': {'lotSize': 2000, 'contractMultiplier': 2000},
    'MSB': {'lotSize': 10000, 'contractMultiplier': 10000},
    'COG': {'lotSize': 5000, 'contractMultiplier': 5000},
    'AAC': {'lotSize': 1000, 'contractMultiplier': 1000},
    'GAC': {'lotSize': 4000, 'contractMultiplier': 4000},
    'GWM': {'lotSize': 10000, 'contractMultiplier': 10000},
    'SNO': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CPI': {'lotSize': 1000, 'contractMultiplier': 1000},
    'TRF': {'lotSize': 50000, 'contractMultiplier': 50000},
    'CSA': {'lotSize': 5000, 'contractMultiplier': 5000},
    'A50': {'lotSize': 5000, 'contractMultiplier': 5000},
    'HCF': {'lotSize': 5000, 'contractMultiplier': 5000},
    'CHO': {'lotSize': 10000, 'contractMultiplier': 10000},
    'AMC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'EVG': {'lotSize': 2000, 'contractMultiplier': 2000},
    'MET': {'lotSize': 500, 'contractMultiplier': 500},
    'CTS': {'lotSize': 1000, 'contractMultiplier': 1000},
    'HAI': {'lotSize': 10000, 'contractMultiplier': 10000},
    'HTS': {'lotSize': 10000, 'contractMultiplier': 10000},
    'ALB': {'lotSize': 500, 'contractMultiplier': 500},
    'CKH': {'lotSize': 500, 'contractMultiplier': 500},
    'CLP': {'lotSize': 500, 'contractMultiplier': 500},
    'HKG': {'lotSize': 1000, 'contractMultiplier': 1000},
    'WHL': {'lotSize': 1000, 'contractMultiplier': 1000},
    'HKB': {'lotSize': 400, 'contractMultiplier': 400},
    'HEH': {'lotSize': 500, 'contractMultiplier': 500},
    'HSB': {'lotSize': 100, 'contractMultiplier': 100},
    'HLD': {'lotSize': 1000, 'contractMultiplier': 1000},
    'NWD': {'lotSize': 1000, 'contractMultiplier': 1000},
    'SWA': {'lotSize': 500, 'contractMultiplier': 500},
    'BEA': {'lotSize': 200, 'contractMultiplier': 200},
    'GLX': {'lotSize': 1000, 'contractMultiplier': 1000},
    'MTR': {'lotSize': 500, 'contractMultiplier': 500},
    'CIT': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CPA': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CPC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'HEX': {'lotSize': 100, 'contractMultiplier': 100},
    'LIF': {'lotSize': 2000, 'contractMultiplier': 2000},
    'COL': {'lotSize': 2000, 'contractMultiplier': 2000},
    'TCH': {'lotSize': 100, 'contractMultiplier': 100},
    'CTC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'CHU': {'lotSize': 2000, 'contractMultiplier': 2000},
    'PEC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'CNC': {'lotSize': 1000, 'contractMultiplier': 1000},
    'HNP': {'lotSize': 2000, 'contractMultiplier': 2000},
    'ACC': {'lotSize': 500, 'contractMultiplier': 500},
    'CCB': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CHT': {'lotSize': 500, 'contractMultiplier': 500},
    'CSE': {'lotSize': 500, 'contractMultiplier': 500},
    'YZC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'ICB': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CCC': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CCE': {'lotSize': 1000, 'contractMultiplier': 1000},
    'SAN': {'lotSize': 400, 'contractMultiplier': 400},
    'PAI': {'lotSize': 500, 'contractMultiplier': 500},
    'PIC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'BOC': {'lotSize': 500, 'contractMultiplier': 500},
    'ALC': {'lotSize': 2000, 'contractMultiplier': 2000},
    'CLI': {'lotSize': 1000, 'contractMultiplier': 1000},
    'ZJM': {'lotSize': 2000, 'contractMultiplier': 2000},
    'BCM': {'lotSize': 1000, 'contractMultiplier': 1000},
    'KSO': {'lotSize': 1000, 'contractMultiplier': 1000},
    'CMB': {'lotSize': 500, 'contractMultiplier': 500},
    'BCL': {'lotSize': 1000, 'contractMultiplier': 1000}
}



stockIndexFuture = {
    'HHI': {'lotSize': 50, 'contractMultiplier': 50, 'priceTick': 1, 'EsunnyCode': 'HHI', 'fluctuation': 'One index point=HK$50'},
    'HSI': {'lotSize': 50, 'contractMultiplier': 50, 'priceTick': 1, 'EsunnyCode': 'HSI', 'fluctuation': 'One index point=HK$50'},
    'MCH': {'lotSize': 10, 'contractMultiplier': 10, 'priceTick': 1, 'EsunnyCode': 'MCH', 'fluctuation': 'One index point=HK$10'},
    'MHI': {'lotSize': 10, 'contractMultiplier': 10, 'priceTick': 1, 'EsunnyCode': 'MHI', 'fluctuation': 'One index point=HK$10'},
}

rateFuture = {
    'CUS': {'lotSize': 100000, 'contractMultiplier': 100000, 'priceTick': 0.0001, 'EsunnyCode': 'CUS', 'fluctuation': ' RMB 0.0001=RMB 10'},
}

pmFuture = {
    'FEM': {'lotSize': 100, 'contractMultiplier': 100},
    'FEQ': {'lotSize': 100, 'contractMultiplier': 100},
    'GDR': {'lotSize': 1000, 'contractMultiplier': 1000},
    'GDU': {'lotSize': 1000, 'contractMultiplier': 1000},
    'LRA': {'lotSize': 5, 'contractMultiplier': 5},
    'LRC': {'lotSize': 5, 'contractMultiplier': 5},
    'LRN': {'lotSize': 1, 'contractMultiplier': 1},
    'LRP': {'lotSize': 5, 'contractMultiplier': 5},
    'LRS': {'lotSize': 1, 'contractMultiplier': 1},
    'LRZ': {'lotSize': 5, 'contractMultiplier': 5}
}


morningStarFuture = {
    # CBOT exchange
    'ZC': {'contractMultiplier': 50, 'lotSize': 5000, 'priceTick': 0.25, 'EsunnyCode': 'C', 'fluctuation': '1/4 of one cent (0.0025) per bushel = $12.50'},
    'MYM': {'contractMultiplier': 0.5, 'lotSize': 0.5, 'priceTick': 1, 'EsunnyCode': 'MYM', 'fluctuation': '1.0 index points = $0.50'},
    'ZS': {'contractMultiplier': 50, 'lotSize': 5000, 'priceTick': 0.25, 'EsunnyCode': 'S', 'fluctuation': '1/4 of one cent (0.0025) per bushel = $12.50'},
    'ZW': {'contractMultiplier': 50, 'lotSize': 5000, 'priceTick': 0.25, 'EsunnyCode': 'W', 'fluctuation': '1/4 of one cent (0.0025) per bushel = $12.50'},
    'YM': {'contractMultiplier': 5, 'lotSize': 5, 'priceTick': 1, 'EsunnyCode': 'YM', 'fluctuation': '1.00 index point = $5.00'},
    'ZB': {'contractMultiplier': 1000, 'lotSize': 100000, 'priceTick': 0.03125, 'EsunnyCode': 'ZB', 'fluctuation': '8/256 of a point = $31.25'},
    'ZF': {'contractMultiplier': 1000, 'lotSize': 100000, 'priceTick': 0.0078125, 'EsunnyCode': 'ZF', 'fluctuation': '2/256  of a point= $7.8125'},
    'ZM': {'contractMultiplier': 100, 'lotSize': 100, 'priceTick': 0.1, 'EsunnyCode': 'ZM', 'fluctuation': '0.10 per short ton = $10.00'},
    'ZN': {'contractMultiplier': 1000, 'lotSize': 100000, 'priceTick': 0.015625, 'EsunnyCode': 'ZN', 'fluctuation': '4/256  of a point= $15.625'},
    'ZT': {'contractMultiplier': 2000, 'lotSize': 200000, 'priceTick': 0.00390625, 'EsunnyCode': 'ZT', 'fluctuation': '1/256  of a point= $7.8125'},

    # CME exchange
    '6A': {'contractMultiplier': 100000, 'lotSize': 100000, 'priceTick': 0.0001, 'EsunnyCode': 'AD', 'fluctuation': '0.0001 USD per AUD increments ($10.00 USD)'},
    '6B': {'contractMultiplier': 62500, 'lotSize': 62500, 'priceTick': 0.0001, 'EsunnyCode': 'BP', 'fluctuation': '0.0001 USD per GBP increments ($6.25 USD)'},
    '6C': {'contractMultiplier': 100000, 'lotSize': 100000, 'priceTick': 0.00005, 'EsunnyCode': 'CD', 'fluctuation': '00005 USD per CAD  ($5.00 USD)'},
    'E7': {'contractMultiplier': 62500, 'lotSize': 62500, 'priceTick': 0.0001, 'EsunnyCode': 'E7', 'fluctuation': '$.00010 per euro increments ($6.25/contract)'},
    '6E': {'contractMultiplier': 125000, 'lotSize': 125000, 'priceTick': 0.00005, 'EsunnyCode': 'EC', 'fluctuation': '0.00005 per Euro increment = $6.25'},
    'ES': {'contractMultiplier': 50, 'lotSize': 50, 'priceTick': 0.25, 'EsunnyCode': 'ES', 'fluctuation': '0.25 index points = $12.50'},
    'J7': {'contractMultiplier': 6250000, 'lotSize': 6250000, 'priceTick': 0.000001, 'EsunnyCode': 'J7', 'fluctuation': '$.0000010 per Japanese yen increments ($6.25/contract)'},
    '6J': {'contractMultiplier': 12500000, 'lotSize': 12500000, 'priceTick': 0.0000005, 'EsunnyCode': 'JY', 'fluctuation': '0.0000005 per JPY increment = $6.25'},
    'MES': {'contractMultiplier': 5, 'lotSize': 5, 'priceTick': 0.25, 'EsunnyCode': 'MES', 'fluctuation': '0.25 index points = $1.25'},
    'MNQ': {'contractMultiplier': 2, 'lotSize': 2, 'priceTick': 0.25, 'EsunnyCode': 'MNQ', 'fluctuation': '0.25 index points = $0.50'},
    '6N': {'contractMultiplier': 100000, 'lotSize': 100000, 'priceTick': 0.0001, 'EsunnyCode': 'NE', 'fluctuation': '$.0001 per New Zealand dollar increments ($10.00/contract)'},
    'NIY': {'contractMultiplier': 500, 'lotSize': 500, 'priceTick': 5, 'EsunnyCode': 'NIY', 'fluctuation': '5.00 index points = ¥2500'},
    'NQ': {'contractMultiplier': 20, 'lotSize': 20, 'priceTick': 0.25, 'EsunnyCode': 'NQ', 'fluctuation': '0.25 index points = $5.00'},
    '6S': {'contractMultiplier': 125000, 'lotSize': 125000, 'priceTick': 0.0001, 'EsunnyCode': 'SF', 'fluctuation': '$.0001 per Swiss Franc increments ($12.50/contract)'},

    # COMEX exchange
    'GC': {'contractMultiplier': 100, 'lotSize': 100, 'priceTick': 0.1, 'EsunnyCode': 'GC', 'fluctuation': '0.10 per troy ounce = $10.00'},
    'HG': {'contractMultiplier': 25000, 'lotSize': 25000, 'priceTick': 0.0005, 'EsunnyCode': 'HG', 'fluctuation': '0.0005 per pound = $12.50'},
    'QC': {'contractMultiplier': 12500, 'lotSize': 12500, 'priceTick': 0.002, 'EsunnyCode': 'QC', 'fluctuation': '$0.002 per pound=$0.25'},
    'QI': {'contractMultiplier': 2500, 'lotSize': 2500, 'priceTick': 0.0125, 'EsunnyCode': 'QI', 'fluctuation': '0.0125 per troy ounce = $31.25'},
    'QO': {'contractMultiplier': 50, 'lotSize': 50, 'priceTick': 0.25, 'EsunnyCode': 'QO', 'fluctuation': '$0.25 per troy ounce= $12.50'},
    'SI': {'contractMultiplier': 5000, 'lotSize': 5000, 'priceTick': 0.005, 'EsunnyCode': 'SI', 'fluctuation': '0.005 per troy ounce = $25.00'},

    # NYMEX exchange
    'BZ': {'contractMultiplier': 1000, 'lotSize': 1000, 'priceTick': 0.01, 'EsunnyCode': 'BZ', 'fluctuation': '0.01 per barrel = $10.00'},
    'CL': {'contractMultiplier': 1000, 'lotSize': 1000, 'priceTick': 0.01, 'EsunnyCode': 'CL', 'fluctuation': '0.01 per barrel = $10.00'},
    'NG': {'contractMultiplier': 10000, 'lotSize': 10000, 'priceTick': 0.001, 'EsunnyCode': 'NG', 'fluctuation': '0.001 per MMBtu = $10.00'},
    'QM': {'contractMultiplier': 500, 'lotSize': 500, 'priceTick': 0.025, 'EsunnyCode': 'QM', 'fluctuation': '0.025 per barrel = $12.50'},

    # SGX exchange
    'CN': {'contractMultiplier': 1, 'lotSize': 1, 'priceTick': 1, 'EsunnyCode': 'CN', 'fluctuation': '1 index point (US$1)'},
    'NK': {'contractMultiplier': 500, 'lotSize': 500, 'priceTick': 5, 'EsunnyCode': 'NK', 'fluctuation': '5 index points (¥2500)'},
    'TW': {'contractMultiplier': 100, 'lotSize': 100, 'priceTick': 0.1, 'EsunnyCode': 'TW', 'fluctuation': '0.1 index points ( US$10)'}
}


allFuture = {
    'stockFutureInfo': {'productInfo': stockFutureInfo},
    'stockIndexFuture': {'productInfo': stockIndexFuture},
    'rateFuture': {'productInfo': rateFuture},
    'pmFuture': {'productInfo': pmFuture},
    'morningStarFuture': {'productInfo': morningStarFuture},
}


# 每个品种交易时间段
exchangeTradeTime = {
    "CBOT_YM" :  ["06:00", "04:15", "04:30", "05:00"],
    "CBOT_MYM" :  ["06:00", "04:15", "04:30", "05:00"],
    "CBOT_ZT" :  ["06:00", "05:00"],
    "CBOT_ZF" :  ["06:00", "05:00"],
    "CBOT_ZN" :  ["06:00", "05:00"],
    "CBOT_ZB" :  ["06:00", "05:00"],
    "CBOT_ZC" :  ["08:00", "20:45", "21:30", "02:20"],
    "CBOT_ZS" :  ["08:00", "20:45", "21:30", "02:20"],
    "CBOT_ZM" :  ["08:00", "20:45", "21:30", "02:20"],
    "CBOT_ZW" :  ["08:00", "20:45", "21:30", "02:20"],
    "CME_6A" : ["06:00","05:00"],
    "CME_6B" : ["06:00","05:00"],
    "CME_6C" : ["06:00","05:00"],
    "CME_6E" : ["06:00","05:00"],
    "CME_6J" : ["06:00","05:00"],
    "CME_6N" : ["06:00","05:00"],
    "CME_6S" : ["06:00","05:00"],
    "CME_E7" : ["06:00","05:00"],
    "CME_J7" : ["06:00","05:00"],
    "CME_NQ" : ["06:00","04:15","04:30","05:00"],
    "CME_MNQ" : ["06:00","04:15","04:30","05:00"],
    "CME_ES" : ["06:00","04:15","04:30","05:00"],
    "CME_MES" : ["06:00","04:15","04:30","05:00"],
    "CME_NIY" : ["06:00","05:00"],
    "COMEX_GC" : ["06:00","05:00"],
    "COMEX_SI" : ["06:00","05:00"],
    "COMEX_HG" : ["06:00","05:00"],
    "COMEX_QO" : ["06:00","05:00"],
    "COMEX_QI" : ["06:00","05:00"],
    "COMEX_QC" : ["06:00","05:00"],
    "HKFE_CUS" : ["17:15","03:00","08:30", "16:30"],
    "HKFE_HSI" : ["17:15","03:00","09:15","12:00","13:00","16:30"],
    "HKFE_HHI" : ["17:15","03:00","09:15","12:00","13:00","16:30"],
    "HKFE_MHI" : ["17:15","03:00","09:15","12:00","13:00","16:30"],
    "HKFE_MCH" : ["17:15","03:00","09:15","12:00","13:00","16:30"],
    "HKFE_HTI" : ["17:15","03:00","09:15","12:00","13:00","16:30"],
    "NYMEX_CL" : ["06:00","05:00"],
    "NYMEX_QM" : ["06:00","05:00"],
    "NYMEX_NG" : ["06:00","05:00"],
    "NYMEX_BZ" : ["06:00","05:00"],
    "SGX_NK" : ["14:55","05:15","07:30","14:25"],
    "SGX_TW" : ["14:15","05:15","08:45","13:45"],
    "SGX_CN" : ["17:00","05:15","09:00","16:30"],
    "HK_Stock" : ["09:30", "12:00", "13:00", "16:00"],     # 港股交易时间
    "US_Stock" : ["21:30", "04:00"],                        # 美股交易时间
    "Grey" : ["16:15", "18:30"]                         # 暗盘
}

# 每个品种的 品种类型、品种简体简称、品种英文简称
procDict = {'CUS': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '美元兑人民币', 'enSimpleName': 'CUS', 'timespin': '171500-030000 083000-163000'},
            'HHI': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': 'H股指数', 'enSimpleName': 'HHI', 'timespin': '171500-030000 091500-120000 130000-163000 084500-091500 123000-130000'},
            'HSI': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '恒生指数', 'enSimpleName': 'HSI', 'timespin': '171500-030000 091500-120000 130000-163000 084500-091500 123000-130000'},
            'MCH': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '小型H股指数', 'enSimpleName': 'MCH', 'timespin': '171500-030000 091500-120000 130000-163000 084500-091500 123000-130000'},
            'MHI': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '小型恒生指数', 'enSimpleName': 'MHI', 'timespin': '171500-030000 091500-120000 130000-163000 084500-091500 123000-130000'},
            'BZ': {'productType': 'ENERGY_CHEMICAL_FUTURE', 'cnSimpleName': '布兰特金融期货', 'enSimpleName': 'Brent Last Day Financial', 'timespin': '070000-060000'},
            'CL': {'productType': 'ENERGY_CHEMICAL_FUTURE', 'cnSimpleName': '美原油', 'enSimpleName': 'Crude Oil', 'timespin': '070000-060000'},
            'NG': {'productType': 'ENERGY_CHEMICAL_FUTURE', 'cnSimpleName': '天然气', 'enSimpleName': 'Natural Gas', 'timespin': '070000-060000'},
            'QM': {'productType': 'ENERGY_CHEMICAL_FUTURE', 'cnSimpleName': '小原油', 'enSimpleName': 'Mini Crude Oil', 'timespin': '070000-060000'},
            'CN': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': 'A50指数', 'enSimpleName': 'A50', 'timespin': '170000-044500 090000-163000'},
            'GC': {'productType': 'METAL_FUTURE', 'cnSimpleName': '美黄金', 'enSimpleName': 'Gold', 'timespin': '070000-060000'},
            'HG': {'productType': 'METAL_FUTURE', 'cnSimpleName': '美铜', 'enSimpleName': 'Copper', 'timespin': '070000-060000'},
            'QC': {'productType': 'METAL_FUTURE', 'cnSimpleName': '小型铜', 'enSimpleName': 'Mini Copper', 'timespin': '070000-060000'},
            'QI': {'productType': 'METAL_FUTURE', 'cnSimpleName': '小白银', 'enSimpleName': 'Mini Sliver', 'timespin': '070000-060000'},
            'QO': {'productType': 'METAL_FUTURE', 'cnSimpleName': '小黄金', 'enSimpleName': 'Mini Gold', 'timespin': '070000-060000'},
            'SI': {'productType': 'METAL_FUTURE', 'cnSimpleName': '美白银', 'enSimpleName': 'Sliver', 'timespin': '070000-060000'},
            'MYM': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '微型E-迷你道指', 'enSimpleName': 'MicroE-mini Dow', 'timespin': '070000-051500 053000-060000'},
            'YM': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '小道指', 'enSimpleName': 'Mini Dow', 'timespin': '070000-051500 053000-060000'},
            'ZB': {'productType': 'INTEREST_RATE_FUTURE', 'cnSimpleName': '长期美债', 'enSimpleName': 'US Bond', 'timespin': '070000-060000'},
            'ZC': {'productType': 'AGRICULTURAL_COMMODITY_FUTURE', 'cnSimpleName': '美玉米', 'enSimpleName': 'Corn', 'timespin': '090000-214500 223000-032000'},
            'ZF': {'productType': 'INTEREST_RATE_FUTURE', 'cnSimpleName': '五年美债', 'enSimpleName': 'TNote 5Y', 'timespin': '070000-060000'},
            'ZM': {'productType': 'AGRICULTURAL_COMMODITY_FUTURE', 'cnSimpleName': '美豆粕', 'enSimpleName': 'Soybean Mea', 'timespin': '090000-214500 223000-032000'},
            'ZN': {'productType': 'INTEREST_RATE_FUTURE', 'cnSimpleName': '十年美债', 'enSimpleName': 'TNote 10Y', 'timespin': '070000-060000'},
            'ZS': {'productType': 'AGRICULTURAL_COMMODITY_FUTURE', 'cnSimpleName': '美黄豆', 'enSimpleName': 'Soybean', 'timespin': '090000-214500 223000-032000'},
            'ZT': {'productType': 'INTEREST_RATE_FUTURE', 'cnSimpleName': '二年美债', 'enSimpleName': 'TNote 2Y', 'timespin': '070000-060000'},
            'ZW': {'productType': 'AGRICULTURAL_COMMODITY_FUTURE', 'cnSimpleName': '美小麦', 'enSimpleName': 'Wheat', 'timespin': '090000-214500 223000-032000'},
            '6A': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '澳元', 'enSimpleName': 'AUD', 'timespin': '070000-060000'},
            '6B': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '英镑', 'enSimpleName': 'GBP', 'timespin': '070000-060000'},
            '6C': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '加元', 'enSimpleName': 'CAD', 'timespin': '070000-060000'},
            'E7': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '小欧元', 'enSimpleName': 'Mini EUR', 'timespin': '070000-060000'},
            '6E': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '欧元', 'enSimpleName': 'EUR', 'timespin': '070000-060000'},
            '6J': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '日元', 'enSimpleName': 'JPY', 'timespin': '070000-060000'},
            '6N': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '纽元', 'enSimpleName': 'NZD', 'timespin': '070000-060000'},
            '6S': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '瑞郎', 'enSimpleName': 'CHF', 'timespin': '070000-060000'},
            'ES': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '小标普', 'enSimpleName': 'JPY', 'timespin': '070000-051500 053000-060000'},
            'J7': {'productType': 'FOREIGN_EXCHANGE_FUTURE', 'cnSimpleName': '小日元', 'enSimpleName': 'Mini JPY', 'timespin': '070000-060000'},
            'MES': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '微型E-迷你标普500', 'enSimpleName': 'MicroE-mini S&P500', 'timespin': '070000-051500 053000-060000'},
            'MNQ': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '微型E-纳斯达克100', 'enSimpleName': 'MicroE-mini Nasdaq100', 'timespin': '070000-051500 053000-060000'},
            'NIY': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '日经平均指数225', 'enSimpleName': 'Nikkei Yen', 'timespin': '070000-060000'},
            'NQ': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '小纳指', 'enSimpleName': 'Mini NASDAQ 100', 'timespin': '070000-051500 053000-060000'},
            'NK': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '日经指数', 'enSimpleName': 'Nikkei', 'timespin': '145500-044500 073000-142500'},
            'TW': {'productType': 'EQUITY_INDEX_FUTURE', 'cnSimpleName': '摩台指数', 'enSimpleName': 'MSCI Taiwan', 'timespin': '143500-020000 084500-134500'}
            }

# APP用到的42个品种
appCodelist = ["YM", "MYM", "ZT", "ZF", "ZN", "ZB", "ZC", "ZS", "ZM", "ZW", "6A", "6B", "6C", "6E", "6J", "6N", "6S", "E7", "J7", "NQ", "MNQ", "ES", "MES", "NIY", "GC", "SI", "HG", "QO", "QI", "QC", "CUS", "HSI", "HHI", "MHI", "MCH", "CL", "QM", "NG", "BZ", "NK", "TW", "CN"]



if __name__ == '__main__':
    print(stockFutureInfo.__len__())