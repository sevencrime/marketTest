# -*- coding:utf-8 -*-

import codecs
import os
import time
from logging import FileHandler

'''
重写FileHandler , 防止多进程报错
'''
class SafeFileHandler(FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=0, suffix="%Y-%m-%d"):
        if codecs is None:
            encoding = None
        current_time = time.strftime(suffix, time.localtime())
        FileHandler.__init__(self, filename + "." + current_time, mode, encoding, delay)

        self.filename = os.fspath(filename)

        self.mode = mode
        self.encoding = encoding
        self.suffix = suffix
        self.suffix_time = current_time

    def emit(self, record):
        try:
            if self.check_base_filename():
                self.build_base_filename()
            FileHandler.emit(self, record)
        except(KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def check_base_filename(self):
        time_tuple = time.localtime()

        if self.suffix_time != time.strftime(self.suffix, time_tuple) or not os.path.exists(
                os.path.abspath(self.filename) + '.' + self.suffix_time):
            return 1
        else:
            return 0

    def build_base_filename(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        # if self.suffix_time != "":
        #     index = self.baseFilename.find("." + self.suffix_time)
        #     if index == -1:
        #         index = self.baseFilename.rfind(".")
        #     self.baseFilename = self.baseFilename[:index]

        current_time_tuple = time.localtime()
        self.suffix_time = time.strftime(self.suffix, current_time_tuple)
        self.baseFilename = os.path.abspath(self.filename) + "." + self.suffix_time

        if not self.delay:
            self.stream = open(self.baseFilename, self.mode, encoding=self.encoding)