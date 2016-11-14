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



install_toolsets()

setup_logging()  # setup logger, handlers
#
# TaskLog.objects.all().delete()
# # SkyLabFile.objects.all().delete()

# manager = MPIThreadManager()



# SkyLabFile.objects.get(task_id=20, type=2, filename='glyz_makefp.log')


# for f in SkyLabFile.objects.filter(type=2, task_id=20):
#     print ('Fname: ' + f.file.name + " URL: " + f.file.url + " PATH: " + f.file.path)
#     print (f.filename)
