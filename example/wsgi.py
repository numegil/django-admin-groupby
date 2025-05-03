"""WSGI/ASGI config for the example project."""

import os

from django.core.wsgi import get_wsgi_application
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# WSGI application 
application = get_wsgi_application()

# ASGI application
asgi_application = get_asgi_application()