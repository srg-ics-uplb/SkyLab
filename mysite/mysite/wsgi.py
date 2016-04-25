"""
WSGI config for mysite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

from skylab.models import MPI_Cluster
import threading, pika, json


class ResultHandler(threading.Thread):
    def __init__(self):
        # TODO: check database for current mpi clusters -> create consumer threads for each
        self.binding_key = "skylab.results.#"
        super(ResultHandler, self).__init__()

    def callback(self, channel, method, properties, body):
        data = json.loads(body)
        # obj = MPI_Cluster.objects.filter(pk=data['pk'])
        if data['model'] == "mpi_cluster":
            for act in data['actions']:
                if act == "update_status":
                    MPI_Cluster.objects.filter(pk=data['pk']).update(status=data['status'])
                elif act == "update_ip":
                    # MPI_Cluster.objects.filter(pk=data['pk']).update(cluster_ip=data['cluster_ip'])
                    MPI_Cluster.objects.filter(pk=data['pk']).update(cluster_ip=data['cluster_ip'])
                elif act == "update_tools":
                    tools = json.loads(MPI_Cluster.objects.filter(pk=data['pk']).supported_tools)
                    tools.append(data['tool'])
                    MPI_Cluster.objects.filter(pk=data['pk']).update(json.dumps(tools))

        # MPI_Cluster.objects.filter(pk=3).update(cluster_ip=data['cluster_ip'])

        pass
    # TODO: handle body then save updates to database

    def run(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True, durable=True)

        self.channel.exchange_declare(exchange='topic_logs',
                                      type='topic')
        self.channel.queue_bind(exchange='topic_logs',
                                queue=result.method.queue,
                                routing_key=self.binding_key)

        self.channel.basic_consume(self.callback,
                                   queue=result.method.queue,
                                   no_ack=True)
        print "Started Result Handler Thread"
        # print MPI_Cluster.objects.filter(pk=1)
        self.channel.start_consuming()

ResultHandler().start()
# print "Kappa is here"

application = get_wsgi_application()
