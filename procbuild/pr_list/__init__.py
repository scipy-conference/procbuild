import urllib3
import json
import os
import io
import codecs

from os.path import join as joinp

from .. import package_path
from ..utils import file_age, log

__all__ = ['fetch_PRs', 'update_papers']


def cache(path='../cache'):
    cache_path = joinp(package_path, path)
    os.makedirs(cache_path, exist_ok=True)
    return cache_path


def get_pr_list_file():
    return joinp(cache(), 'pr_info.json')


def status_file(fork):
    return joinp(cache(), fork + '.status')

def fork_name(user, branch):
    return '-'.join((user, branch)).replace('/', '-').replace('\\', '-')

def status_from_cache(fork):
    papers = get_papers()
    if fork == '*':
        keys = papers.keys()
        status_files = [status_file(key) for key in keys]
    else:
        keys = [fork]
        status_files = [status_file(fork)]

    data = {}

    for key, fp in zip(keys, status_files):

        if key in papers:
            data[key] = {'status': 'fail',
                      'data': {'build_output': 'No build info'}}
        else:
            data[key] = {'status': 'fail',
                       'data': {'build_output': 'Invalid paper'}}

        if os.path.exists(fp):
            with io.open(fp, 'r') as f:
                try:
                    data[key] = json.load(f)
                except ValueError as e:
                    pass
    # Unpack status if only one record requested
    if fork != '*':
        return {fork: data[fork]}
    else:
        return data


def update_pr_list(expiry=1):
    if not os.path.isfile(get_pr_list_file()):
        update_papers()
    elif file_age(get_pr_list_file()) > expiry:
        log("Updating papers...")
        update_papers()


def get_pr_info():
    if not os.path.exists(get_pr_list_file()):
        update_papers()
    with io.open(get_pr_list_file(), 'r') as f:
        pr_info = json.load(f)
    return pr_info


def get_papers():
    return {fork_name(pr['user'], pr['branch']): pr for pr in get_pr_info()}


def fetch_PRs(user, repo, state='open'):
    """This command fetches PR information based on the passed in parameters.

    It specifies how many responses are expected per page, and so if we ever
    receive fewer than that number of responses, we know that there are no more.
    """
    responses_per_page = 100

    fields = {'state': state,
              'per_page': responses_per_page,
              'page': 1}

    config = {'user': user,
              'repo': repo}

    config.update(fields)

    data = []
    page_data = []

    base_url = 'https://api.github.com/repos/'
    url = f'{base_url}{config["user"]}/{config["repo"]}/pulls'
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED')

    while len(data) == 0 or len(page_data) == responses_per_page:
        fetch_status = ('Fetching page {page:d} (state={state:s})'
                        ' from {user:s}/{repo:s}...').format(**config)
        print(fetch_status)

        response = http.request('GET', url, fields=fields,
                                headers={'user-agent': 'scipy-procbuild/0.1'})

        fields['page'] += 1
        config.update(fields)

        page_data = json.loads(response.data.decode('utf-8'))

        # There are two ways this can fail: no PRs or the repo doesn't exist.
        if len(page_data) == 0:
            # This happens when the repo exists, but there are no PRs from the user.
            print('No PRs on ({user:s}/{repo:s})'.format(**config))
            break
        elif 'message' in page_data and page_data['message'] == "Not Found":
            # This happens when the user does not have the repo.
            print(('Warning: Repo not found '
                   '({user:s}/{repo:s})').format(**config))
            break
        else:
            data.extend(page_data)

    return data


def update_papers():
    PRs = fetch_PRs(user='scipy-conference',
                    repo='scipy_proceedings',
                    state='open')

    PRs = [p for p in reversed(PRs) if p['title'].startswith('Paper:')]

    pr_info = []
    for p in PRs:
        pr_info.append({'user': p['head']['user']['login'], 'title': p['title'],
                        'branch': p['head']['ref'], 'url': p['html_url']})

    with io.open(get_pr_list_file(), 'wb') as f:
        json.dump(pr_info, codecs.getwriter('utf-8')(f), ensure_ascii=False)
