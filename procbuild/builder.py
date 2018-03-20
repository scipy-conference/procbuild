from __future__ import print_function, absolute_import, division

import tempfile
import subprocess
import shlex
import os
import shutil
import time
import random

from os.path import join as joinp
from glob import iglob

excluded = ['vanderwalt', '00_vanderwalt', 'jane_doe', 'bibderwalt', '00_intro']

base_path = os.path.abspath(os.path.dirname(__file__))


def cache(path='../cache'):
    cache_path = joinp(base_path, path)
    try:
        os.mkdir(cache_path)
    except OSError as e:
        pass

    return cache_path


def repo(user='scipy'):
    return f'https://github.com/{user}/scipy_proceedings.git'


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
            if b'Resource temporarily unavailable' not in e.strerror:
                return 1, e.strerror + b'\n'
            else:
                output += b'\n' + e.strerror

        if i < retry:
            delay = random.randint(5, 10)
            output += b'\nRetrying after %ds...\n' % delay
            time.sleep(delay)

    return returncode, output.strip() + b'\n'


def checkout(repo, branch, build_path):
    return shell(f'git clone {repo} --branch {branch} --single-branch {build_path}', retry=4)

    
class BuildError(Exception):
    
    def __init__(self, message):
        self.message = f"A build error occurred during the self.{message} step."

        
class BuildManager:
    """
    
    Parameters
    ----------
    user: str; name of GitHub user
    branch: str; name of git branch on user's PR
    target: str; string representation of integer for which paper to build
    cache: str; cache directory in which the build tools and final paper live
    master_branch: str; git branch for build tools 
    log: function; logging function
    """
    
    def __init__(self, 
                 user, 
                 branch, 
                 target, 
                 cache,
                 master_branch='master', 
                 log=None):
        self.user = user
        self.build_output = ''
        self.status = 'fail'
        self.branch = branch
        self.master_branch = master_branch
        self.build_status = 'Build started...'
        self.build_pdf_path = ''
        self.cache = cache
        self.master_repo_path = joinp(self.cache, 'scipy_proceedings')
        self.build_timestamp = time.strftime('%d/%m %H:%M')
        self.target_path = joinp(self.cache, f'{target!s}.pdf')
        self.build_path = None
        
        data_filenames = ['IEEEtran.cls', 
                          'draftwatermark.sty', 
                          'everypage.sty']
        self.data_files = [joinp(base_path, 'data', f) for f in data_filenames]

    def add_output(self, msg):
        self.build_output += msg

    @property
    def status_report(self):
        return {'status': self.status,
                'data': {'build_status': self.build_status,
                         'build_output': self.build_output,
                         'build_pdf_path': self.build_pdf_path,
                         'build_timestamp': self.build_timestamp}
                }


    def _get_build_tools(self):
        """This command will get the latest version of the repo path.
        
        """
        if not os.path.exists(self.master_repo_path):
            self.add_output('[*] Checking out proceedings build tools '
                            f'to {self.master_repo_path}...\n')
            errcode, output = checkout(repo('scipy-conference'), 
                                       self.master_branch,
                                       self.master_repo_path)
        else:
            self.add_output('[*] Updating proceedings build tools in'
                            ' {self.master_repo_path}...\n')
            errcode, output = shell('git pull', self.master_repo_path, retry=2)
        
        self.add_output(output)
        
        if errcode:
            self.add_output('[X] Could not get build tools, errcode: %d ' % errcode)
            raise BuildError("get_build_tools")
        
        self._remove_papers_dir()
        
    
    def _remove_papers_dir(self):
        """ this command will remove the papers dir from the build_tools dir
        
        """
        errcode, output = shell('rm -rf papers', 
                                path=self.master_repo_path)
        
        self.add_output(output)

        if errcode:
            self.add_output('[X] Could not clean papers/ build tools, errcode: %d ' % errcode)
            raise BuildError("remove_papers_dir")

    def _checkout_paper_repo(self):
        self.add_output('[*] Check out paper repository...\n')
        errcode, output = checkout(repo(self.user), 
                                   self.branch, 
                                   self.build_path)
        self.add_output(output)
        
        if errcode:
            self.add_output('[X] Could not checkout user\'s repo, errcode: %d\n' % errcode)
            self.build_status = 'Failed to check out paper'
            raise BuildError('checkout_paper_repo')

    
    def _relocate_build_tools(self):
        """Move local build tools into temporary directory
        """
        self.add_output('Moving proceedings build tools to temp directory...\n')
        errcode, output = shell('cp -r '
                                f'{self.master_repo_path}/. {self.build_path}')
        self.add_output(output)
        if errcode:
            self.add_output('[X] Could not relocate build tools, errcode: %d\n' % errcode)
            self.build_status = 'Could not move build tools to temp directory'
            raise BuildError('relocate_build_tools')

    def _relocate_static_files(self):
        for f in self.data_files:
            shutil.copy(f, self.paper_path)
    
    @property
    def paper_path(self):
        return joinp(self.build_path, 'papers', self.paper)
        
    @property
    def paper(self):
        """This returns the directory from inside the papers/ directory in the PR.
        
        There should be one unique directory in the PR's papers/ directory that 
        is not explicitly excluded based on values in ``excluded``.
        
        This will err if the there no papers are found after exclusion.
        """
        papers = [p for p in iglob(self.build_path + '/papers/*')
                  if not any(p.endswith(e) for e in excluded)]

        if self.build_path is None:
            self.add_output('[X] No build path declared: %s\n' % papers)
            self.build_status = 'No build path declared'
            raise BuildError('paper')
        
        if len(papers) < 1:
            self.add_output('[X] No papers found: %s\n' % papers)
            self.build_status = 'Paper not found'
            raise BuildError('paper')
        else:
            return papers[0].split('/')[-1]
    
    def _run_make_paper_script(self):
        """Runs the scipy_proceedings make_paper.sh script
        
        """
        self.add_output('[*] Build the paper...\n')
        errcode, output = shell('./make_paper.sh %s' % self.paper_path, self.build_path)
        # errcode, output = shell('./make_paper.sh %s' self.paper_path, 
        #                         self.build_path)
        self.add_output(output)
        if errcode:
            self.add_output('[X] Error code %d\n' % errcode)
            self.build_status = 'Build failed, make_paper.sh did not succeed'
            raise BuildError('run_make_paper_script')

    def _retrieve_pdf(self):
        """Collects pdf from temporary directory and moves it to target_path.
        """
        output_path = joinp(self.build_path, 'output', self.paper)
        try:
            shutil.copy(joinp(output_path, 'paper.pdf'), self.target_path)
        except IOError:
            self.add_output('[X] Paper build failed.\n')
            self.build_status = 'Build failed, no pdf can be found'
            raise BuildError('retrieve_pdf')

    def build_paper(self):
        try:
            with tempfile.TemporaryDirectory() as build_path:
                self.build_path = build_path
                self._get_build_tools()
                self._checkout_paper_repo()
                self._relocate_build_tools()
                self._relocate_static_files()
                self._run_make_paper_script()
                self._retrieve_pdf()
        except BuildError as e:
            self.add_output(e.message)
            return self.status_report
        
        self.status = 'success'
        self.build_status = 'success'
        self.build_pdf_path = self.target_path

        return self.status_report


if __name__ == "__main__":
    build_man = BuildManager('ejeschke', '2012', 'ejeschke')
    build_man.build_paper()
