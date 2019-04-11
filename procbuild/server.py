from flask import (render_template, url_for, send_file, jsonify,
                   request, Flask)
import json
import subprocess


from . import ALLOW_MANUAL_BUILD_TRIGGER
from .submitter import BuildRequestSubmitter
from .pr_list import update_pr_list, get_papers, get_pr_info, status_from_cache
from .utils import log


app = Flask(__name__)
print("Starting up build queue...")
# TODO add logging to these processes
subprocess.Popen(['python', '-m', 'procbuild.message_proxy'])
subprocess.Popen(['python', '-m', 'procbuild.listener'])
submitter = BuildRequestSubmitter()


@app.route('/')
def index():
    # if it's never been built or is over 5 minutes old, update_papers
    update_pr_list(expiry=5)
    papers = get_papers()

    return render_template('index.html', papers=papers,
                           build_url=url_for('build', fork=''),
                           download_url=url_for('download', fork=''),
                           allow_manual_build_trigger=ALLOW_MANUAL_BUILD_TRIGGER)



def dummy_build(fork):
    return jsonify({'status': 'fail', 'message': 'Not authorized'})


def real_build(fork):
    papers = get_papers()
    try:
        pr = papers[fork]
    except:
        return jsonify({'status': 'fail',
                        'message': 'Invalid paper specified'})

    submitter.submit(fork)

    return jsonify({'status': 'success',
                    'data': {'info': 'Build for paper %s scheduled.  Note that '
                                     'builds are only executed if the current '
                                     'build attempt is more than '
                                     '5 minutes old.' % fork}})


@app.route('/build/<fork>')
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
@app.route('/status/<fork>')
def status(fork=None):
    data = []

    if fork is None:
        fork = '*'

    return jsonify(status_from_cache(fork))


@app.route('/download/<fork>')
def download(fork):
    status = status_from_cache(fork)

    if not (status.get(fork, {}).get('data', {}).get('build_status', '') == 'success'):
        return "Paper has not been successfully rendered yet."

    return send_file(status[fork]['data']['build_pdf_path'])


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
    paper = [p for p, info in papers.items() if info['url'] == pr_url]

    if paper:
        return real_build(paper[0])
    else:
        return jsonify({'status': 'fail',
                        'message': 'Hook called for building '
                                   'non-existing paper (%s)' % pr_url})
