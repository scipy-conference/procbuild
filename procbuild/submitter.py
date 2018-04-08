import zmq
import json

from .message_proxy import IN


class BuildRequestSubmitter:
    
    def __init__(self):
        ctx = zmq.Context()
        self.socket = ctx.socket(zmq.PUSH)
        self.socket.connect(IN)
    
    def construct_message(self, nr):
        return ['build_queue', json.dumps({'build_paper': nr})]
        
    def submit(self, nr):
        message = self.construct_message(nr)
        # TODO: remove after debugging
        print('Submitting:', message)
        # TODO: Error checking around this send?
        self.socket.send_multipart([m.encode('utf-8') for m in message])

if __name__ == "__main__":
    BuildRequestSubmitter().submit(0)
