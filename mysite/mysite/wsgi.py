"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application
import logging



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
application = get_wsgi_application()

from skylab.bootskylab import install_toolsets, setup_logging, MPIThreadManager

install_toolsets() #check modules directory and run install.py
setup_logging()  # setup logger, handlers

manager = MPIThreadManager() #spawn MPIThreads to handle tasks for each MPICluster


