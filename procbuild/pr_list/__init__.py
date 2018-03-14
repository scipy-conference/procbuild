from __future__ import print_function, absolute_import

import urllib3
import json
import os
import io
import codecs

from os.path import join as joinp

from ..builder import cache

__all__ = ['fetch_PRs', 'update_papers']

pr_list_file = joinp(cache(), 'pr_info.json')


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

    url = 'https://api.github.com/repos/{user:s}/{repo:s}/pulls'.format(**config)
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED')

    while len(data)==0 or len(page_data) == responses_per_page:
        fetch_status = 'Fetching page {page:d} (state={state:s})'.format(**fields) + \
                       ' from {user:s}/{repo:s}...'.format(**config)
        print(fetch_status)

        response = http.request('GET', url, fields=fields,
                                headers={'user-agent': 'scipy-procbuild/0.1'})

        fields['page'] += 1

        page_data = json.loads(response.data.decode('utf-8'))

        if 'message' in page_data and page_data['message'] == "Not Found":
            print('Warning: Repo not found ({user:s}/{repo:s})'.format(**config))
            break
        else:
            data.extend(page_data)

    return data


def update_papers():
    PRs = fetch_PRs(user='scipy-conference', repo='scipy_proceedings', state='open')

    PRs = [p for p in reversed(PRs) if p['title'].startswith('Paper:')]
    
    pr_info = []
    for p in PRs:
        pr_info.append({'user': p['head']['user']['login'], 'title': p['title'],
                        'branch': p['head']['ref'], 'url': p['html_url']})

    with io.open(pr_list_file, 'wb') as f:
        json.dump(pr_info, codecs.getwriter('utf-8')(f), ensure_ascii=False)
