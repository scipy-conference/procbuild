#!/usr/bin/env python

# Schedule some or all papers for build

from procbuild.pr_list import get_papers
from procbuild.submitter import BuildRequestSubmitter
import sys

if len(sys.argv) > 1:
    to_build = argv[1:]
else:
    to_build = [nr for nr, info in get_papers()]

submitter = BuildRequestSubmitter()
for p in to_build:
    print(f"Submitting paper {p} to build queue.")
    submitter.submit(p)
