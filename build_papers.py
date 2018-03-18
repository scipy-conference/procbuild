#!/usr/bin/env python

# Schedule some or all papers for build

from procbuild.pr_list import get_papers 
from procbuild.test_submit import submit_build_request
import sys

if len(sys.argv) > 1:
    to_build = argv[1:]
    import ipdb; ipdb.set_trace()
else:
    to_build = [nr for nr, info in get_papers()]

for p in to_build:
    print("Placing %s in the build queue." % p)
    submit_build_request(p)
