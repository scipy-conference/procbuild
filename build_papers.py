#!/usr/bin/env python

# Schedule some or all papers for build

from procbuild import get_papers, paper_queue
import sys

if len(sys.argv) > 1:
    to_build = sys.argv[1:]
else:
    to_build = [int(nr) for nr, info in get_papers()]

for p in to_build:
    print("Placing %s in the build queue." % p)

    ### TODO: submit message to zmq bus
