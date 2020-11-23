"""
WSGI config for orthos2 project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import pwd

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "orthos2.settings")
os.environ.setdefault("HOME", pwd.getpwuid(os.getuid()).pw_dir)

application = get_wsgi_application()
