import tempfile
import subprocess
import shlex
from glob import glob
import os
import shutil
from datetime import datetime, timedelta


excluded = ['vanderwalt',]


def cache(path='cache'):
    try:
        os.mkdir(path)
    except OSError as e:
        pass

    # Delete all files older than 5 minutes
    cache_files = glob(path + '/*')
    for f in cache_files:
        modified = datetime.fromtimestamp(os.path.getmtime(f))
        if datetime.now() - modified > timedelta(minutes=5):
            os.remove(f)

    return path


def repo(user='scipy'):
    return 'https://github.com/%s/scipy_proceedings.git' % user

#def repo(user='scipy'):
#    return '/tmp/sp'


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
        return 1, e.output
    except OSError as e:
        return 1, 'File not found: ' + e.strerror


def checkout(repo, branch, build_path):
    print 'git clone %s --branch %s --single-branch %s' % (repo, branch, build_path)
    return shell('git clone %s --branch %s --single-branch %s' % \
                 (repo, branch, build_path))


def build(user, branch, target):
    build_path = tempfile.mkdtemp()

    errcode, output = checkout(repo(user), branch, build_path)
    if errcode:
        raise RuntimeError('Could not check out git repo: ' + output)

    papers = glob(build_path + '/papers/*')
    papers = [p for p in papers if not any(p.endswith(e) for e in excluded)]

    try:
        paper = papers[0].split('/')[-1]
    except:
        raise RuntimeError('No papers found: %s' % papers)

    errcode, output = shell('./make_paper.sh papers/%s' % paper, build_path)

    if errcode:
        raise RuntimeError('Could not build paper: ' + output)

    target_path = cache() + '/%s.pdf' % target
    shutil.copy('%s/output/%s/paper.pdf' % (build_path, paper),
                target_path)

    shutil.rmtree(build_path)

    return target_path


if __name__ == "__main__":
    pdf_path = build('ejeschke', '2012', 'ejeschke')
