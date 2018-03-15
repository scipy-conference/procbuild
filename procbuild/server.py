from __future__ import print_function, absolute_import, unicode_literals

from flask import (render_template, url_for, send_file, jsonify,
                   request, Flask)
import json
import os
import io
import time
import inspect
import codecs

from os.path import join as joinp
from glob import glob
from flask import Flask

import subprocess

import zmq
import random
import json

from .message_proxy import IN


from . import ALLOW_MANUAL_BUILD_TRIGGER, MASTER_BRANCH 
from .builder import BuildManager, cache, base_path
from .pr_list import outdated_pr_list, get_papers, get_pr_info
from .utils import file_age, status_file, log


print("Connecting to message bus")
ctx = zmq.Context()
socket = ctx.socket(zmq.PUSH)
socket.connect(IN)




def status_from_cache(nr):
    papers = get_papers()
    if nr == '*':
        status_files = [status_file(i) for i in range(len(papers))]
    else:
        status_files = [status_file(nr)]

    data = {}

    for fn in status_files:
        n = fn.split('/')[-1].split('.')[0]

        try:
            papers[int(n)]
        except:
            data[n] = {'status': 'fail',
                       'data': {'build_output': 'Invalid paper'}}
        else:
            status = {'status': 'fail',
                      'data': {'build_output': 'No build info'}}

            if os.path.exists(fn):
                with io.open(fn, 'r') as f:
                    try:
                        data[n] = json.load(f)
                    except ValueError:
                        pass

    # Unpack status if only one record requested
    if nr != '*':
        return data[nr]
    else:
        return data


app = Flask(__name__)
print("Starting up build queue...")
subprocess.Popen(['python', '-m', 'procbuild.message_proxy'])

@app.route('/')
def index():
    # if it's never been built or is over 1 minute old, update_papers
    outdated_pr_list(expiry=5)
    papers = get_papers()

    return render_template('index.html', papers=papers,
                           build_url=url_for('build', nr=''),
                           download_url=url_for('download', nr=''),
                           allow_manual_build_trigger=ALLOW_MANUAL_BUILD_TRIGGER)


# TODO: MOVE THIS TO THE LISTENER
#
# def _process_queue(queue):
#     done = False
#     while not done:
#         nr = queue.get()
#         if nr is None:
#             log("Sentinel found in queue. Ending queue monitor.")
#             done = True
#         else:
#             log("Queue yielded paper #%d." % nr)
#             _build_worker(nr)


def monitor_queue():
    print("Launching queue monitoring...")
    ## TODO: Add logging to this subprocess
    subprocess.Popen(['python', '-m', 'procbuild.test_listen'])

def dummy_build(nr):
    return jsonify({'status': 'fail', 'message': 'Not authorized'})


def real_build(nr):
    pr_info = get_pr_info()
    try:
        pr = pr_info[int(nr)]
    except:
        return jsonify({'status': 'fail',
                        'message': 'Invalid paper specified'})

## TODO: Move check to the listener
#
#    if paper_queue[1] >= 50:
#        return jsonify({'status': 'fail',
#                        'message': 'Build queue is currently full.'})

    message = ['build_queue', json.dumps({'build_paper': nr})]

    # TODO: remove after debugging
    print('Submitting:', message)

    # TODO: Error checking around this send?
    socket.send_multipart([m.encode('utf-8') for m in message])

    return jsonify({'status': 'success',
                    'data': {'info': 'Build for paper %s scheduled.  Note that '
                                     'builds are only executed if the current '
                                     'build attempt is more than '
                                     '5 minutes old.' % nr}})


@app.route('/build/<nr>')
def build(*args, **kwarg):
    if ALLOW_MANUAL_BUILD_TRIGGER:
        return real_build(*args, **kwarg)
    else:
        return dummy_build(*args, **kwarg)



#@app.route('/build_queue_size')
#def print_build_queue(nr=None):
#
#    return jsonify(paper_queue[1])

@app.route('/status')
@app.route('/status/<nr>')
def status(nr=None):
    data = []

    if nr is None:
        nr = '*'

    return jsonify(status_from_cache(nr))


@app.route('/download/<nr>')
def download(nr):
    status = status_from_cache(nr)

    if not (status.get('data', {}).get('build_status', '') == 'success'):
        return "Paper has not been successfully rendered yet."

    return send_file(status['data']['build_pdf_path'])


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = json.loads(request.data.decode('utf-8'))
    except TypeError as e:
        log(e)
        return jsonify({'status': 'fail',
                        'message': 'Invalid data type when decoded'})
    except json.JSONDecodeError as e:
        log(e)
        return jsonify({'status': 'fail',
                        'message': 'Data is not valid JSON format'})
    except Exception as e:
        log(e)
        return jsonify({'status': 'fail',
                        'message': 'unknown error'})


    papers = get_papers()
    pr_url = data.get('pull_request', {}).get('html_url', '')
    paper = [p for p, info in papers if info['url'] == pr_url]

    if paper:
        return real_build(paper[0])
    else:
        return jsonify({'status': 'fail',
                        'message': 'Hook called for building '
                                   'non-existing paper (%s)' % pr_url})

