import tempfile
import subprocess
import shlex
from glob import glob
import os
import shutil
import json
import time
import random
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


def shell(cmd, path=None, retry=0):
    """
    Raises
    ------
    CalledProcessError (has .returncode, .output parameter)
    """
    returncode = 0
    output = ''
    for i in range(retry + 1):
        try:
            return 0, subprocess.check_output(shlex.split(cmd), cwd=path)
        except subprocess.CalledProcessError as e:
            if not isinstance(e.output, list):
                e.output = [e.output]
            returncode = e.returncode
            output += '\n'.join(e.output)
        except OSError as e:
            if not 'Resource temporarily unavailable' in e.strerror:
                return 1, e.strerror
            else:
                output += '\n' + e.strerror

        if i < retry:
            delay = random.randint(5, 10)
            output += '\nRetrying after %ds...\n' % delay
            time.sleep(delay)

    return returncode, output.strip() + '\n'


def checkout(repo, branch, build_path):
    return shell('git clone %s --branch %s --single-branch %s' % \
                 (repo, branch, build_path), retry=3)


def build(user, branch, target, master_branch='master', log=None):
    status = {'status': 'fail',
              'data': {'build_status': 'Building started',
                       'build_output': '',
                       'build_pdf_path': '',
                       'build_timestamp': time.strftime('%d/%m %H:%M')}}

    def add_output(msg):
        status['data']['build_output'] += msg

    build_path = tempfile.mkdtemp()
    master_repo_path = cache() + '/scipy_proceedings'
    target_path = joinp(cache(), '%s.pdf' % target)


    add_output('[*] Update proceedings build tools...\n')
    if not os.path.exists(master_repo_path):
        errcode, output = checkout(repo('scipy-conference'), master_branch,
                                   master_repo_path)
    else:
        errcode, output = shell('git pull', master_repo_path)

    add_output(output)

    if errcode:
        add_output('[X] Error code %d '
                   '(could be in use by another build)\n' % errcode)

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
        return status

    add_output('[*] Remove temporary files...\n')
    shutil.rmtree(build_path)

    status['status'] = 'success'
    status['data']['build_status'] = 'success'
    status['data']['build_pdf_path'] = target_path

    return status


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
