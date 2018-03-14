import zmq
import json


from .message_proxy import OUT

def handle_message(data):
    print('Message received:', data)

ctx = zmq.Context.instance()
socket = ctx.socket(zmq.SUB)
socket.connect(OUT)

socket.setsockopt(zmq.SUBSCRIBE, 'build_queue'.encode('utf-8'))

if __name__ == "__main__":
    print('Listening for incoming messages...')
    while True:
        msg = socket.recv_multipart()
        target, payload = msg
        print('received', json.loads(payload.decode('utf-8')))
