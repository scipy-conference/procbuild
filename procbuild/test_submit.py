import zmq
import random
import json

from .message_proxy import IN


ctx = zmq.Context()
socket = ctx.socket(zmq.PUSH)
socket.connect(IN)


if __name__ == "__main__":
    for i in range(10):
        message = ['build_queue', json.dumps({'build_paper': 0})]
        print('Submitting:', message)
        socket.send_multipart([m.encode('utf-8') for m in message])
