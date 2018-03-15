from __future__ import print_function, absolute_import

import os

package_dir = os.path.abspath(os.path.dirname(__file__))

MASTER_BRANCH = os.environ.get('MASTER_BRANCH', '2017')
ALLOW_MANUAL_BUILD_TRIGGER = bool(int(
    os.environ.get('ALLOW_MANUAL_BUILD_TRIGGER', 1))
    )

#from .server import (app, log, get_papers, monitor_queue,
#    MASTER_BRANCH, ALLOW_MANUAL_BUILD_TRIGGER)

# --- Customize these variables ---

__all__ = ['app', 'log', 'MASTER_BRANCH', 'paper_queue']
