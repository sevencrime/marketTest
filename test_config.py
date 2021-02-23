# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/14
# @Software: PyCharm

import os
import sys

# SIT 为QA环境， PRD 为生产环境
env = 'SIT'
isSummerTime = False    # True:夏令时, False:冬令时
sub_quote_type = "DELAY_QUOTE_MSG"   # REAL_QUOTE_MSG: 实时行情, DELAY_QUOTE_MSG: 延时行情

"""Returns the base application path."""
if hasattr(sys, 'frozen'):
    # Handles PyInstaller
    SETUP_DIR = os.path.dirname(sys.executable)
else:
    SETUP_DIR = os.path.dirname(__file__)

if sys.platform == 'win32':
    txt_file_save_folder = SETUP_DIR + '\\zmq_py3\\zmq_save_files\\Txt\\'
    db_save_folder = SETUP_DIR + '\\zmq_py3\\zmq_save_files\\db\\'
    report_folder = SETUP_DIR + '\\report\\'
    log_path = SETUP_DIR + '\\common\\test_log\\'
    allure_result_folder = report_folder + 'allure\\allure_result\\'
    allure_report_folder = report_folder + 'allure\\allure_report\\'
else:
    txt_file_save_folder = SETUP_DIR + '/zmq_py3/zmq_save_files/Txt/'
    db_save_folder = SETUP_DIR + '/zmq_py3/zmq_save_files/db/'
    report_folder = SETUP_DIR + '/report/'
    log_path = SETUP_DIR + '/common/test_log/'
    allure_result_folder = report_folder + 'allure/allure_result/'
    allure_report_folder = report_folder + 'allure/allure_report/'
    future_rocksdb_path = '/mnt/future_rocksdb'      # 需加载映射磁盘
    stock_rocksdb_path = '/mnt/stock_rocksdb'      # 需加载映射磁盘

pub_table = 'pub_sub_info'
deal_table = 'deal_router_info'
subscribe_table = 'subscribe_info'
time_analysis_base_table = 'time_analysis_base_info'
statistical_analysis_table = 'statistical_analysis'
cal_table = 'cal_sub_info'
sql_assemble_num = 500  # sqlite单条插入数值最多为500个
sql_transaction_num = 20    # 为了减少执行sql的次数，此处优化为使用事务一次性批量插入: 此参数表示事务里执行的sql命令个数

# log_type = 'getlog'
log_type = 'onlyconsole'

delay_minute = 15   # 行情的时间
tolerance_time = 0  # 容忍误差时间 ms


###############期货###################
HK_exchange = 'HKFE'
HK_code1 = 'MHImain'
HK_code2 = 'HHI2102'
HK_code3 = 'HSI2102'
HK_code4 = 'HTImain'
HK_code5 = 'HSI2102'
HK_code6 = 'MHI2102'

HK_main1 = "CUSmain"
HK_main2 = "HSImain"
HK_main3 = "HHImain"
HK_main4 = "MHImain"
HK_main5 = "MCHmain"
HK_main6 = "HTImain"

NYMEX_exchange = 'NYMEX'
NYMEX_code1 = "CLmain"
NYMEX_code2 = "QMmain"
NYMEX_code3 = "NGmain"
NYMEX_code4 = "BZmain"

COMEX_exchange = 'COMEX'
COMEX_code1 = "GCmain"
COMEX_code2 = "SImain"
COMEX_code3 = "HGmain"
COMEX_code4 = "QOmain"
COMEX_code5 = "QImain"
COMEX_code6 = "QCmain"

CBOT_exchange = 'CBOT'
CBOT_code1 = "ZCmain"
CBOT_code2 = "ZSmain"
CBOT_code3 = "ZMmain"
CBOT_code4 = "ZWmain"
CBOT_code5 = "ZTmain"
CBOT_code6 = "ZFmain"
CBOT_code7 = "ZNmain"
CBOT_code8 = "ZBmain"
CBOT_code9 = "YMmain"
CBOT_code10 = "MYMmain"

CME_exchange = 'CME'
CME_code1 = "6Emain"
CME_code2 = "6Bmain"
CME_code3 = "6Cmain"
CME_code4 = "6Amain"
CME_code5 = "6Jmain"
CME_code6 = "6Nmain"
CME_code7 = "6Smain"
CME_code8 = "E7main"
CME_code9 = "J7main"
CME_code10 = "NQmain"
CME_code11 = "MNQmain"
CME_code12 = "ESmain"
CME_code13 = "MESmain"
CME_code14 = "NIYmain"
CME_code15 = "MES2203"

