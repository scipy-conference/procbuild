#!/usr/bin/env python

# -- SERVER CONFIGURATION -- (can be overridden from shell)

config = (('MASTER_BRANCH', '2015'),
          ('ALLOW_MANUAL_BUILD_TRIGGER', '0'))

# -- END SERVER CONFIGURATION --

import os
for (key, val) in config:
    if not key in os.environ:
        os.environ[key] = val

from procbuild import app
from waitress import serve

serve(app, host='0.0.0.0', port=8080)

# Without waitress, this is the call:
#
# app.run(debug=False, host='0.0.0.0', port=8080)
