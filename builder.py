import tempfile
import subprocess
import shlex
from glob import glob
import os
import shutil
import json

from futil import age as file_age

excluded = ['vanderwalt',]


def cache(path='cache'):
    try:
        os.mkdir(path)
    except OSError as e:
        pass

    # Delete all files older than 5 minutes
    cache_files = glob(path + '/*')
    for f in cache_files:
        if file_age(f) > 5:
            os.remove(f)

    return path

#def repo(user='scipy'):
#    return 'https://github.com/%s/scipy_proceedings.git' % user

def repo(user='scipy'):
    return '/tmp/sp'


def error(msg):
    print msg


def shell(cmd, path=None):
    """
    Raises
    ------
    CalledProcessError (has .returncode, .output parameter)
    """
    try:
        return 0, subprocess.check_output(shlex.split(cmd), cwd=path)
    except subprocess.CalledProcessError as e:
        return 1, '\n'.join(e.output)
    except OSError as e:
        return 1, 'File not found: ' + e.strerror


def checkout(repo, branch, build_path):
    print 'REMOVE THIS XXX'
    return shell('git clone %s --branch 2012 --single-branch %s' % \
                 (repo, build_path))

    return shell('git clone %s --branch %s --single-branch %s' % \
                 (repo, branch, build_path))


def build(user, branch, target, log=None):
    status = {'success': False,
              'output': '',
              'pdf_path': ''}

    build_path = tempfile.mkdtemp()

    errcode, output = checkout(repo(user), branch, build_path)
    status['output'] += output
    if errcode:
        return status

    papers = glob(build_path + '/papers/*')
    papers = [p for p in papers if not any(p.endswith(e) for e in excluded)]

    try:
        paper = papers[0].split('/')[-1]
    except:
        status['output'] += 'No papers found: %s' % papers
        return status

    errcode, output = shell('./make_paper.sh papers/%s' % paper, build_path)
    status['output'] += output
    if errcode:
        return status

    target_path = cache() + '/%s.pdf' % target
    shutil.copy('%s/output/%s/paper.pdf' % (build_path, paper),
                target_path)

    shutil.rmtree(build_path)

    status['success'] = True
    status['pdf_path'] = target_path

    if log is not None:
        with open(log, 'w') as f:
            json.dump(status, f)

    return status


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
