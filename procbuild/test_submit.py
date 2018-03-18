import zmq
import json

from .message_proxy import IN

ctx = zmq.Context()
socket = ctx.socket(zmq.PUSH)
socket.connect(IN)

def submit_build_request(nr):
    message = ['build_queue', json.dumps({'build_paper': nr})]
    print('Submitting:', message)
    socket.send_multipart([m.encode('utf-8') for m in message])


if __name__ == "__main__":
    main(0)
