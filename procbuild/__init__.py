from __future__ import print_function, absolute_import
# --- Customize these variables ---
import os
MASTER_BRANCH = os.environ.get('MASTER_BRANCH', '2016')
ALLOW_MANUAL_BUILD_TRIGGER = bool(int(os.environ.get(
    'ALLOW_MANUAL_BUILD_TRIGGER', 1)))

# ---

__all__ = ['app', 'log', 'MASTER_BRANCH', 'papers', 'paper_queue']


from .server import app, log, papers, paper_queue



server.monitor_queue()
