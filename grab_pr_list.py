import urllib
import json
import os

def fetch_PRs(user, repo, state='open'):
    params = {'state': state,
              'per_page': 100,
              'page': 1}

    data = []
    page_data = True

    while page_data:
        config = {'user': user,
                  'repo': repo,
                  'params': urllib.urlencode(params)}

        fetch_status = 'Fetching page %(page)d (state=%(state)s)' % params + \
                       ' from %(user)s/%(repo)s...' % config
        print fetch_status

        f = urllib.urlopen(
            'https://api.github.com/repos/%(user)s/%(repo)s/pulls?%(params)s' \
            % config
        )

        params['page'] += 1

        page_data = json.loads(f.read())

        if 'message' in page_data and page_data['message'] == "Not Found":
            page_data = []
            print 'Warning: Repo not found (%(user)s/%(repo)s)' % config
        else:
            data.extend(page_data)

    return data

PRs = fetch_PRs(user='scipy-conference', repo='scipy_proceedings', state='open')

PRs = [p for p in PRs if p['title'].startswith('Paper:')]

pr_info = []
for p in PRs:
    pr_info.append({'user': p['head']['user']['login'], 'title': p['title'],
                    'branch': p['head']['ref'], 'url': p['html_url']})


try:
    os.mkdir('data')
except:
    pass

with open('data/pr_info.json', 'w') as f:
    json.dump(pr_info, f)
