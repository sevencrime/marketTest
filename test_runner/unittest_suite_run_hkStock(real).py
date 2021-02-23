

import unittest

from testcase.ws_testcase.second_phase.stock_SubscribeQuoteMsgReq_testcase import stockSubscribeTestCases

suite = unittest.TestSuite()
tests = [
    # ----------港股---------------------------------------------------------
    # stockSubscribeTestCases("test_Instr01"),
    # stockSubscribeTestCases("test_Instr02"),
    # stockSubscribeTestCases("test_Instr03"),
    # stockSubscribeTestCases("test_Instr04"),
    # stockSubscribeTestCases("test_Instr05"),
    # stockSubscribeTestCases("test_Instr06"),
    # stockSubscribeTestCases("test_Instr07"),
    # stockSubscribeTestCases("test_Instr08"),
    # stockSubscribeTestCases("test_Instr09"),

    # stockSubscribeTestCases("test_QuoteSnapshotApi_01"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_02"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_03"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_04"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_05"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_06"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_07"),
    # stockSubscribeTestCases("test_QuoteSnapshotApi_08"),
    #
    # stockSubscribeTestCases("test_QuerySnapshotApi_01"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_02"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_03"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_04"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_05"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_06"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_07"),
    # stockSubscribeTestCases("test_QuerySnapshotApi_08"),

    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_001"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_002"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_003"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_004"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_005"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_006"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_007"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_008"),
    #
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi01"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi02"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi03"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi04"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi05"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi06"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi07"),
    # stockSubscribeTestCases("test_QuoteOrderBookDataApi08"),
    #
    # stockSubscribeTestCases("test_Subscribe_Msg_01"),
    # stockSubscribeTestCases("test_Subscribe_Msg_02"),
    # stockSubscribeTestCases("test_Subscribe_Msg_03"),
    # stockSubscribeTestCases("test_Subscribe_Msg_04"),
    #
    # stockSubscribeTestCases("test_UnInstr01"),
    # stockSubscribeTestCases("test_UnInstr02"),
    # stockSubscribeTestCases("test_UnInstr03"),

    # stockSubscribeTestCases("test_UnInstr04"),
    # stockSubscribeTestCases("test_UnInstr05"),
    # stockSubscribeTestCases("test_UnInstr06"),
    # stockSubscribeTestCases("test_UnInstr07"),
    # stockSubscribeTestCases("test_UnInstr08"),
    # stockSubscribeTestCases("test_UnInstr09"),
    # stockSubscribeTestCases("test_UnInstr10"),
    # stockSubscribeTestCases("test_UnInstr11"),
    # stockSubscribeTestCases("test_UnInstr12"),

    # stockSubscribeTestCases("test_UnSnapshot_001"),
    # stockSubscribeTestCases("test_UnSnapshot_002"),
    # stockSubscribeTestCases("test_UnSnapshot_003"),
    # stockSubscribeTestCases("test_UnSnapshot_004"),
    # stockSubscribeTestCases("test_UnSnapshot_005"),
    # stockSubscribeTestCases("test_UnSnapshot_006"),
    # stockSubscribeTestCases("test_UnSnapshot_007"),
    # stockSubscribeTestCases("test_UnSnapshot_008"),
    # stockSubscribeTestCases("test_UnSnapshot_009"),
    # stockSubscribeTestCases("test_UnSnapshot_010"),
    # stockSubscribeTestCases("test_UnSnapshot_011"),
    # stockSubscribeTestCases("test_UnSnapshot_012"),
    # stockSubscribeTestCases("test_UnSnapshot_013"),
    # stockSubscribeTestCases("test_UnSnapshot_014"),
# 以上实时行情测试OK 2021.2.9
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi01"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi02"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi03"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi04"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi05"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi06"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi07"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi08"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi09"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi10"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi11"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi12"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi13"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi14"),

    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_001"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_002"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_003"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_004"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_005"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_006"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_007"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_008"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_009"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_010"),
    #
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi01"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi02"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi03"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi04"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi05"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi06"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi07"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi08"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi09"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi10"),
    # stockSubscribeTestCases("test_UnSubsQutoMsgApi11"),
# 以上实时行情测试OK 2021.2.4
# 以上实时行情测试OK 2021.2.1
## 以上生产环境 实时行情测试OK 2021.2.1
]
suite.addTests(tests)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)