SGX_exchange = 'SGX'
SGX_code1 = "NKmain"
SGX_code2 = "TWmain"
SGX_code3 = "CNmain"
SGX_code4 = "NK2012"

ForwardContractLists = {'QC2101', 'HHI2312', 'HSI2212', 'CUS2203', 'HSI2512', 'HSI2312', 'HHI2212', 'HHI2412',
                   'HSI2412', 'HSI2112', 'CUS2112', 'HHI2512', 'HHI2112', 'CUS2109', 'CUS2106', 'CN2011',
                        'NIY2011', 'NK2011', 'NK2101', 'NK2010', 'TW2012', 'CN2012', 'TW2011',
                        'NIY2010', '6J2101', 'SI2101', 'HG2011', 'GC2011', 'QM2101', 'CUS2206', 'NIY2101', 'GC2606',
                        'NK2106', 'YM2106', 'CN2106', 'CN2103', 'MES2012', 'ZS2307', 'ZS2209', 'ZS2311', 'ZS2208',
                        'NK2212', 'TW2203', 'NK2112', 'NK2712', 'TW2112', 'TW2306', 'NK2306', 'NK2303', 'NK2412',
                        'NK2512', 'TW2209', 'NK2406', 'NK2806', 'NK2102', 'NK2105', 'TW2106', 'NK2612', 'NK2104',
                        'TW2303', 'NK2109', 'NK2709', 'TW2103', 'NK2203', 'NK2409', 'NK2103', 'NK2703', 'TW2206',
                        'NKmain', 'NK2012', 'TW2010', 'NK2009', 'NK2309', 'TW2109', 'NK2503', 'TW2212',
                        'NK2206', 'GC2506'}



################证券#####################

SEHK_exchange = 'SEHK'
SEHK_code1 = "00700"    # 腾讯
SEHK_code2 = "02319"
SEHK_code3 = "00005"
SEHK_code4 = "08225"
SEHK_code5 = "01458"
SEHK_code6 = "87001"
SEHK_code7 = "01810"
SEHK_code8 = "01573"    # 小米

SEHK_greyMarketCode1 = "02170"
SEHK_greyMarketCode2 = "02161"
SEHK_greyMarketCode1_yesterday = "02160"

SEHK_newshares_code1 = '02160'
SEHK_newshares_code2 = '06993'
SEHK_newshares_code3 = '09913'
SEHK_newshares_code4 = '09987'

SEHK_indexCode1 = "0000100"     # 指数-恒生指数
SEHK_indexCode2 = "0001400"     # 指数-恒生中国企业指数

SEHK_TrstCode1 = "02778"    # 信托产品-冠君产业信托
SEHK_TrstCode2 = "00823"    # 信托产品-领展房产基金

NYSE_TrstCode1 = "ABR"    # 信托产品-阿拉伯房地产信托
NYSE_TrstCode2 = "AHI"    # 信托产品-

SEHK_WarrantCode1 = "17618"     # 涡轮
SEHK_WarrantCode2 = "17618"     # 涡轮

SEHK_CbbcCode1 = "54921"        # 牛熊证
SEHK_CbbcCode2 = "69994"        # 牛熊证

SEHK_InnerCode1 = "47060"       # 界内证
SEHK_InnerCode2 = "48073"       # 界内证

SEHK_FundCode1 = "02800"       # 基金
SEHK_FundCode2 = "02823"       # 基金

SEHK_DevrivativeCode1 = "29417"        # 认沽权证
SEHK_DevrivativeCode2 = "13898"        # 认沽权证

SEHK_EquityCode1 = "08015"        # 认购权证


ASE_exchange = 'ASE'  # American Stock Exchange美国证券交易所
ASE_code1 = 'PED'
ASE_code2 = 'FTSI'

NYSE_exchange = 'NYSE'  # 纽交所
NYSE_code1 = "BABA"
NYSE_code2 = "XPEV"

NASDAQ_exchange = 'NASDAQ'  # 纳斯达克
NASDAQ_code1 = "AAPL"
NASDAQ_code2 = "AMZN"
NASDAQ_code3 = 'PDD'
NASDAQ_code4 = 'JD'
NASDAQ_code5 = 'TSLA'

BATS_exchange = 'BATS'
BATS_code1 = "ACES"
BATS_code2 = "ACWV"

