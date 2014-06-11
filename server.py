from flask import (Flask, render_template, url_for, send_file, jsonify,
                   request)
import json
import os
from os.path import join as joinp
from glob import glob
from futil import age as file_age, base_path
import time
import logging

from time import gmtime, strftime

from builder import build as build_paper, cache
from multiprocessing import Process
from pr_list import update_papers, pr_list_file

app = Flask(__name__)

# --- Customize these variables ---
MASTER_BRANCH='2014'

# ---

if not os.path.isfile(pr_list_file):
    update_papers()

with open(pr_list_file) as f:
    pr_info = json.load(f)
papers = [(str(n), pr) for n, pr in enumerate(pr_info)]

logfile = open(joinp(os.path.dirname(__file__), './flask.log'), 'w')
def log(message):
    logfile.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " +
                  message + '\n')
    logfile.flush()


def status_file(nr):
    return joinp(cache(), str(nr) + '.status')


def status_from_cache(nr):
    if nr == '*':
        status_files = glob(status_file(nr))
    else:
        status_files = [status_file(nr)]

    data = {}

    for fn in status_files:
        n = fn.split('/')[-1].split('.')[0]

        if not os.path.exists(fn):
            data[n] = {'success': 'fail', 'build_output': ''}
        else:
            with open(fn, 'r') as f:
                data[n] = json.load(f)['data']

    # Unpack status if only one record requested
    if nr != '*':
        return data[nr]
    else:
        return data


@app.route('/')
def index():
    prs_age = file_age(pr_list_file)
    if (prs_age is None or prs_age > 60):
        log("Updating papers...")
        update_papers()

    print status_from_cache('*')
    return render_template('index.html', papers=papers,
                           status=status_from_cache('*'),
                           build_url=url_for('build', nr=''),
                           download_url=url_for('download', nr=''))


@app.route('/build/<nr>')
def build(nr):
    try:
        pr = pr_info[int(nr)]
    except:
        return jsonify({'status': 'fail',
                        'message': 'Invalid paper specified'})

    age = file_age(status_file(nr))
    if not (age is None or age > 5):
        # Currently, these returns aren't used anywhere, but we
        # must send back something
        return jsonify({'status': 'fail',
                        'message': 'Paper was rebuilt recently. '
                                   'Wait a while'})

    log = status_file(nr)
    with open(log, 'w') as f:
        json.dump({'status': 'success',
                   'data': {'build_status': 'Building...',
                            'build_output': '',
                            'build_timestamp': ''}}, f)


    def build_and_log(*args, **kwargs):
        status = build_paper(*args, **kwargs)
        with open(log, 'w') as f:
            json.dump(status, f)

    p = Process(target=build_and_log,
                kwargs=dict(user=pr['user'], branch=pr['branch'],
                            master_branch=MASTER_BRANCH,
                            target=nr, log=log))
    p.start()

    def killer(p, timeout):
        time.sleep(timeout)
        try:
            p.terminate()
        except OSError:
            pass

    k = Process(target=killer, args=(p, 180))
    k.start()

    return jsonify({'status': 'OK'})


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

    if not status['succes']:
        return "Paper has not been successfully rendered yet."

    return send_file(status['pdf_path'])


@app.route('/webhook', methods=['POST'])
def webhook():
    print request.data
    data = json.loads(request.data)
#    log(data)
    return jsonify({'status': 'success'})


if __name__ == "__main__":
    app.run(debug=True)
