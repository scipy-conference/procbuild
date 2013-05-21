from __future__ import division

from datetime import datetime, timedelta
import os

base_path = os.path.abspath(os.path.dirname(__file__))

def age(fn):
    """Return the age of file `fn` in minutes.  Return None is the file does
    not exist.
    """
    if not os.path.exists(fn):
        return None

    modified = datetime.fromtimestamp(os.path.getmtime(fn))
    delta = datetime.now() - modified

    return delta.seconds / 60
