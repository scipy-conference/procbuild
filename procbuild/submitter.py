import zmq
import json

from .message_proxy import IN


class BuildRequestSubmitter:
    """Class for submitting build requests to zmq socket.
    
    Attributes:
    ------------
    
    socket: zmq.socket, socket for pushing messages out
    
    verbose: bool, whether to print a message when submitting with builder
    """
    
    def __init__(self, verbose=False):
        """
        
        Parameters:
        ------------
        verbose: bool, whether to print a message when submitting with builder
            defaults to False
        """
        ctx = zmq.Context()
        self.socket = ctx.socket(zmq.PUSH)
        self.socket.connect(IN)
        self.verbose = verbose
    
    def construct_message(self, nr):
        """Creates message to be sent on zmq socket.
        
        Parameters:
        ------------
        nr: int, the number of the PR in order of receipt
        """
        return ['build_queue', json.dumps({'build_paper': nr})]
        
    def submit(self, nr):
        """Submits message to zmq socket
        
        Parameters:
        ------------
        nr: int, the number of the PR in order of receipt
        """
        message = self.construct_message(nr)
        if self.verbose:
            print('Submitting:', message)

        # TODO: Error checking around this send?
        self.socket.send_multipart([m.encode('utf-8') for m in message])


if __name__ == "__main__":
    BuildRequestSubmitter().submit(0)
