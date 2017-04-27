from __future__ import print_function, absolute_import, division

import tempfile
import subprocess
import shlex
import os
import shutil
import json
import time
import random

from os.path import join as joinp
from datetime import datetime, timedelta
from glob import glob

excluded = ['vanderwalt','00_vanderwalt','jane_doe','bibderwalt','00_intro']

base_path = os.path.abspath(os.path.dirname(__file__))

def age(fn):
    """Return the age of file `fn` in minutes.  Return None is the file does
    not exist.
    """
    if not os.path.exists(fn):
        return None

    modified = datetime.fromtimestamp(os.path.getmtime(fn))
    delta = datetime.now() - modified

    return delta.seconds / 60

def cache(path='../cache'):
    cache_path = joinp(base_path, path)
    try:
        os.mkdir(cache_path)
    except OSError as e:
        pass

    return cache_path


def repo(user='scipy'):
    return 'https://github.com/%s/scipy_proceedings.git' % user


def error(msg):
    print(msg)


def decode_output(f):
    def wrapped_f(*args, **kwargs):
        err, out = f(*args, **kwargs)
        out = out.decode('utf-8')
        return err, out

    return wrapped_f


@decode_output
def shell(cmd, path=None, retry=0):
    """
    Raises
    ------
    CalledProcessError (has .returncode, .output parameter)
    """
    returncode = 0
    output = b''
    for i in range(retry + 1):
        try:
            return 0, subprocess.check_output(shlex.split(cmd), cwd=path,
                                              stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            if not isinstance(e.output, list):
                e.output = [e.output]
            returncode = e.returncode
            output += b'\n'.join(e.output)
        except OSError as e:
            if not b'Resource temporarily unavailable' in e.strerror:
                return 1, e.strerror + b'\n';
            else:
                output += b'\n' + e.strerror

        if i < retry:
            delay = random.randint(5, 10)
            output += b'\nRetrying after %ds...\n' % delay
            time.sleep(delay)

    return returncode, output.strip() + b'\n'


def checkout(repo, branch, build_path):
    return shell('git clone %s --branch %s --single-branch %s' % \
                 (repo, branch, build_path), retry=4)


def build(user, branch, target, master_branch='master', log=None):
    status = {'status': 'fail',
              'data': {'build_status': 'Build started...',
                       'build_output': '',
                       'build_pdf_path': '',
                       'build_timestamp': time.strftime('%d/%m %H:%M')}}

    def add_output(msg):
        status['data']['build_output'] += msg

    build_path = tempfile.mkdtemp()
    master_repo_path = joinp(cache(), 'scipy_proceedings')
    target_path = joinp(cache(), '%s.pdf' % target)


    if not os.path.exists(master_repo_path):
        add_output('[*] Checking out proceedings build tools '
                   'to %s...\n' % master_repo_path)
        errcode, output = checkout(repo('scipy-conference'), master_branch,
                                   master_repo_path)
    else:
        add_output('[*] Updating proceedings build tools in'
                   ' %s...\n' % master_repo_path)
        errcode, output = shell('git pull', master_repo_path, retry=2)

    add_output(output)

    if errcode:
        add_output('[X] Error code %d ' % errcode)
        return status

    add_output('[*] Check out paper repository...\n')
    errcode, output = checkout(repo(user), branch, build_path)
    add_output(output)

    if errcode:
        add_output('[X] Error code %d\n' % errcode)
        status['data']['build_status'] = 'Failed to check out paper'
        return status

    papers = glob(build_path + '/papers/*')
    papers = [p for p in papers if not any(p.endswith(e) for e in excluded)]

    try:
        paper = papers[0].split('/')[-1]
    except:
        add_output('[X] No papers found: %s\n' % papers)
        status['data']['build_status'] = 'Paper not found'
        return status

    # For safety, use our copy of the tools
    add_output('Installing proceedings build tools...\n')
    errcode, output = shell('cp -r %s/. %s' % (master_repo_path, build_path))
    add_output(output)
    if errcode:
        add_output('[X] Error code %d\n' % errcode)
        status['data']['build_status'] = 'Could not install build tools'
        return status

    paper_path = joinp(build_path, 'papers', paper)
    output_path = joinp(build_path, 'output', paper)

    shutil.copy('%s/data/IEEEtran.cls' % base_path, paper_path)
    shutil.copy('%s/data/draftwatermark.sty' % base_path, paper_path)
    shutil.copy('%s/data/everypage.sty' % base_path, paper_path)

    add_output('[*] Build the paper...\n')
    errcode, output = shell('./make_paper.sh %s' % paper_path, build_path)
    add_output(output)
    if errcode:
        add_output('[X] Error code %d\n' % errcode)
        status['data']['build_status'] = 'Build failed'
        return status

    try:
        shutil.copy(joinp(output_path, 'paper.pdf'), target_path)
    except IOError:
        add_output('[X] Paper build failed.\n')
        status['data']['build_status'] = 'Build failed'
        return status

    add_output('[*] Remove temporary files...\n')
    shutil.rmtree(build_path)

    status['status'] = 'success'
    status['data']['build_status'] = 'success'
    status['data']['build_pdf_path'] = target_path

    return status


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
