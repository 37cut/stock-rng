import os
import re
import json
import time
import numpy
import requests
import threading
import contextlib
import utils

def interrupt(excp: str):
    with Semaphore_limit:
        print(f'> Quit with an exception: {excp}')
        os.kill(os.getpid(), 9)

def task_status(func):
    def wrapper(self):
        print(f'> Task {func.__name__} :: processing', end = '\r')
        func(self)
        print(f'> Task {func.__name__} :: complete  ')
    return wrapper

def verify(code: str):
    with Semaphore:
        tag = f'sh{code}' if code[0] == '6' else f'sz{code}'
        url = f'https://quote.eastmoney.com/{tag}.html'

        try: access = Session.get(url = url, timeout = 60)
        except Exception as e: interrupt(e)

        content = access.text if access.status_code == 200 else ''

        for i in re.finditer('var quotedata = {(.*)};', content):
            info = json.loads( content[i.start():i.end()].split('= ')[-1].replace(';','') )
            normal = info['bk_name'] != ''

            if normal:
                Info_append(info)

def receive(info: dict):
    with Semaphore:
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?'
        parameters = {'fields1': F1,
                      'fields2': F2,
                      'beg': From, 'end': To,
                      'secid': info['quotecode'], 'klt': Type, 'fqt': 1}

        try: access = Session.get(url = url, params = parameters, timeout = 60)
        except Exception as e: interrupt(e)

        source = json.loads(access.text)['data']

        Index_append(source['code'])
        Data_append(numpy.array([ s.split(',') for s in source['klines'] ]).reshape(-1, 7))

def swap(idx: int):
    with Semaphore:
        j = 0
        while Info[j]['code'] != Index[idx]:
            j += 1
        else:
            Info[idx], Info[j] = Info[j], Info[idx]

class Workflow:
    def __init__(self):
        pass

    def task_control(self, item: list):
        [ t.start() for t in item ]
        [ t.join() for t in item ]

    @task_status
    def task_verify(self):
        Verify = [ threading.Thread(target = verify,
                                    args = (item,),
                                    daemon = True) for item in Code ]

        self.task_control(Verify)

    @task_status
    def task_receive(self):
        Receive = [ threading.Thread(target = receive,
                                     args = (item,),
                                     daemon = True) for item in Info ]

        self.task_control(Receive)

    @task_status
    def task_swap(self):
        Swap = [ threading.Thread(target = swap,
                                  args = (idx,),
                                  daemon = True) for idx in range(len(Info)) ]

        self.task_control(Swap)

    def run(self):
        Time_start = time.time()

        self.task_verify()
        self.task_receive()
        self.task_swap()

        Time_usage = time.time() - Time_start

        print()
        print(f'> Time usage: {Time_usage:.2f}s')
        print(f'> Proceed {len(Info)} / {len(Code)} stocks')

        for idx in range(len(Info)):
            stock = utils.Stock(Info[idx], Data[idx])
            stock.show()

if __name__ == '__main__':
    Code = utils.generate_code(100)
    Semaphore = threading.Semaphore(10)
    Semaphore_limit = threading.Semaphore(1)
    Session = requests.Session()

    Info = []
    Index = []
    Data = []

    Info_append = Info.append
    Index_append = Index.append
    Data_append = Data.append

    F1 = 'f1,f2,f3,f5,f6,f7,f9,f10'
    F2 = 'f51,f52,f53,f54,f55,f56,f59'
    To = time.strftime('%Y%m%d', time.localtime())
    From = str(int(To[:4]) - 8) + To[4:6] + '01'
    Type = 103

    with contextlib.suppress(KeyboardInterrupt):
        workflow = Workflow()
        workflow.run()
