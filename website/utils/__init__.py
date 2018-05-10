import subprocess
from functools import partial

default_runner = partial(subprocess.run, stdout=subprocess.PIPE)
