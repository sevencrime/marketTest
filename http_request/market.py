# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/7/30
# @Software: PyCharm

from http_request.base import HttpClient
from test_config import *


class MarketHttpClient(HttpClient):
    def get_login_token(self, phone, pwd, device_id):
        url = mid_auth_address
        if env != 'PRD':
            authorization = 'Basic dGVzdGFwcDI6YWJjZA=='
        else:
            authorization = 'Basic Y2xpZW50X2FwcDo5ZWFlYmE1Ny0wYmEyLTQyZGItOTcxOS05Y2IzYTZjNmNjZDA='
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': authorization
        }
        data = {
            "scope": 'basic',
            "grant_type": 'password',
            "login_type": 'phone',
            "username": phone,
            "pwd_type": 'secret',
            "password": pwd,
            "device_id": device_id,
        }
        rsp_list = self.post(url=url, header=header, data=data)
        login_token = self.common.searchDicKV(rsp_list[1], 'access_token')
        return login_token

    def get_market_token(self, login_token):
        url = mid_market_right_address
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer {}'.format(login_token)
        }
        rsp_list = self.get(url=url, header=header)
        market_token = self.common.searchDicKV(rsp_list[1]['data'], 'accessToken')
        self.common.logger.debug('Get market token: {}'.format(market_token))
        return market_token


if __name__ == '__main__':
    cl = MarketHttpClient()
    a = cl.get_login_token(login_phone, login_pwd, device_id=login_device_id)
    b = cl.get_market_token(a)
    print(b)



