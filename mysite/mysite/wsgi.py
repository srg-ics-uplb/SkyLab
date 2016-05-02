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
import spur, pika, threading
import re, sys, json
from skylab.modules.gamess.tool import gamess_tool

frontend_ip = "10.0.3.101"
frontend_username = "user"
frontend_password = "excellence"

cluster_username = "mpiuser"
cluster_password = "mpiuser"

class ConsumerThreadManager(threading.Thread):

    def __init__(self):
        self.threadHash = {}
        self.binding_key = "skylab.mpi.*"
        super(ConsumerThreadManager, self).__init__()
        # self.setDaemon(True)

    def callback(self, channel, method, properties, body):
        data = json.loads(body)
        print "ConsumerThreadManager: Received %s" % data
        if data['actions'] == "create_cluster":
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'],binding_key="skylab.consumer.%d" % data['pk'],
                                                         cluster_name=data['cluster_name'],cluster_size=data['cluster_size'],
                                                         supported_tools=data['tools'])
        elif data['actions'] == "connect_cluster":
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'],binding_key="skylab.consumer.%d" % data['pk'],
                                                         cluster_name=data['cluster_name'],cluster_size=data['cluster_size'],cluster_ip=data['cluster_ip'],
                                                         supported_tools=data['tools'])
            pass
        elif data['actions'] == "stop_cluster":
            pass

        self.threadHash[data['pk']].start()
        self.status = 0

    def remove(self, consumer_id):
        self.threadHash[consumer_id].stop()
        del self.threadHash[consumer_id]

    def run(self):
        clusters = MPI_Cluster.objects.filter(status=1)
        for c in clusters:
            if c.id not in self.threadHash:
                self.threadHash[c.id] = ConsumerThread(pk=c.id, binding_key="skylab.consumer.%r" % c.id,
                                                     cluster_name=c.cluster_name,
                                                     cluster_size=c.cluster_size, cluster_ip=c.cluster_ip,
                                                     supported_tools=c.supported_tools)
                self.threadHash[c.id].start()

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(heartbeat_interval=0,
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

        self.channel.start_consuming()

class ConsumerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        self.mpi_pk = kwargs.pop('pk')
        self.binding_key = kwargs.pop('binding_key')
        self.cluster_name = kwargs.pop('cluster_name')
        self.cluster_size = kwargs.pop('cluster_size')
        self.supported_tools = kwargs.pop('supported_tools')
        self.cluster_ip = kwargs.pop('cluster_ip', None)
        self.print_to_console("Created Consumer Thread ID: %d, Key: %s Cluster {name: %s, size: %d, ip:%r}" % (self.mpi_pk,self.binding_key,
                                                                                               self.cluster_name, self.cluster_size, self.cluster_ip))

        self.status = 0
        super(ConsumerThread, self).__init__(*args, **kwargs)
        # self.setDaemon(True)

    def print_to_console(self, msg):
        print "Consumer Thread %d: %s" % (self.mpi_pk, msg)

    def send_mpi_message(self,routing_key, body):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        channel = connection.channel()

        channel.exchange_declare(exchange='topic_logs',
                                 type='topic')

        channel.basic_publish(exchange='topic_logs',
                              routing_key=routing_key,
                              body=body,
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                              ))

        self.print_to_console(" [x] Sent %r:%r" % (routing_key, "body:%r" % body))
        connection.close()

    def callback(self, channel, method, properties, body):
        self.status = 1
        self.print_to_console("Received : %r" % body)
        data = json.loads(body)
        # self.print_to_console("Received %s" % data)
        if data['actions'] == "use_tool":
            self.print_to_console("Using %s" % data['tool'])

            #todo: insert code for running gamess
            tool = gamess_tool(shell=self.cluster_shell, id=data['activity'])
            tool.run_tool()

        self.status = 0

    def connect_to_frontend(self):
        try:
            self.print_to_console( "Connecting to Frontend {ip: %s; username: %s, pass: %s}" % (
                                frontend_ip, frontend_username, frontend_password))
            self.frontend_shell = spur.SshShell(hostname=frontend_ip,
                                                username=frontend_username,
                                                password=frontend_password,
                                                missing_host_key=spur.ssh.MissingHostKey.accept)
        except:
            self.print_to_console("Error: Failed to connect to frontend")
            self.print_to_console(sys.exc_info())

    def connect_to_cluster(self,create=False):
        try:
            self.cluster_shell = spur.SshShell(hostname=self.cluster_ip, username=cluster_username,
                                               password=cluster_password,
                                               missing_host_key=spur.ssh.MissingHostKey.accept)
            self.print_to_console("Connecting to MPI Cluster")
            if create:
                self.update_p2c()

        except spur.ssh.ConnectionError as err:
            self.print_to_console("Error: Failed to connect to MPI cluster.")
            # self.print_to_console(sys.exc_info())
            self.print_to_console(err.args)
            raise

    def activate_tool(self,tool_name):
        self.print_to_console("Activating %s" % tool_name)
        tool_activator = self.cluster_shell.run(["p2c-tools","activate",tool_name])
        # running sudo p2c-tools activate gamess associates gamess work directories to root
        # tool_activator = self.cluster_shell.spawn(["sudo", "p2c-tools", "activate", tool_name], use_pty=True)
        #
        # tool_activator.stdin_write(cluster_password + "\n")
        # tool_activator = tool_activator.wait_for_result()
        # p = re.compile("export\s(?P<path>PATH.+)")
        # m = p.search(tool_activator.output)
        # if m is not None:
        #     self.cluster_shell.run(["sh","-c","export",m.group('path')])
        # self.print_to_console(output.output)  #might be text-heavy skipped
        self.print_to_console(tool_activator.output)
        x = MPI_Cluster.objects.get(pk=self.mpi_pk)
        # curr_tool = json.loads(x.supported_tools)
        # curr_tool.append(tool_name)
        # x.supported_tools = json.dumps(curr_tool)
        x.supported_tools = tool_name
        x.save()
        self.print_to_console("%s is now activated" % tool_name)

    def update_p2c(self):
        self.cluster_shell.run(["sh","-c","rm p2c-tools*"])
        self.print_to_console("Updating p2c-tools")
        self.cluster_shell.run(["wget", "10.0.3.10/downloads/p2c/p2c-tools"])
        self.cluster_shell.run(["chmod", "755", "p2c-tools"])
        p2c_updater = self.cluster_shell.spawn(["./p2c-tools"], use_pty=True)
        p2c_updater.stdin_write(cluster_password + "\n")
        self.print_to_console(p2c_updater.wait_for_result().output)
        self.print_to_console(self.cluster_shell.run(["p2c-tools"]).output)

    def connect_or_create(self):
        if self.cluster_ip is None: #exec vcluster-create
            self.connect_to_frontend()
            try:
                self.print_to_console("Creating MPI Cluster")
                # self.changeStatus("Creating MPI Cluster")
                self.print_to_console("Execute vcluster-start %s %s" % (self.cluster_name, self.cluster_size))
                result_cluster_ip = self.frontend_shell.run(
                    ["./vcluster-start", self.cluster_name, str(self.cluster_size)],
                    cwd="vcluster")

                self.print_to_console(result_cluster_ip.output)
                p = re.compile("(?P<username>\S+)@(?P<floating_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
                m = p.search(result_cluster_ip.output)
                self.cluster_username = m.group('username')
                self.cluster_password = self.cluster_username
                self.cluster_ip = m.group('floating_ip')
                # print "%s@%s" % (self.cluster_username, self.cluster_ip)
                self.print_to_console("Cluster ip: %s" % self.cluster_ip)

                MPI_Cluster.objects.filter(pk=self.mpi_pk).update(cluster_ip=self.cluster_ip)

                self.connect_to_cluster(True)
                # for tool in self.supported_tools:
                self.activate_tool(self.supported_tools)
            except spur.ssh.ConnectionError as err:
                self.print_to_console (err.args)
                # print sys.exc_info()
                raise
                # raise('Cannot connection to ')
                # self.changeStatus("Error: Failed to connect to frontend.")
        else:
            self.connect_to_cluster()

        # update mpi_cluster status to ready
        self.print_to_console("Consumer now ready")
        MPI_Cluster.objects.filter(pk=self.mpi_pk).update(status=1)

    def run(self):
        self.connect_or_create()
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        channel = connection.channel()

        result = channel.queue_declare(exclusive=True, durable=True)

        channel.exchange_declare(exchange='topic_logs',
                                 type='topic')
        channel.queue_bind(exchange='topic_logs',
                           queue=result.method.queue,
                           routing_key=self.binding_key)

        channel.basic_consume(self.callback,
                              queue=result.method.queue,
                              no_ack=True)

        channel.start_consuming()

def handle_uploaded_file(f):
    with open('pogi.txt', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

ConsumerThreadManager().start()

# x = MPI_Cluster.objects.get(pk=55)
# curr_tool = json.loads(x.supported_tools)
# curr_tool.append("gamess")
# x.supported_tools = json.dumps(curr_tool)
# x.save()

# x = SkyLabFile.objects.get(pk=1).file #works

# x = SkyLabFile.objects.filter(toolactivity__pk=76) #using reverse m2m
# x = x[0]
# print x.file.name

# handle_uploaded_file(x)

application = get_wsgi_application()
