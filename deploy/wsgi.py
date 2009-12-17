
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from environment import setup
setup()

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
