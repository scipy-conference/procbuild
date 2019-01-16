import zmq
import json

from .message_proxy import IN


class BuildRequestSubmitter:
    """Class for submitting build requests to zmq socket.

    Parameters
    ----------
    verbose : bool, optional
        whether to print a message when submitting with builder (default is False)

    Attributes
    ----------
    verbose
    socket : zmq.socket, socket for pushing messages out
    """

    def __init__(self, verbose=False):
        ctx = zmq.Context()
        self.socket = ctx.socket(zmq.PUSH)
        self.socket.connect(IN)
        self.verbose = verbose

    def construct_message(self, fork):
        """Creates message to be sent on zmq socket.

        Parameters
        ----------
        nr : int
            the number of the PR in order of receipt
        """
        return ['build_queue', json.dumps({'build_paper': fork})]

    def submit(self, fork):
        """Submits message to zmq socket

        Parameters
        ----------
        nr : int
            the number of the PR in order of receipt
        """
        message = self.construct_message(fork)
        if self.verbose:
            print('Submitting:', message)

        # TODO: Error checking around this send?
        self.socket.send_multipart([m.encode('utf-8') for m in message])


if __name__ == "__main__":
    BuildRequestSubmitter().submit(0)
