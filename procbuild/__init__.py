from __future__ import print_function, absolute_import

import os

from .server import app, log, papers, paper_queue, monitor_queue

# --- Customize these variables ---
MASTER_BRANCH = os.environ.get('MASTER_BRANCH', '2017')
ALLOW_MANUAL_BUILD_TRIGGER = bool(int(os.environ.get(
    'ALLOW_MANUAL_BUILD_TRIGGER', 1)))

__all__ = ['app', 'log', 'MASTER_BRANCH', 'papers', 'paper_queue']
