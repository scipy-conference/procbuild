#!/usr/bin/env python

# imports
import os
from procbuild.server import app
from waitress import serve

# -- SERVER CONFIGURATION -- (can be overridden from shell)
config = (('MASTER_BRANCH', '2017'),
          ('ALLOW_MANUAL_BUILD_TRIGGER', '1'),
          ('PORT', '7001'))

# -- END SERVER CONFIGURATION --
for (key, val) in config:
    if key not in os.environ:
        os.environ[key] = val


print('Monitoring build queue...')

# Iniitalize queue monitor
serve(app, host='0.0.0.0', port=os.environ['PORT'])

# Without waitress, this is the call:
# app.run(debug=False, host='0.0.0.0', port=7001)
