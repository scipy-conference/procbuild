import tempfile
import subprocess
import shlex
from glob import glob
import os
import shutil
import json
import time
from os.path import join as joinp

from futil import age as file_age, base_path

excluded = ['vanderwalt',]


def cache(path='cache'):
    cache_path = joinp(base_path, path)
    try:
        os.mkdir(cache_path)
    except OSError as e:
        pass

    return cache_path


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


def build(user, branch, target, master_branch='master', log=None):
    status = {'success': False,
              'output': '',
              'pdf_path': '',
              'status': 'Build failed.',
              'timestamp': time.strftime('%d/%m %H:%M')}

    build_path = tempfile.mkdtemp()
    master_repo_path = cache() + '/scipy_proceedings'
    target_path = joinp(cache(), '%s.pdf' % target)

    if not os.path.exists(master_repo_path):
        errcode, output = checkout(repo('scipy'), master_branch, master_repo_path)
        status['output'] += output
    else:
        errcode, output = shell('git pull', master_repo_path)
        status['output'] += output
    if errcode:
        return status

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
    errcode, output = shell('cp -r %s/. %s' % (master_repo_path, build_path))
    status['output'] += output
    if errcode:
        return status

    paper_path = joinp(build_path, 'papers', paper)
    output_path = joinp(build_path, 'output', paper)

    shutil.copy('%s/data/IEEEtran.cls' % base_path, paper_path)
    shutil.copy('%s/data/draftwatermark.sty' % base_path, paper_path)
    shutil.copy('%s/data/everypage.sty' % base_path, paper_path)

    errcode, output = shell('./make_paper.sh %s' % paper_path, build_path)
    status['output'] += output
    if errcode:
        return status

    try:
        shutil.copy(joinp(output_path, 'paper.pdf'), target_path)
    except IOError:
        status['output'] += 'Paper build failed.'
        return status

    shutil.rmtree(build_path)

    status['success'] = True
    status['status'] = 'OK'
    status['pdf_path'] = target_path

    return status


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
