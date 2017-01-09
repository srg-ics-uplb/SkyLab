import importlib
import json
import pprint
import re
import sys
import threading
import time

import pika
import spur
from django.conf import settings

from skylab.models import MPICluster

frontend_ip = settings.FRONTEND_IP
frontend_username = settings.FRONTEND_USERNAME
frontend_password = settings.FRONTEND_PASSWORD

cluster_username = settings.CLUSTER_USERNAME
cluster_password = settings.CLUSTER_PASSWORD


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
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'], binding_key="skylab.consumer.%d" % data['pk'],
                                                         cluster_name=data['cluster_name'],
                                                         cluster_size=data['cluster_size'],
                                                         supported_tools=data['tools'])
        elif data['actions'] == "connect_cluster":
            self.threadHash[data['pk']] = ConsumerThread(pk=data['pk'], binding_key="skylab.consumer.%d" % data['pk'],
                                                         cluster_name=data['cluster_name'],
                                                         cluster_size=data['cluster_size'],
                                                         cluster_ip=data['cluster_ip'],
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
        clusters = MPICluster.objects.exclude(status=4)
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
        self.print_to_console("Created Consumer Thread ID: %d, Key: %s Cluster {name: %s, size: %d, ip:%r}" % (
            self.mpi_pk, self.binding_key,
            self.cluster_name, self.cluster_size, self.cluster_ip))
        self.connected = False
        self.status = 0
        super(ConsumerThread, self).__init__(*args, **kwargs)
        init_thread = threading.Thread(target=self.connect_or_create)
        init_thread.start()
        # self.setDaemon(True)

    def print_to_console(self, msg, prprint=False):
        localtime = time.asctime(time.localtime(time.time()))
        if prprint:
            print("Consumer Thread {0} ({1}): {2}".format(self.mpi_pk, localtime, pprint.pformat(msg)))
        else:
            print("Consumer Thread {0} ({1}): {2}".format(self.mpi_pk, localtime, msg))

    def send_mpi_message(self, routing_key, body):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        channel = connection.channel()

        channel.exchange_declare(exchange='topic_logs',
                                 type='topic')

        channel.confirm_delivery()

        channel.basic_publish(exchange='topic_logs',
                              routing_key=routing_key,
                              body=body,
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # make message persistent
                              ), mandatory=True)

        self.print_to_console(" [x] Sent %r:%r" % (routing_key, "body:%r" % body))
        connection.close()

    def callback(self, channel, method, properties, body):
        while not self.connected:
            time.sleep(10)
            print ("Waiting to connect")
        # self.status = 1
        self.print_to_console("Received : %r" % body)
        data = json.loads(body)
        # self.print_to_console("Received %s" % data)
        if data['actions'] == "use_tool":
            selected_tool = data['tool']
            selected_executable = "%sExecutable" % ''.join(word.title() for word in data['param_executable'].split(' '))
            self.print_to_console("Using %s : %s" % (selected_tool, selected_executable))
            # mod = __import__("%s.%s.executables" % (settings.SKYLAB_MODULES_PACKAGE, selected_tool), globals(),
            #                  locals(),
            #                  [selected_executable], -1)
            mod = importlib.import_module('{0}.{1}.executables'.format(settings.SKYLAB_MODULES_PACKAGE, selected_tool))
            cls = getattr(mod, selected_executable)
            executable_obj = cls(shell=self.cluster_shell, id=data['activity'])
            executable_obj.run_tool()

            # self.status = 0

    def connect_to_frontend(self):
        try:
            self.print_to_console("Connecting to Frontend {ip: %s; username: %s, pass: %s}" % (
                frontend_ip, frontend_username, frontend_password))
            self.frontend_shell = spur.SshShell(hostname=frontend_ip,
                                                username=frontend_username,
                                                password=frontend_password,
                                                missing_host_key=spur.ssh.MissingHostKey.accept)

        except:
            self.print_to_console("Error: Failed to connect to frontend")
            self.print_to_console(sys.exc_info())

    def connect_to_cluster(self, create=False):
        try:
            self.cluster_shell = spur.SshShell(hostname=self.cluster_ip, username=cluster_username,
                                               password=cluster_password,
                                               missing_host_key=spur.ssh.MissingHostKey.accept)
            self.print_to_console("Connecting to MPI Cluster")
            if create:
                self.update_p2c()
                self.activate_tool(self.supported_tools)
                while True:
                    try:
                        self.print_to_console("Updating apt-get")
                        command = "sudo apt-get update"
                        zip_shell = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                        zip_shell.stdin_write(cluster_password + "\n")
                        self.print_to_console(zip_shell.wait_for_result().output)

                        self.print_to_console("Installing zip")
                        command = "sudo apt-get install zip -y"
                        zip_shell = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                        zip_shell.stdin_write(cluster_password + "\n")
                        # zip_shell.stdin_write("Y\n")
                        self.print_to_console(zip_shell.wait_for_result().output)
                        break
                    except spur.RunProcessError as err:
                        if err.return_code == -1:  # no return code received
                            self.logger.error(
                                self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                        else:
                            self.logger.error(self.log_prefix + 'RuntimeError: ' + err.message)



        except spur.ssh.ConnectionError as err:
            self.print_to_console("Error: Failed to connect to MPI cluster.")
            # self.print_to_console(sys.exc_info())
            self.print_to_console(err.args)
            raise

    def activate_tool(self, tool_name):
        self.print_to_console("Activating %s" % tool_name)
        while True:
            try:
                command = "p2c-tools activate {0}".format(tool_name)
                tool_activator = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                tool_activator.stdin_write(cluster_password + "\n")
                tool_activator.wait_for_result()
                self.print_to_console("{0} is now activated.".format(tool_name))
                self.print_to_console(tool_activator.wait_for_result().output)
                MPICluster.objects.filter(pk=self.mpi_pk).update(supported_tools=tool_name)
                break
            except spur.RunProcessError as err:
                if err.return_code == -1:  # no return code received
                    self.logger.error(
                        self.log_prefix + 'No response from server. Retrying command ({0})'.format(command))
                else:
                    self.logger.error(self.log_prefix + 'RuntimeError: ' + err.message)
                # else:
                #     break
            except spur.ssh.ConnectionError as err:
                self.print_to_console("Connection Error to MPI Cluster")
                self.print_to_console(err.args)

    def update_p2c(self):
        self.cluster_shell.run(["sh", "-c", "rm p2c-tools*"])
        self.print_to_console("Updating p2c-tools")
        self.cluster_shell.run(["wget", "10.0.3.10/downloads/p2c/p2c-tools"])
        self.cluster_shell.run(["chmod", "755", "p2c-tools"])
        p2c_updater = self.cluster_shell.spawn(["./p2c-tools"], use_pty=True)
        p2c_updater.stdin_write(cluster_password + "\n")
        self.print_to_console(p2c_updater.wait_for_result().output)
        self.print_to_console(self.cluster_shell.run(["p2c-tools"]).output)

    def connect_or_create(self):
        if self.cluster_ip is None:  # exec vcluster-create
            self.connect_to_frontend()
            try:
                self.print_to_console("Creating MPI Cluster")
                # self.changeStatus("Creating MPI Cluster")

                self.print_to_console("Execute vcluster-stop %s %s" % (self.cluster_name, self.cluster_size))
                self.frontend_shell.run(["./vcluster-stop", self.cluster_name, str(self.cluster_size)],
                                        cwd="vcluster")  # to remove duplicates in case server restart while creating
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

                MPICluster.objects.filter(pk=self.mpi_pk).update(cluster_ip=self.cluster_ip)

                self.connect_to_cluster(True)
                # for tool in self.supported_tools:

                self.connected = True

            except spur.ssh.ConnectionError as err:
                self.print_to_console(err.args)
                # print sys.exc_info()
                raise
                # raise('Cannot connection to ')
                # self.changeStatus("Error: Failed to connect to frontend.")
        else:
            self.connect_to_cluster()
            self.connected = True

        # update mpi_cluster status to ready
        self.print_to_console("Consumer now ready")
        MPICluster.objects.filter(pk=self.mpi_pk).update(status=1)

    def run(self):
        # threading.Thread(target=self.connect_or_create())
        # self.connect_or_create()
        connection = pika.BlockingConnection(pika.ConnectionParameters(heartbeat_interval=0,
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
