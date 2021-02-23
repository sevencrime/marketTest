

import unittest
import time
from apscheduler.schedulers.blocking import BlockingScheduler

from testcase.ws_testcase.second_phase.stock_SubscribeQuoteMsgReq_testcase import stockSubscribeTestCases

suite = unittest.TestSuite()
tests = [
    # ----------美股---------------------------------------------------------
    # stockSubscribeTestCases("test_Instr_01"),
    stockSubscribeTestCases("test_Instr_02"),
    # stockSubscribeTestCases("test_Instr_03"),
    # stockSubscribeTestCases("test_Instr_04"),
    # stockSubscribeTestCases("test_Instr_05"),

    # stockSubscribeTestCases("test_QuerySnapshotApi_001"),
    stockSubscribeTestCases("test_QuerySnapshotApi_002"),

    # stockSubscribeTestCases("test_QuoteSnapshotApi_001"),
    stockSubscribeTestCases("test_QuoteSnapshotApi_002"),

    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_01"),
    # stockSubscribeTestCases("test_QuoteBasicInfo_Msg_02"),

    # stockSubscribeTestCases("test_QuoteOrderBookDataApi_01"),
    stockSubscribeTestCases("test_QuoteOrderBookDataApi_02"),

    stockSubscribeTestCases("test_UnInstr_01"),
    # stockSubscribeTestCases("test_UnInstr_02"),
    stockSubscribeTestCases("test_UnInstr_03"),

    # stockSubscribeTestCases("test_UnSnapshot_01"),
    # stockSubscribeTestCases("test_UnSnapshot_02"),
    stockSubscribeTestCases("test_UnSnapshot_03"),

    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_01"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_02"),
    # stockSubscribeTestCases("test_UnQuoteBasicInfo_Msg_03"),

    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi_01"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi_02"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi_03"),
    # stockSubscribeTestCases("test_UnQuoteOrderBookDataApi_04"),

]

def job():
    suite.addTests(tests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

# def job1():
#     print('12345')

# if __name__ == '__main_':
scheduler = BlockingScheduler()
scheduler.add_job(job, 'date', run_date='2021-02-05 22:30:00')
# scheduler.add_job(job, 'interval', seconds=2)
scheduler.start()