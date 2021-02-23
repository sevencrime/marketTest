# -*- coding: utf-8 -*-
# !/usr/bin/python
# @Author: WX
# @Create Time: 2020/4/21
# @Software: PyCharm

import websockets
import asyncio
import sys
import time
from common.test_log.ed_log import get_log


class BaseWebSocketClient(object):
    def __init__(self, url, loop=None, close_timeout=5):
        self.url = url
        self.loop = loop
        self.close_timeout = close_timeout
        self.logger = get_log()

    async def ws_connect(self, extra_headers=None):
        try:
            asyncio.set_event_loop(self.loop)
            _start = time.time()
            self._ws = await websockets.connect(self.url, 
                                                close_timeout=self.close_timeout, 
                                                # max_queue=9**20,
                                                # max_size=9**20,
                                                # read_limit=9**20,
                                                # write_limit=9**20,
                                                extra_headers=extra_headers,
                                                ping_interval = 60
                                                )
            self.logger.debug("WS连接时间 : {}".format(time.time() - _start))
            self.logger.debug('Creat a new ws connect! Url is {}'.format(self.url))
        except Exception as e:
            self.logger.debug('Connect Error: {}'.format(e))
            assert False

    async def send(self, send_content):
        try:
            await self._ws.send(send_content)
        except Exception as e:
            self.logger.debug('Ws client send error, please check!\n{}'.format(e))

    async def recvSingle(self, index):
        rsp = None
        try:
            # self.logger.debug('The %d time to recv!' % (index+1))
            rsp = await self._ws.recv()
        except asyncio.CancelledError:
            self.logger.debug('ws recv timeout to skip!')
        except Exception as e:
            self.logger.debug('Ws client recvSingle error, please check!\n{}'.format(e))
        finally:
            return rsp

    async def recv(self, recv_num=1, recv_timeout_sec=8):
        rspList = []
        try:
            if not self.is_disconnect():
                for i in range(recv_num):
                    task = {asyncio.ensure_future(self.recvSingle(i))}
                    doneSet, pendingSet = await asyncio.wait(task, timeout=recv_timeout_sec)
                    for doneInfo in doneSet:
                        if doneInfo._result != None: # 因断连等原因导致返回为None时，这里过滤掉
                            rspList.append(doneInfo._result)
                    if pendingSet:
                        for pending in pendingSet:
                            pending.cancel()
                        self.logger.debug('Only recv {} data, and {} data timeout to skip!'.format(i, recv_num - i))
                        break
            else:
                self.logger.debug('Already disconnected! Will exiting for this case as failed')
                raise BaseException
        except BaseException as e:
            self.logger.debug('Ws client recv error, please check!\n{}'.format(e))
        return rspList

    async def send_and_recv(self, send_content, recv_num=1):
        await self.send(send_content)
        rspList = await self.recv(recv_num=recv_num)
        return rspList

    def disconnect(self):
        try:
            asyncio.set_event_loop(self.loop)
            asyncio.get_event_loop().run_until_complete(self._ws.close())
            self.logger.debug("断开连接")
        except Exception as e:
            self.logger.debug('disconnect ws error:\n{}'.format(e))

    async def stress_disconnect(self):
        try:
            await self._ws.close()
            self.logger.debug("断开连接")
        except Exception as e:
            self.logger.debug('disconnect ws error:\n{}'.format(e))

    def is_disconnect(self):
        '''
        CONNECTING, OPEN, CLOSING, CLOSED = range(4)
        '''
        if self._ws.state == 1:
            return False
        elif self._ws.state in (2, 3):
            return True

if __name__ =='__main__':
    start = time.time()
    url = 'ws://publisher-qa.eddid.com.cn:1516'
    headers = {'Device-Id': '2c259502820523853b3e817f8c8aabb6b', 'Authorization': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ0ZXN0YXBwMiIsImV4cCI6MTYwMjIzODYyOSwic3ViIjoiZDA5NDI5MmQtNTlkYS00YjMwLWIxNTktYzNiZTgxY2I4ZjIwIiwic2NvcGUiOiJiYXNpYyJ9.YdrvWA-t0t4JXU17Yw4kzSpNe42CsUS0UL9lWPL9YtFNleOQsw1TJ0wXRI02KvRxBDWcDhmvjbv3RaOBibTfsivPDdz-KEiXsQSdTlOHLvjH52xK_ucvlemVPpMYonG3PFvPZ74l5xaykjP4G40_7rUv90ugZ7CLGYgCoRl8SsE'}
    # headers = None
    if sys.platform == 'win32':
        new_loop = asyncio.ProactorEventLoop()
    else:
        new_loop = asyncio.new_event_loop()

    asyncio.set_event_loop(new_loop)
    client = BaseWebSocketClient(url, new_loop)
    
    while True:
        asyncio.get_event_loop().run_until_complete(client.ws_connect(extra_headers=headers))

