import tempfile
import subprocess
import shlex
from glob import glob
import os
import shutil
import json
import time

from futil import age as file_age

excluded = ['vanderwalt',]


def cache(path='cache'):
    try:
        os.mkdir(path)
    except OSError as e:
        pass

    return path


def repo(user='scipy'):
    return 'https://github.com/%s/scipy_proceedings.git' % user


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
    return shell('git clone %s --branch %s --single-branch %s' % \
                 (repo, branch, build_path))


def build(user, branch, target, log=None):
    status = {'success': False,
              'output': '',
              'pdf_path': '',
              'status': 'Build failed.'}

    master_path = cache() + '/scipy_proceedings'
    if not os.path.exists(master_path):
        errcode, output = checkout(repo('scipy'), 'master', master_path)
        status['output'] += output

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
        status['output'] += 'No papers found: %s\n' % papers
        return status

    # For safety, use our copy of the tools
    status['output'] += 'Copying proceedings build tools...\n'
    errcode, output = shell('cp -r %s %s' % (master_path, build_path))
    status['output'] += output
    if errcode:
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
    status['status'] = time.strftime('%d/%m %H:%M')
    status['pdf_path'] = target_path

    if log is not None:
        with open(log, 'w') as f:
            json.dump(status, f)

    return status


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