IEX_exchange = 'IEX'
IEX_code1 = "ZEXIT"
# IEX_code2 = "ETH"

if env == 'SIT':
    mid_auth_address = 'https://eddid-auth-center-qa.eddid.com.cn:1443/v2/token'
    mid_market_right_address = 'https://route-service-qa.eddid.com.cn:1443/open/account/eddid/market-right'

    # login_phone = '8615800002196'
    # login_pwd = 'a123456'
    # login_device_id = '2c259502820523853b3e817f8c8aabb6b'

    # login_phone = '8615919987852'
    # login_pwd = 'abcd1234'
    # login_device_id = '2e1197869ce7435e7bf77f979d9ace1b7'

    login_phone = '8615100000002'
    login_pwd = 'a123456'
    login_device_id = '2f27504ca21f531deafc5cc7da15350ce'

    dbPath = db_save_folder + env + '_market_test.db'
    pub_address = 'tcp://*:56789'
    router_address = 'tcp://*:5555'

    '''行情源IP'''
    fiu_sub_address = 'tcp://192.168.80.201:5576'  # FIU港期行情采集器, 测试环境
    ms_sub_address = 'tcp://192.168.80.201:5558'  # MorningStar外期行情采集器, 测试环境
    hk_stock_sub_address = 'tcp://172.16.10.211:5570'  # 港股行情采集器, 测试环境
    us_stock_sub_address = 'tcp://172.16.10.211:5580'  # 美股行情采集器, 测试环境
    future_cal_sub_address = 'tcp://192.168.80.201:7556'  # 期货计算服务地址，测试环境
    stock_cal_sub_address = 'tcp://172.16.10.211:7556'  # 证券计算服务地址，测试环境
    grey_stock_sub_address = 'tcp://172.16.10.211:3885'  # 暗盘

    fiu_dealer_address = 'tcp://192.168.80.201:5575'  # FIU港期行情采集器, 测试环境
    ms_dealer_address = 'tcp://192.168.80.201:5557'  # MorningStar外期行情采集器, 测试环境
    hk_stock_dealer_address = 'tcp://172.16.10.211:5571'  # 港股行情采集器, 测试环境
    us_stock_dealer_address = 'tcp://172.16.10.211:5581'  # 美股行情采集器, 测试环境

    codegenerate_dealer_address = 'tcp://192.168.80.201:19555'  # 合约生成服务, 测试环境
    # codegenerate_dealer_address = 'tcp://instrcode-qa.eddid.com.cn:19555'  # 合约生成服务, 测试环境

    # union_ws_url = 'ws://172.16.10.211:1516'       # 测试环境二期统一订阅地址
    # union_ws_url = 'ws://192.168.80.201:1518'       # nginx订阅, QA环境订阅地址
    # union_ws_url = 'ws://publisher-qa.eddid.com.cn:1516'   # 域名地址

    union_ws_url = 'ws://publisher-uat.eddid.com.cn:11516'      # 行情UAT环境订阅地址

    future_redis_host = '192.168.80.201'                     # 期货测试环境redis地址
    stock_redis_host = '172.16.10.211'                     # 证券测试环境redis地址
    future_redis_port = 6379
    stock_redis_port = 6381

elif env == 'PRD':
    mid_auth_address = 'https://oauth.eddidapp.com/v2/token'
    mid_market_right_address = 'https://middle-api.eddidapp.com/open/account/eddid/market-right'
    dbPath = db_save_folder + 'SIT' + '_market_test.db'   # 避免初始化出错，这里写死sit场的配置

    login_phone = '8615800002196'
    login_pwd = 'a123456'
    login_device_id = '26243c56ca7903f4d83d34a8704b6842a'

    codegenerate_dealer_address = 'tcp://contract.eddidapp.com:9555'  # 域名合约生成服务
    union_ws_url = 'ws://publisher.eddidapp.com:11516'  # 生产深圳实时订阅地址

    # ----------香港服务器-------------
    # union_ws_url = 'ws://publisher-hk-tmp.eddidapp.com:11516'       # 香港阿里云订阅地址
    # union_ws_url = 'ws://47.242.137.135:11516'                           # 生产香港负载均衡地址
    # hk_stock_sub_address = "tcp://47.242.143.223:5570"          # 生产-香港港股采集
    # us_stock_sub_address = "tcp://47.242.143.223:5580"          # 生产-香港证券采集
