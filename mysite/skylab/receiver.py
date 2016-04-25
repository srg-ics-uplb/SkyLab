from __future__ import absolute_import

import re
import sys

import spur

global n
n = 1
import json
import pika
import threading

frontend_ip = "10.0.3.101"
frontend_username = "user"
frontend_password = "excellence"

cluster_username = "mpiuser"
cluster_password = "mpiuser"

MAX_CONSUMERS_PER_CLUSTER = 1



class ConsumerThreadManager(threading.Thread):

    def __init__(self):
        # TODO: check database for current mpi clusters -> create consumer threads for each
        self.threadHash = {}
        self.binding_key = "skylab.mpi.*"
        super(ConsumerThreadManager, self).__init__()

    def callback(self, channel, method, properties, body):
        # TODO: run create_mpi_cluster()
        #        on success add consumer thread
        data = json.loads(body)
        print "ConsumerThreadManager: Received %s" % data
        if data['actions'] == "create_cluster":
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'],binding_key="skylab.consumer.%r" % data['pk'],
                                                         cluster_name=data['cluster_name'],cluster_size=data['cluster_size'],
                                                         supported_tools=data['tools'])
        elif data['actions'] == "connect_cluster":
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'],binding_key="skylab.consumer.%r" % data['pk'],
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
        result = {}
        result['received_body'] = body
        result = json.dumps(result)
        self.send_mpi_message("skylab.results.%d" % self.mpi_pk, result)
        result = json.dumps(result)
        # TODO: if data['tool'] .. .
        # print("Method: {}".format(method))
        # print("Properties: {}".format(properties))
        #
        # data = json.loads(body)
        # print data['cluster_id']
        # print("ID: {}".format(data['cluster_id']))
        # print("Name: {}".format(data['cluster_name']))
        # print('Size: {}'.format(data['cluster_size']))
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

    def connect_to_cluster(self):
        try:
            self.cluster_shell = spur.SshShell(hostname=self.cluster_ip, username=cluster_username,
                                               password=cluster_password,
                                               missing_host_key=spur.ssh.MissingHostKey.accept)
            self.print_to_console("Connecting to MPI Cluster")
            self.update_p2c()

        except:  # spur.ssh.ConnectionError
            self.print_to_console("Error: Failed to connect to MPI cluster.")
            self.print_to_console(sys.exc_info())

    def activate_tool(self,tool_name):
        self.print_to_console("Activating %s" % tool_name)
        output = self.cluster_shell.run(["p2c-tools", "activate", tool_name])
        self.print_to_console(output.output)
        p = re.compile("export\s(?P<path>PATH.+)")
        m = p.search(output.output)
        if m is not None:
            output = self.cluster_shell.run(["sh","-c","export",m.group('path')])
            self.print_to_console(output.output)



    def update_p2c(self):
        self.print_to_console("Updating p2c-tools")
        self.cluster_shell.run(["wget", "10.0.3.10/downloads/p2c/p2c-tools"])
        self.cluster_shell.run(["chmod", "755", "p2c-tools"])
        p2c_updater = self.cluster_shell.spawn(["./p2c-tools"], use_pty=True)
        p2c_updater.stdin_write(cluster_password + "\n")
        self.print_to_console(p2c_updater.wait_for_result().output)
        self.print_to_console(self.cluster_shell.run(["p2c-tools"]).output)

    def connect_or_create(self):    #TODO: chec
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

                result = {}
                result['pk'] = self.mpi_pk
                result['model'] = "mpi_cluster"
                result['actions'] = ["update_ip"]
                result['cluster_ip'] = self.cluster_ip
                result = json.dumps(result)

                self.send_mpi_message("skylab.results.%s" % self.mpi_pk, result)

                self.connect_to_cluster()
                for tool in self.supported_tools:
                    self.activate_tool(tool)
            except:  # spur.ssh.ConnectionError
                print sys.exc_info()
                # self.changeStatus("Error: Failed to connect to frontend.")
        else:
            self.connect_to_cluster()

        result = {}
        result['pk'] = self.mpi_pk
        result['model'] = "mpi_cluster"
        result['actions'] = ["update_status"]
        result['status'] = 1
        result = json.dumps(result)

        self.send_mpi_message("skylab.results.%s" % self.mpi_pk, result)

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

ConsumerThreadManager().start()

# ConsumerThread(id=1,binding_key="skylab.tools.*").start()
# ConsumerThread(id=2,binding_key="skylab.msg").start()

