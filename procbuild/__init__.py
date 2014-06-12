# --- Customize these variables ---
MASTER_BRANCH='2014'

# ---

__all__ = ['app', 'log', 'MASTER_BRANCH', 'papers', 'paper_queue']

from flask import Flask

import os
from os.path import join as joinp
from time import gmtime, strftime

from pr_list import update_papers, pr_list_file
import json

from multiprocessing import Queue


app = Flask(__name__)


logfile = open(joinp(os.path.dirname(__file__), '../flask.log'), 'w')
def log(message):
    logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " +
                  message + '\n')
    logfile.flush()


if not os.path.isfile(pr_list_file):
    update_papers()

with open(pr_list_file) as f:
    pr_info = json.load(f)
    papers = [(str(n), pr) for n, pr in enumerate(pr_info)]

print "Setting up build queue..."
paper_queue = Queue()

import server
server.monitor_queue()
