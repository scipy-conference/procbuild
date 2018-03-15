import zmq
import json
import io
import codecs
import time
from multiprocessing import Process

from . import MASTER_BRANCH
from .message_proxy import OUT
from .utils import file_age, status_file
from .pr_list import get_pr_info, log
from .builder import BuildManager

def handle_message(data):
    print('Message received:', data)

ctx = zmq.Context.instance()
socket = ctx.socket(zmq.SUB)
socket.connect(OUT)

socket.setsockopt(zmq.SUBSCRIBE, 'build_queue'.encode('utf-8'))

def _build_worker(nr):
    pr_info = get_pr_info()
    pr = pr_info[int(nr)]
    age = file_age(status_file(nr))
    min_wait = 0.5
    if not (age is None or age > min_wait):
        log("Did not build paper %d--recently built." % nr)
        return

    status_log = status_file(nr)
    with io.open(status_log, 'wb') as f:
        build_record = {'status': 'fail',
                        'data': {'build_status': 'Building...',
                                 'build_output': 'Initializing build...',
                                 'build_timestamp': ''}}
        json.dump(build_record, codecs.getwriter('utf-8')(f), ensure_ascii=False)


    def build_and_log(*args, **kwargs):
        build_manager = BuildManager(*args, **kwargs)
        status = build_manager.build_paper()
        with io.open(status_log, 'wb') as f:
            json.dump(status, codecs.getwriter('utf-8')(f), ensure_ascii=False)

    p = Process(target=build_and_log,
                kwargs=dict(user=pr['user'], 
                            branch=pr['branch'],
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
    while True:
        msg = socket.recv_multipart()
        target, raw_payload= msg
        payload = json.loads(raw_payload.decode('utf-8'))
        print('received', payload)
        paper_to_build = payload.get('build_paper', None)
        _build_worker(paper_to_build)
