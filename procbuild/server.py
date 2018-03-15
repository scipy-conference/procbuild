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
from datetime import datetime, timedelta
from glob import glob
from flask import Flask

from multiprocessing import Process, Queue

from .builder import build as build_paper, BuildManager, cache, base_path 
from .pr_list import update_papers, pr_list_file

MASTER_BRANCH = os.environ.get('MASTER_BRANCH', '2017')
ALLOW_MANUAL_BUILD_TRIGGER = bool(int(os.environ.get(
    'ALLOW_MANUAL_BUILD_TRIGGER', 1)))


def get_pr_info():
    with io.open(pr_list_file) as f:
        pr_info = json.load(f)
    return pr_info


def get_papers():
    return [(str(n), pr) for n, pr in enumerate(get_pr_info())]


def outdated_pr_list(expiry=1):
    if not os.path.isfile(pr_list_file):
        update_papers()
    elif file_age(pr_list_file) > expiry:
        log("Updating papers...")
        update_papers()


def file_age(fn):
    """Return the age of file `fn` in minutes.  Return None is the file does
    not exist.
    """
    if not os.path.exists(fn):
        return None

    modified = datetime.fromtimestamp(os.path.getmtime(fn))
    delta = datetime.now() - modified

    return delta.seconds / 60


def log(message):
    print(message)
    with io.open(joinp(os.path.dirname(__file__), '../flask.log'), 'a') as f:
        time_of_message = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) 
        cf = inspect.currentframe().f_back
        where = '{}:{}'.format(cf.f_code.co_filename, cf.f_lineno)
        f.write(" ".join([time_of_message, where, message, '\n']))
        f.flush()


def status_file(nr):
    return joinp(cache(), str(nr) + '.status')


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
print("Setting up build queue...")

paper_queue_size = 0
paper_queue = {0: Queue(), 1: paper_queue_size}


@app.route('/')
def index():
    # if it's never been built or is over 1 minute old, update_papers
    outdated_pr_list(expiry=5)
    papers = get_papers()

    return render_template('index.html', papers=papers,
                           build_url=url_for('build', nr=''),
                           download_url=url_for('download', nr=''),
                           allow_manual_build_trigger=ALLOW_MANUAL_BUILD_TRIGGER)


def _process_queue(queue):
    done = False
    while not done:
        nr = queue.get()
        if nr is None:
            log("Sentinel found in queue. Ending queue monitor.")
            done = True
        else:
            log("Queue yielded paper #%d." % nr)
            _build_worker(nr)


def monitor_queue():
    print("Launching queue monitoring process...")
    p = Process(target=_process_queue, kwargs=dict(queue=paper_queue[0]))
    p.start()


def dummy_build(nr):
    return jsonify({'status': 'fail', 'message': 'Not authorized'})


def real_build(nr):
    pr_info = get_pr_info()
    try:
        pr = pr_info[int(nr)]
    except:
        return jsonify({'status': 'fail',
                        'message': 'Invalid paper specified'})

    if paper_queue[1] >= 50:
        return jsonify({'status': 'fail',
                        'message': 'Build queue is currently full.'})

    paper_queue[0].put(int(nr))
    paper_queue[1] += 1

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


def _build_worker(nr):
    pr_info = get_pr_info()
    pr = pr_info[int(nr)]
    age = file_age(status_file(nr))
    min_wait = 0.5
    if not (age is None or age > min_wait):
        log("Did not build paper %d--recently built." % nr)
        return

    status_log = status_file(nr)
    with io.open(status_log, 'wb') as f:
        build_record = {'status': 'fail',
                        'data': {'build_status': 'Building...',
                                 'build_output': 'Initializing build...',
                                 'build_timestamp': ''}}
        json.dump(build_record, codecs.getwriter('utf-8')(f), ensure_ascii=False)


    def build_and_log(*args, **kwargs):
        status = build_paper(*args, **kwargs)
        # build_manager = BuildManager(*args, **kwargs)
        # status = build_manager.build_paper()
        with io.open(status_log, 'wb') as f:
            json.dump(status, codecs.getwriter('utf-8')(f), ensure_ascii=False)

    p = Process(target=build_and_log,
                kwargs=dict(user=pr['user'], branch=pr['branch'],
                            master_branch=MASTER_BRANCH,
                            target=nr, log=log))
    p.start()

    def killer(process, timeout):
        time.sleep(timeout)
        try:
            process.terminate()
        except OSError:
            pass

    k = Process(target=killer, args=(p, 180))
    k.start()

    # Wait for process to complete or to be killed
    p.join()
    k.terminate()

@app.route('/build_queue_size')
def print_build_queue(nr=None):

    return jsonify(paper_queue[1])

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

