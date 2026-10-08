import os

from .base import *

ENV = os.environ.get('DJANGO_ENV', 'development')

if ENV == 'production':
    from .production import *
elif ENV == 'school_server':
    from .school_server import *
else:
    from .development import *
