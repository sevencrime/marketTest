

import unittest

from testcase.ws_testcase.first_phase.SubscribeQuoteMsgReq_testcase import SubscribeTestCases

suite = unittest.TestSuite()
tests = [
    SubscribeTestCases("test_Instr_01"),
    SubscribeTestCases("test_Instr_02"),
    SubscribeTestCases("test_Instr_03"),
    SubscribeTestCases("test_Instr_04"),
    SubscribeTestCases("test_Instr_05"),
    SubscribeTestCases("test_Instr_06"),
    SubscribeTestCases("test_Instr_07"),
    SubscribeTestCases("test_Instr_08"),
    # SubscribeTestCases("test_UnMarket_03"),
    # SubscribeTestCases("test_UnSnapshot_01"),
    # SubscribeTestCases("test_UnSnapshot_02"),
    # SubscribeTestCases("test_UnSnapshot_03"),
    # SubscribeTestCases("test_UnSnapshot_04"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_01"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_02"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_03"),
    # SubscribeTestCases("test_UnQuoteBasicInfo_Msg_04"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_01"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_02"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_03"),
    # SubscribeTestCases("test_UnQuoteOrderBookDataApi_04"),

]
suite.addTests(tests)
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)