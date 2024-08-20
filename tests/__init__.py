import os
import sys

p = os.path.dirname(os.path.dirname(__file__))

sys.path.append(p)
sys.path.append(os.path.join(p, 'nukeserversocket'))
