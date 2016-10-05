"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application

from skylab.bootskylab import setup_logging, MPIThreadManager
from skylab.modules.basetool import install_toolsets

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
application = get_wsgi_application()

install_toolsets()
# insert_to_db()
# MPICluster.objects.filter(activated_toolset__display_name="Autodo")

setup_logging()  # setup logger, handlers
manager = MPIThreadManager()

# for f in SkyLabFile.objects.filter():
#     print ('Fname: ' + f.file.name + " URL: " + f.file.url + " PATH: " + f.file.path)
#     print (f.filename)
