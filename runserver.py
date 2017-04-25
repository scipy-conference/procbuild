#!/usr/bin/env python

# -- SERVER CONFIGURATION -- (can be overridden from shell)

config = (('MASTER_BRANCH', '2017'),
          ('ALLOW_MANUAL_BUILD_TRIGGER', '1'))

# -- END SERVER CONFIGURATION --

import os
for (key, val) in config:
    if not key in os.environ:
        os.environ[key] = val

from procbuild import app, monitor_queue
from waitress import serve

print('Monitoring build queue...')
monitor_queue()
serve(app, host='0.0.0.0', port=7000)

# Without waitress, this is the call:
#
# app.run(debug=False, host='0.0.0.0', port=7000)
