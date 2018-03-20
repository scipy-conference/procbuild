import json
import io
import codecs
import time
from multiprocessing import Process

import zmq

from . import MASTER_BRANCH
from .message_proxy import OUT
from .utils import file_age, log
from .pr_list import get_pr_info, status_file, cache
from .builder import BuildManager


class Listener:
    def __init__(self, prefix='build_queue'):
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect(OUT)
        self.socket.setsockopt(zmq.SUBSCRIBE, prefix.encode('utf-8'))
        
    def listen(self):
        while True:
            msg = self.socket.recv_multipart()
            target, raw_payload = msg
            payload = json.loads(raw_payload.decode('utf-8'))
            print('received', payload)
            paper_to_build = payload.get('build_paper', None)
            _build_worker(paper_to_build)

        
def _build_worker(nr):
    pr_info = get_pr_info()
    pr = pr_info[int(nr)]
    age = file_age(status_file(nr))
    min_wait = 0.5
    if age is None or age <= min_wait:
        log(f"Did not build paper {nr}--recently built.")
        return

    status_log = status_file(nr)
    with io.open(status_log, 'wb') as f:
        build_record = {'status': 'fail',
                        'data': {'build_status': 'Building...',
                                 'build_output': 'Initializing build...',
                                 'build_timestamp': ''}}
        json.dump(build_record, codecs.getwriter('utf-8')(f), ensure_ascii=False)


    def build_and_log(user, branch, cache, master_branch, target, log):
        build_manager = BuildManager(user=user, 
                                     branch=branch,
                                     cache=cache,
                                     master_branch=master_branch,
                                     target=target,
                                     log=log)
        status = build_manager.build_paper()
        with io.open(status_log, 'wb') as f:
            json.dump(status, codecs.getwriter('utf-8')(f), ensure_ascii=False)

    p = Process(target=build_and_log,
                kwargs=dict(user=pr['user'], 
                            branch=pr['branch'],
                            cache=cache(),
                            master_branch=MASTER_BRANCH,
                            target=nr, log=log))
    p.start()

    def killer(process, timeout):
        time.sleep(timeout)
        try:
            process.terminate()
        except OSError:
            pass

    k = Process(target=killer, args=(p, 180))
    k.start()

    # Wait for process to complete or to be killed
    p.join()
    k.terminate()

if __name__ == "__main__":
    print('Listening for incoming messages...')
    listener = Listener()
    listener.listen()
