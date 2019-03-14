import os

package_path = os.path.abspath(os.path.dirname(__file__))

MASTER_BRANCH = os.environ.get('MASTER_BRANCH', '2019')
ALLOW_MANUAL_BUILD_TRIGGER = bool(int(os.environ.get('ALLOW_MANUAL_BUILD_TRIGGER', 1)))
