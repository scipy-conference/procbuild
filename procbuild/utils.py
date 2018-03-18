import os
import inspect
import io
import time

from datetime import datetime
from os.path import join as joinp

from . import package_path


def log(message):
    print(message)
    with io.open(joinp(package_path, '../flask.log'), 'a') as f:
        time_of_message = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) 
        cf = inspect.currentframe().f_back
        where = f'{cf.f_code.co_filename}:{cf.f_lineno}'
        f.write(" ".join([time_of_message, where, message, '\n']))
        f.flush()


def file_age(fn):
    """Return the age of file `fn` in minutes.  Return None is the file does
    not exist.
    """
    if not os.path.exists(fn):
        return None

    modified = datetime.fromtimestamp(os.path.getmtime(fn))
    delta = datetime.now() - modified

    return delta.seconds / 60

    
    
