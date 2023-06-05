import json
import io
import codecs
import asyncio

from concurrent.futures import ThreadPoolExecutor

import zmq
from zmq.asyncio import Context

from . import MASTER_BRANCH
from .message_proxy import OUT
from .utils import file_age, log
from .pr_list import get_pr_info, status_file, cache, get_papers
from .builder import BuildManager


class Listener:
    """ Listener class for defining zmq sockets and maintaining a build queue.

    Attributes
    ----------
    ctx : zmq.asyncio.Context
        main context for the listener class
    socket : zmq.socket
        the socket for listening to
    queue : asyncio.Queue
        the queue for holding the builds
    dont_build : set
        unique collection of PRs currently in self.queue
        Note: Only modify self.dont_build within synchronous blocks.
    """

    def __init__(self):
        self.ctx = Context.instance()
        target_set = {'build_queue'}

        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.connect(OUT)
        for target in target_set:
            self.socket.setsockopt(zmq.SUBSCRIBE, target.encode('utf-8'))

        self.queue = asyncio.Queue()
        self.dont_build = set()

    async def listen(self):
        """Listener method, containing while loop for checking socket

        """
        while True:
            msg = await self.socket.recv_multipart()
            target, raw_payload = msg
            payload = json.loads(raw_payload.decode('utf-8'))
            paper_nr = payload.get('build_paper', None)

            if self.paper_too_young(paper_nr) or self.paper_in_queue(paper_nr):
                continue
            self.dont_build.add(paper_nr)
            await self.queue.put(paper_nr)

    def paper_too_young(self, fork):
        """Check the age of a PR's status_file based on its number.

        Parameters
        ----------
        fork : str
            the combined user-branch name
        """
        age = file_age(status_file(fork))
        min_wait = 0.5
        too_young = (age is not None) and (age <= min_wait)
        if too_young:
            log(f"Did not build paper {fork}--recently built.")
        return too_young

    def paper_in_queue(self, fork):
        """Check whether the queue currently contains a build request for a PR.

        Parameters
        ----------
        fork : str
            the combined user-branch name
        """
        in_queue = fork in self.dont_build
        if in_queue:
            log(f"Did not queue paper {fork}--already in queue.")
        return in_queue

    def report_status(self, fork):
        """prints status notification from status_file for paper `fork`

        Parameters
        ----------
        fork : str
            the combined user-branch name
        """
        with io.open(status_file(fork), 'r') as f:
            status = json.load(f)['status']

        if status == 'success':
            print(f"Completed build for paper {fork}.")
        else:
            print(f"Paper for {fork} did not build successfully.")


    async def queue_builder(self, loop=None):
        """Manage queue and trigger builds, report results.

        loop : asyncio.loop
            the loop on which to be running these tasks
        """
        while True:
            # await an item from the queue
            fork = await self.queue.get()
            # launch subprocess to build item
            with ThreadPoolExecutor(max_workers=1) as e:
                await loop.run_in_executor(e, self.build_and_log, fork)
                self.dont_build.remove(fork)
                self.report_status(fork)

    def paper_log(self, fork, record):
        """Writes status to PR's log file

        Parameters
        ----------
        fork : str
            the combined user-branch name
        record : dict
            the dictionary content to be written to the log
        """
        status_log = status_file(fork)
        with io.open(status_log, 'wb') as f:
            json.dump(record, codecs.getwriter('utf-8')(f), ensure_ascii=False)

    def build_and_log(self, fork):
        """Builds paper for PR number and logs the resulting status

        Parameters
        ----------
        fork : str
            the combined user-branch name
        """
        papers = get_papers()
        pr = papers[fork]

        build_record = {'status': 'fail',
                        'data': {'build_status': 'Building...',
                                 'build_output': 'Initializing build...',
                                 'build_timestamp': ''}}
        self.paper_log(fork, build_record)

        build_manager = BuildManager(user=pr['user'],
                                     repo=pr['repo'],
                                     branch=pr['branch'],
                                     cache=cache(),
                                     master_branch=MASTER_BRANCH,
                                     target=fork,
                                     log=log)

        status = build_manager.build_paper()
        self.paper_log(fork, status)


if __name__ == "__main__":
    print('Listening for incoming messages...')

    listener = Listener()

    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(listener.listen(),
                           listener.queue_builder(loop))
    try:
        loop.run_until_complete(tasks)
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
