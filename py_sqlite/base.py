# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/14
# @Software: PyCharm

import threading
import time
import os

import sqlite3

from common.common_method import Common
from common.test_log.ed_log import get_log
from test_config import *


class SqliteDB(object):

    __instance = None
    __first_init = False

    def __new__(cls, *args, **kwargs):
        # 单例模式
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance


    def __init__(self, is_subscribe_record=False):
        if not SqliteDB.__first_init:
            # 先创建目录
            if not os.path.exists(db_save_folder):
                os.makedirs(db_save_folder)

            self.common = Common()
            self.logger = get_log()
            self.conn = sqlite3.connect(dbPath, check_same_thread=False, timeout=15)
            currentDayTimeStampInfo = self.common.getCurrentDayTimeStampInfo()
            self.todayBeginTimeStamp = currentDayTimeStampInfo['todayBeginTimeStamp']
            self.todayEndTimeStamp = currentDayTimeStampInfo['todayEndTimeStamp']
            self.is_subscribe_record = is_subscribe_record
            self.assemble_num = sql_assemble_num
            self.assemble_sql = ''
            self.assemble_float_num = 0
            self.transaction_num = sql_transaction_num
            self.transaction_float_num = 0
            # db_file = SETUP_DIR + "\\zmq_py3\\zmq_save_files\\db\\SIT_market_test.db"
            # if not os.path.exists(db_file):
            self.create_table()
            SqliteDB.__first_init = True

    def create_table(self):
        # 创建DB目录
        create_pub_table = '''
            CREATE TABLE IF NOT EXISTS {} (
              "id" INTEGER NOT NULL,
              "data_type" TEXT NOT NULL,
              "origin_info" TEXT,
              "json_info" TEXT,
              "record_time" integer,
              PRIMARY KEY ("id")
            );
        '''.format(pub_table)

        create_deal_table = '''
            CREATE TABLE IF NOT EXISTS {} (
              "id" INTEGER NOT NULL,
              "data_type" TEXT NOT NULL,
              "origin_info" TEXT,
              "json_info" TEXT,
              "record_time" integer,
              PRIMARY KEY ("id")
            );
        '''.format(deal_table)

        create_subscribe_table = '''
            CREATE TABLE IF NOT EXISTS {} (
              "id" INTEGER NOT NULL,
              "data_type" integer NOT NULL,
              "product_code" TEXT,
              "instr_code" TEXT,
              "source_update_time" integer,
              "record_time" integer,
              "json_info" TEXT, period_type TEXT,
              PRIMARY KEY ("id")
            );
        '''.format(subscribe_table)

        create_time_analysis_base_table = '''
            CREATE TABLE IF NOT EXISTS {} (
              "id" integer NOT NULL,
              "exchange" TEXT,
              "product_code" TEXT,
              "instr_code" TEXT,
              "data_type" integer,
              "collect2out" integer,
              "subscribe2out" integer,
              "collector2subscribe" integer,
              "source2collector" integer,
              "inner_total_time" integer,
              "json_info" TEXT,
              PRIMARY KEY ("id")
            );

            CREATE INDEX IF NOT EXISTS analysis_index 
            ON time_analysis_base_info ('instr_code', 'data_type');
        '''.format(time_analysis_base_table)

        create_statistical_analysis_table = '''
            CREATE TABLE IF NOT EXISTS {} (
                "id" integer NOT NULL,
                "desc" TEXT,
                "exchange" TEXT,
                "product_code" TEXT,
                "instr_code" TEXT,
                "data_type" TEXT,
                "max_collect2out" TEXT,
                "min_collect2out" TEXT,
                "av_collect2out" TEXT,
                "max_subscribe2out" TEXT,
                "min_subscribe2out" TEXT,
                "av_subscribe2out" TEXT,
                "max_collector2subscribe" TEXT,
                "min_collector2subscribe" TEXT,
                "av_collector2subscribe" TEXT,
                "max_source2collector" TEXT,
                "min_source2collector" TEXT,
                "av_source2collector" TEXT,
                "max_inner_total_time" TEXT,
                "min_inner_total_time" TEXT,
                "av_inner_total_time" TEXT,
                "analysis_num" integer,
                PRIMARY KEY ("id")
            );

            CREATE INDEX IF NOT EXISTS statistical_analysis_index
            ON statistical_analysis ('instr_code', 'data_type');
        '''.format(statistical_analysis_table)

        create_cal_table = '''
            CREATE TABLE IF NOT EXISTS {} (
              "id" integer NOT NULL,
              "data_type" text,
              "product_code" TEXT,
              "instr_code" TEXT,
              "precision" integer,
              "price" integer,
              "vol" integer,
              "time" integer,
              PRIMARY KEY ("id")
            );
        '''.format(cal_table)

        sql = create_pub_table + create_deal_table + create_subscribe_table + create_time_analysis_base_table + create_statistical_analysis_table + create_cal_table

        self.commit(sql)

    def commit(self, sql):
        start = time.time()
        try:
            cursor = self.conn.cursor()
            cursor.executescript(sql)
            self.conn.commit()
            result = cursor.fetchone()
            return result
        except Exception as e:
            self.logger.debug("sqlCommit exec error: {}".format(e))
        finally:
            self.logger.debug('sql commit cost: {} seconds.'.format(time.time() - start))

    def select(self, sql):
        self.logger.debug('sqlSelect Sql: {}'.format(sql))
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchone()
            return result
        except Exception as e:
            self.logger.debug("sqlSelect exec error: {}".format(e))

    def multi_select(self, sql):
        self.logger.debug('sqlSelectMulil Sql:{}'.format(sql))
        resList = []
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            for line in result:
                resList.append(line)
            return resList
        except Exception as e:
            self.logger.debug("sqlSelectMulil exec error: {}".format(e))

    def multi_select_with_gen(self, sql):
        self.logger.debug('sqlSelectMulil Sql:{}'.format(sql))
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            for line in result:
                yield line
        except Exception as e:
            self.logger.debug("sqlSelectMulilWithGen exec error: {}".format(e))

    def exit(self):
        self.conn.close()

    def stress_insert(self, assemble_first, single_info):
        self.assemble_float_num += 1
        self.assemble_sql = self.assemble_sql + single_info
        if self.assemble_float_num >= self.assemble_num:
            single_finaly_sql = (assemble_first + self.assemble_sql).rstrip(', ') + ';\n'
            self.assemble_sql = ''
            self.assemble_float_num = 0
            self.transaction_float_num += 1
            if self.transaction_float_num == 1:
                self.finaly_sql = 'begin;\n' + single_finaly_sql
            elif self.transaction_float_num > 1 and self.transaction_float_num < self.transaction_num:
                self.finaly_sql = self.finaly_sql + single_finaly_sql
            elif self.transaction_float_num > 1 and self.transaction_float_num == self.transaction_num:
                self.finaly_sql = self.finaly_sql + single_finaly_sql + 'commit;'
            if self.transaction_num == 1:
                self.finaly_sql = self.finaly_sql + 'commit;'
            if self.transaction_float_num >= self.transaction_num:
                self.commit(self.finaly_sql)
                self.transaction_float_num = 0


if __name__ == '__main__':
    pass
    SqliteDB()
