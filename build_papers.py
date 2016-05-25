#!/usr/bin/env python

# Schedule some or all papers for build

from procbuild import papers, paper_queue 
import sys

if len(sys.argv) > 1:
    to_build = sys.argv[1:]
else:
    to_build = [nr for nr, info in papers]

for p in to_build:
    print "Placing %s in the build queue." % p
    paper_queue[0].put(int(p))
    paper_queue[1] += int(p)

# Add sentinel to queue
paper_queue.put(None)

