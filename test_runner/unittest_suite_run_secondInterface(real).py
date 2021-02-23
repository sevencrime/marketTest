

import unittest

from testcase.ws_testcase.second_phase.test_stock_subscribeForSecond_testcase import Test_SubscribeForSecond

suite = unittest.TestSuite()
tests = [
    # ----------第二阶段新接口---------------------------------------------------------
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot004"),
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_SubscribeGreyMarketQuoteSnapshot006"),

    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot002"), #需要两个暗盘
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot004"),#需要两个暗盘
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot006"),
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketQuoteSnapshot007"),
    # Test_SubscribeForSecond("test_SubscribeBrokerSnapshotReq_GreyMarket"),
    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq_GreyMarket"),
    #
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot004"),  # 需要两个暗盘
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot006"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot007"),
    # Test_SubscribeForSecond("test_H5_SubscribeGreyMarketQuoteSnapshot008"),

    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot002"),  # 需要两个暗盘
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot004"),  # 需要两个暗盘 ----待测试
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot006"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeGreyMarketQuoteSnapshot007"),
    #
    # Test_SubscribeForSecond("test_SubscribeGreyMarketBrokerSnapshotReq"),
    # Test_SubscribeForSecond("test_UnSubscribeGreyMarketBrokerSnapshotReq"),
    #
    # Test_SubscribeForSecond("test_Instr_GreyMarketQuote01"),
    # Test_SubscribeForSecond("test_UnInstr_GreyMarketQuote01"),
# 以上实时行情测试OK 2021.2.5
    # Test_SubscribeForSecond("test_SubscribeBrokerSnapshotReq001"),
    # Test_SubscribeForSecond("test_SubscribeBrokerSnapshotReq002"),
    # Test_SubscribeForSecond("test_SubscribeBrokerSnapshotReq003"),
    # Test_SubscribeForSecond("test_SubscribeBrokerSnapshotReq004"),

    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq001"),
    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq002"),
    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq003"),
    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq004"),
    # Test_SubscribeForSecond("test_UnSubscribeBrokerSnapshotReq005"),

    # Test_SubscribeForSecond("test_SubscribeNewsharesQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_SubscribeNewsharesQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_SubscribeNewsharesQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_SubscribeNewsharesQuoteSnapshot004"),
    # Test_SubscribeForSecond("test_SubscribeNewsharesQuoteSnapshot005"),

    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot004"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot006"),
    # Test_SubscribeForSecond("test_UnSubscribeNewsharesQuoteSnapshot007"),

    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot004"),
    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_H5_SubscribeNewsharesQuoteSnapshot006"),
    #
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot001"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot002"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot003"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot004"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot005"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot006"),
    # Test_SubscribeForSecond("test_H5_UnSubscribeNewsharesQuoteSnapshot007"),

    # Test_SubscribeForSecond("test_Instr_NewsharesQuote01"),
    # Test_SubscribeForSecond("test_UnInstr_NewsharesQuote01"),

    # Test_SubscribeForSecond("test_InstrIndex01"),
    # Test_SubscribeForSecond("test_UnInstrIndex01"),
    #
    # Test_SubscribeForSecond("test_InstrTrst01"),
    # Test_SubscribeForSecond("test_UnInstrTrst01"),
    #
    # Test_SubscribeForSecond("test_InstrWarrant01"),
    # Test_SubscribeForSecond("test_UnInstrWarrant01"),

    # Test_SubscribeForSecond("test_InstrCbbc01"),
    # Test_SubscribeForSecond("test_UnInstrCbbc01"),
    #
    # Test_SubscribeForSecond("test_InstrDevrivative01"),
    # Test_SubscribeForSecond("test_UnInstrDevrivative01"),
    #
    # Test_SubscribeForSecond("test_InstrEquity01"),
    # Test_SubscribeForSecond("test_UnInstrEquity01"),
    #
    # Test_SubscribeForSecond("test_InstrInner01"),
    # Test_SubscribeForSecond("test_UnInstrInner01"),
    #
    # Test_SubscribeForSecond("test_InstrFund01"),
    # Test_SubscribeForSecond("test_UnInstrFund01"),
    # 以上实时行情测试OK 2021.2.4
    # 以上实时行情测试OK 2021.2.1
]
suite.addTests(tests)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)