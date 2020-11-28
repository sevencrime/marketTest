#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json

from common.test_log.ed_log import get_log

class GlobalMap:
    # 拼装成字典构造全局变量  借鉴_map  包含变量的增删改查
    logger = get_log()

    _map = {}

    def set_map(self, key, value):
        if (isinstance(value, dict)):
            # 把dict转为str
            value = json.dumps(value)
        self._map[key] = value

    def set_List(self, key, value):
        if (isinstance(value, list)):
            self._map[key] = value

    def set_value(self, **keys):
        try:
            for key_, value_ in keys.items():
                self._map[key_] = str(value_)
                # self.logger.debug(key_+":"+str(value_))
        except BaseException as msg:
            self.logger.error(msg)
            raise msg

    def set_bool(self, **keys):
        try:
            for key_, value_ in keys.items():
                self._map[key_] = value_
                # self.logger.debug(key_+":"+str(value_))
        except BaseException as msg:
            self.logger.error(msg)
            raise msg


    def del_map(self, key):
        try:
            # 删除变量
            # del语句作用在变量上，而不是数据对象上。
            del self._map[key]
            return self._map
        except KeyError:
            self.logger.error("key:'" + str(key) + "'  不存在")

    def get_value(self, *args):
        try:
            dic = {}
            for key in args:
                if len(args) == 1:
                    dic = self._map[key]
                    # self.logger.debug(key+":"+str(dic))
                elif len(args) == 1 and args[0] == 'all':
                    dic = self._map
                else:
                    dic[key] = self._map[key]
            return dic
        except KeyError:
            self.logger.warning("key:'" + str(key) + "'  不存在")
            return None


if __name__ == '__main__':
    gm = GlobalMap()
    gm.set_map("basic", {"a":1})
    a = gm.get_value("basic")
    print(a)
    print(type(a))
    print(gm._map)
