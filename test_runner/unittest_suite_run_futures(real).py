

import unittest

from testcase.ws_testcase.first_phase.SubscribeQuoteMsgReq_testcase import SubscribeTestCases

suite = unittest.TestSuite()
tests = [
    # ----------港期---------------------------------------------------------
    # SubscribeTestCases("test_Instr01"),
    # SubscribeTestCases("test_Instr02"),
    # SubscribeTestCases("test_Instr03"),
    # SubscribeTestCases("test_Instr04"),
    # SubscribeTestCases("test_Instr05"),
    # SubscribeTestCases("test_Instr06"),
    # SubscribeTestCases("test_Instr07"),
    # SubscribeTestCases("test_Instr08"),
    # SubscribeTestCases("test_Instr09"),
    # SubscribeTestCases("test_Instr10"),

    # SubscribeTestCases("test_Product_001"),
    # SubscribeTestCases("test_Product_002"),
    # SubscribeTestCases("test_Product_003"),
    # SubscribeTestCases("test_Product_004"),
    # SubscribeTestCases("test_Product_005"),
    # SubscribeTestCases("test_Product_006"),
    # SubscribeTestCases("test_Product_007"),
    # SubscribeTestCases("test_Product_008"),
    #
    # SubscribeTestCases("test_Market_001"),
    # SubscribeTestCases("test_Market_002"),
    # SubscribeTestCases("test_Market_003"),
    # SubscribeTestCases("test_Market_004"),
    # SubscribeTestCases("test_Market_005"),
    # SubscribeTestCases("test_Market_006"),
    # SubscribeTestCases("test_Market_007"),

    # SubscribeTestCases("test_QuoteSnapshotApi_01"),
    # SubscribeTestCases("test_QuoteSnapshotApi_02"),
    # SubscribeTestCases("test_QuoteSnapshotApi_03"),
    # SubscribeTestCases("test_QuoteSnapshotApi_04"),
    # SubscribeTestCases("test_QuoteSnapshotApi_05"),
    # SubscribeTestCases("test_QuoteSnapshotApi_06"),
    # SubscribeTestCases("test_QuoteSnapshotApi_07"),
    # SubscribeTestCases("test_QuoteSnapshotApi_08"),
    #
    # SubscribeTestCases("test_QuerySnapshotApi_01"),
    # SubscribeTestCases("test_QuerySnapshotApi_02"),
    # SubscribeTestCases("test_QuerySnapshotApi_03"),
    # SubscribeTestCases("test_QuerySnapshotApi_04"),
    # SubscribeTestCases("test_QuerySnapshotApi_05"),
    # SubscribeTestCases("test_QuerySnapshotApi_06"),
    # SubscribeTestCases("test_QuerySnapshotApi_07"),
    # SubscribeTestCases("test_QuerySnapshotApi_08"),
    #
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_001"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_002"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_003"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_004"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_005"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_006"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_007"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_008"),

    # SubscribeTestCases("test_QuoteOrderBookDataApi01"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi02"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi03"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi04"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi05"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi06"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi07"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi08"),
    #
    # SubscribeTestCases("test_Subscribe_Msg_01"),
    # SubscribeTestCases("test_Subscribe_Msg_02"),
    # SubscribeTestCases("test_Subscribe_Msg_03"),
    # SubscribeTestCases("test_Subscribe_Msg_04"),
    #
    # SubscribeTestCases("test_UnInstr01"),
    # SubscribeTestCases("test_UnInstr02"),
    # SubscribeTestCases("test_UnInstr03"),
    # SubscribeTestCases("test_UnInstr04"),
    # SubscribeTestCases("test_UnInstr05"),
    # SubscribeTestCases("test_UnInstr06"),
    # SubscribeTestCases("test_UnInstr07"),
    # SubscribeTestCases("test_UnInstr08"),
    # SubscribeTestCases("test_UnInstr09"),
    # SubscribeTestCases("test_UnInstr10"),

    # SubscribeTestCases("test_UnSnapshot_001"),
    # SubscribeTestCases("test_UnSnapshot_002"),
    # SubscribeTestCases("test_UnSnapshot_003"),
    # SubscribeTestCases("test_UnSnapshot_004"),
    # SubscribeTestCases("test_UnSnapshot_005"),
    # SubscribeTestCases("test_UnSnapshot_006"),
    # SubscribeTestCases("test_UnSnapshot_007"),
    # SubscribeTestCases("test_UnSnapshot_008"),
    # SubscribeTestCases("test_UnSnapshot_009"),
    # SubscribeTestCases("test_UnSnapshot_010"),
    # SubscribeTestCases("test_UnSnapshot_011"),
    # SubscribeTestCases("test_UnSnapshot_012"),
    #
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_001"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_002"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_003"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_004"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_005"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_006"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_007"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_008"),
    #
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi01"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi02"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi03"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi04"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi05"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi06"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi07"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi08"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi09"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi10"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi11"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi12"),

    # SubscribeTestCases("test_UnSubsQutoMsgApi01"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi02"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi03"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi04"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi05"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi06"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi07"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi08"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi09"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi10"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi11"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi12"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi13"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi14"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi15"),
    # SubscribeTestCases("test_UnSubsQutoMsgApi16"),

    # SubscribeTestCases("test_UnMarket_001"),
    # SubscribeTestCases("test_UnMarket_002"),
    # SubscribeTestCases("test_UnMarket_003"),
    # SubscribeTestCases("test_UnMarket_004"),
    # SubscribeTestCases("test_UnMarket_005"),

    # SubscribeTestCases("test_UnProduct01"),
    # SubscribeTestCases("test_UnProduct02"),
    # SubscribeTestCases("test_UnProduct03"),
    # SubscribeTestCases("test_UnProduct04"),
    # SubscribeTestCases("test_UnProduct05"),
    # SubscribeTestCases("test_UnProduct06"),
    # SubscribeTestCases("test_UnProduct07"),
    # SubscribeTestCases("test_UnProduct08"),
    # SubscribeTestCases("test_UnProduct09"),
    # SubscribeTestCases("test_UnProduct10"),
    # SubscribeTestCases("test_UnProduct11"),
    # 以上测试OK--实时行情 2021.2.8
    # 以上测试OK--实时行情 2021.2.3
    # 以上测试OK--实时行情 2021.1.27
    # 以上测试OK--实时行情 2021.1.18

    # ----------外期---------------------------------------------------------
    # SubscribeTestCases("test_Instr_01"),
    # SubscribeTestCases("test_Instr_02"),
    # SubscribeTestCases("test_Instr_03"),  # 需要港期
    # SubscribeTestCases("test_Instr_04"),
    # SubscribeTestCases("test_Instr_05"),
    # SubscribeTestCases("test_Instr_06"),
    # SubscribeTestCases("test_Instr_07"),
    # SubscribeTestCases("test_Instr_08"),

    # SubscribeTestCases("test_Product_01"),
    # SubscribeTestCases("test_Product_02"),
    # SubscribeTestCases("test_Product_03"),
    # SubscribeTestCases("test_Product_04"),  # 需要港期
    # SubscribeTestCases("test_Product_05"),  # 需要港期
    # SubscribeTestCases("test_Product_06"),  # 需要港期
    #
    # SubscribeTestCases("test_Market_001_01"),
    # SubscribeTestCases("test_Market_001_02"),  # 需要港期
    # SubscribeTestCases("test_Market_001_03"),
    # SubscribeTestCases("test_Market_002_01"),
    # SubscribeTestCases("test_Market_002_02"),  # 需要港期
    #
    # SubscribeTestCases("test_QuoteSnapshotApi_001"),
    # SubscribeTestCases("test_QuoteSnapshotApi_002"),
    # SubscribeTestCases("test_QuoteSnapshotApi_003"),  # 需要港期
    # SubscribeTestCases("test_QuoteSnapshotApi_004"),

    # SubscribeTestCases("test_QuerySnapshotApi_001"),
    # SubscribeTestCases("test_QuerySnapshotApi_002"),
    # SubscribeTestCases("test_QuerySnapshotApi_003"),  # 需要港期
    # SubscribeTestCases("test_QuerySnapshotApi_004"),

    # SubscribeTestCases("test_QuoteBasicInfo_Msg_01"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_02"),
    # SubscribeTestCases("test_QuoteBasicInfo_Msg_03"),
    # #
    # SubscribeTestCases("test_QuoteOrderBookDataApi_01"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi_02"),
    # SubscribeTestCases("test_QuoteOrderBookDataApi_03"),
    # #
    # SubscribeTestCases("test_UnInstr_01"),
    # SubscribeTestCases("test_UnInstr_02"),
    # SubscribeTestCases("test_UnInstr_03"),

    # SubscribeTestCases("test_UnProduct_01"),
    # SubscribeTestCases("test_UnProduct_02"),
    # SubscribeTestCases("test_UnProduct_03"),
    #
    # SubscribeTestCases("test_UnMarket_01"),
    # SubscribeTestCases("test_UnMarket_02"),  # 需要港期
    # SubscribeTestCases("test_UnMarket_03"),  # 需要港期

    # SubscribeTestCases("test_UnSnapshot_01"),
    # SubscribeTestCases("test_UnSnapshot_02"),
    # SubscribeTestCases("test_UnSnapshot_03"),
    # SubscribeTestCases("test_UnSnapshot_04"),
    #
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_01"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_02"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_03"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_04"),
    #
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_01"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_02"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_03"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_04"),
# 以上测试OK----外期实时行情 2021.2.4
# 以上测试OK----生产环境 外期实时行情 2021.1.29
# 以上测试OK----外期实时行情 2021.1.28
# 以上测试OK----外期实时行情 2021.1.18



]

suite.addTests(tests)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
