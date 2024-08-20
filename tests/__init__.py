import os
import sys

import nukeserversocket

p = os.path.dirname(os.path.dirname(__file__))

sys.path.append(os.path.join(p, 'nukeserversocket'))

print('sys path', sys.path)
