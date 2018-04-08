# http://zguide.zeromq.org/page:all#The-Dynamic-Discovery-Problem

import zmq
from . import package_path


IN = f'ipc://{package_path}/queue.in'
OUT = f'ipc://{package_path}/queue.out'


if __name__ == "__main__":
    context = zmq.Context()

    feed_in = context.socket(zmq.PULL)
    feed_in.bind(IN)

    feed_out = context.socket(zmq.PUB)
    feed_out.bind(OUT)

    print('[message_proxy] Forwarding messages between {} and {}'.format(IN, OUT))
    zmq.proxy(feed_in, feed_out)
