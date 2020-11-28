# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/7/30
# @Software: PyCharm

from requests.cookies import RequestsCookieJar
import requests
import urllib3
import json
from common.common_method import Common


class HttpClient(object):
    # 解决请求的时候添加 verify=False 时的报错
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def __init__(self):
        self.cookies = RequestsCookieJar()
        self.verify = False
        self.common = Common()

    def get(self, url, header=None, param=None):
        res = None
        if header is not None:
            res = requests.get(url=url, headers=header, verify=self.verify, params=param)
        else:
            res = requests.get(url=url, verify=self.verify, params=param)

        if self.common.isJson(res.text):
            return [res.status_code, json.loads(res.text)]
        else:
            return [res.status_code, res.text]

    def post(self, url, data=None, header=None):
        res = None
        if header is not None:
            if 'application/json' == header['Content-Type']:
                if type(data) == 'list':
                    pass
                else:
                    data = json.dumps(data)
            res = requests.post(url=url, data=data, headers=header, verify=self.verify)
        else:
            res = requests.post(url=url, data=data, verify=self.verify)

        if self.common.isJson(res.text):
            return [res.status_code, json.loads(res.text)]

        else:
            return [res.status_code, res.text]

    def delete(self, url, data=None, header=None):
        res = None
        if header is not None:
            res = requests.delete(url=url, data=data, headers=header)
        else:
            res = requests.delete(url=url, data=data)

        if self.common.isJson(res.text):
            return [res.status_code, json.loads(res.text)]
        else:
            return [res.status_code, res.text]