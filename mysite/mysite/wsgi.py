"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""
import os

from django.core.wsgi import get_wsgi_application
from django.db.models.signals import post_save

from skylab.bootskylab import MPIThreadManager
from skylab.models import MPICluster, Task

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
application = get_wsgi_application()

# install_toolsets()
# insert_to_db()
# MPICluster.objects.filter(activated_toolset__display_name="Autodo")

manager = MPIThreadManager()
post_save.connect(receiver=manager.receive_mpi_cluster_from_post_save_signal, sender=MPICluster,
                  dispatch_uid="receive_mpi_from_post_save_signal")
post_save.connect(receiver=manager.receive_task_from_post_save_signal, sender=Task,
                  dispatch_uid="receive_task_from_post_save_signal")





# ConsumerThreadManager().start()

# x = MPICluster.objects.get(pk=55)
# curr_tool = json.loads(x.supported_tools)
# curr_tool.append("gamess")
# x.supported_tools = json.dumps(curr_tool)
# x.save()
# f = SkyLabFile.objects.get(toolactivity__pk=139)
# print f.file.name
# x = SkyLabFile.objects.get(pk=1).file #works

# x = SkyLabFile.objects.filter(toolactivity__pk=76) #using reverse m2m
# x = x[0]
# print x.file.name

# handle_uploaded_file(x)
