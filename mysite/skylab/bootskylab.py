from __future__ import print_function

import Queue  # queue for python 3
import json
import logging
import logging.config
import os
import re
import threading
import time

import spur
from django.conf import settings
from django.db.models.signals import post_save

from skylab.models import MPICluster, Task

def populate_tools():
    pass


def setup_logging(
        path=os.path.dirname(os.path.abspath(__file__)) + '/logs/skylab_log_config.json',
        default_level=logging.INFO,

):
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

class MPIThreadManager(object):
    def __init__(self):
        self.threadHash = {}
        self.logger = logging.getLogger(__name__)
        clusters = MPICluster.objects.exclude(status=5)
        self.logger.info("Creating MPIThreads")
        self._connected_to_frontend = threading.Event()

        self.frontend_shell = None
        init_thread = threading.Thread(target=self.connect_to_frontend)
        init_thread.start()

        for cluster in clusters:

            if cluster.id not in self.threadHash:
                print(cluster.cluster_name)
                t = MPIThread(cluster, self.frontend_shell)

                self.threadHash[cluster.id] = t
                t.start()

        post_save.connect(receiver=self.receive_mpi_cluster_from_post_save_signal, sender=MPICluster,
                          dispatch_uid="receive_mpi_from_post_save_signal")
        post_save.connect(receiver=self.receive_task_from_post_save_signal, sender=Task,
                          dispatch_uid="receive_task_from_post_save_signal")

        super(MPIThreadManager, self).__init__()

    def connect_to_frontend(self):
        if self.frontend_shell is None:
            self.frontend_shell = spur.SshShell(hostname=settings.FRONTEND_IP,
                                                username=settings.FRONTEND_USERNAME,
                                                password=settings.FRONTEND_PASSWORD,
                                                missing_host_key=spur.ssh.MissingHostKey.accept)
            while True:
                try:
                    self.logger.info("Connecting to frontend...")
                    # check if connection is sucessful
                    # from : http://stackoverflow.com/questions/28288533/check-if-paramiko-ssh-connection-is-still-alive
                    channel = self.frontend_shell._get_ssh_transport().send_ignore()
                    self._connected_to_frontend.set()
                    break
                except (spur.ssh.ConnectionError, EOFError) as e:
                    # print ("Error connecting to frontend")
                    self.logger.error("Error connecting to frontend", exc_info=True)
                finally:
                    time.sleep(5)
            self.logger.info("Connected to frontend...")

        return self.frontend_shell

    def get_frontend_shell(self):
        self._connected_to_frontend.wait()
        return self.frontend_shell


    def receive_task_from_post_save_signal(self, sender, instance, **kwargs):
        logging.info('Received Task #{0} for MPI #{1}'.format(instance.id, instance.mpi_cluster.cluster_name))
        # print('Received Task #{0} for MPI #{1}'.format(instance.id, instance.mpi_cluster.cluster_name))

        # append to queue
        self.threadHash[instance.mpi_cluster_id].add_task_to_queue(instance)

    def receive_mpi_cluster_from_post_save_signal(self, sender, instance, **kwargs):
        print("Received MPICluster #{0},{1}".format(instance.id, instance.cluster_name))
        pass


class MPIThread(threading.Thread):
    def __init__(self, mpi_cluster, manager):
        # current implementation. task_queue only has a single consumer.

        # This design can be improved and cater multiple consumers for this queue
        # In multiple consumers, this thread would be the producer
        # Consumers consume task queue, pass cluster_shell to consumer instances
        # Recommendation: Dynamic consumers spawn based on task intensity
        # If current task is light on resources regardless of expected running time,
        # A new consumer is signalled that it is allowed to consume

        self.task_queue = Queue.PriorityQueue()

        self._stop = threading.Event()
        self.manager = manager
        self.mpi_cluster = mpi_cluster
        self.frontend_shell = None
        self.cluster_shell = None
        self.logger = logging.getLogger(__name__)
        self.log_prefix = 'MPI [id:{0},name:{1}] : '.format(self.mpi_cluster.id, self.mpi_cluster.cluster_name)

        self.logger.info(self.log_prefix + 'Spawned MPI Thread')


        self.logger.info(self.log_prefix + "Populating task queue")
        # get tasks that are not finished yet
        tasks = Task.objects.filter(mpi_cluster=self.mpi_cluster.id).exclude(tasklog__status_code=200).exclude(
            tasklog__status_code=400)
        for task in tasks:
            print(self.log_prefix + 'Queueing task [id:{0},type:{1}]'.format(task.id, task.type))
            self.add_task_to_queue(task)

        super(MPIThread, self).__init__()

    # TODO: implement connect and create to cluster functions
    def connect_or_create(self):
        self.frontend_shell = self.manager.get_frontend_shell()
        if self.mpi_cluster.status == 0:  # create
            self.create_mpi_cluster()

        self.connect_to_cluster()

        # activate toolsets supported that are not yet activated
        # for toolset in self.mpi_cluster.supported_toolsets.all():
        #     if toolset not in self.mpi_cluster.activated_toolsets.all():
        #         self.activate_toolset(toolset)
        # changed tasks with type 1 are created instead for tool activation

        if self.mpi_cluster.status == 0:  # create
            pass
            # TODO: self.install_dependencies()
            # else:
            #     # set status to 1 (Connecting...)
            #     self.mpi_cluster.change_status(1)


            # pass

    def connect_to_cluster(self):
        self.cluster_shell = spur.SshShell(hostname=self.mpi_cluster.cluster_ip, username=settings.CLUSTER_USERNAME,
                                           password=settings.CLUSTER_PASSWORD,
                                           missing_host_key=spur.ssh.MissingHostKey.accept)  # TODO: test timeout

        while True:
            try:
                self.logger.info(self.log_prefix + "Connecting to cluster...")
                # check if connection is sucessful
                # from : http://stackoverflow.com/questions/28288533/check-if-paramiko-ssh-connection-is-still-alive
                channel = self.cluster_shell._get_ssh_transport().send_ignore()

                break
            except (spur.ssh.ConnectionError, EOFError) as e:
                # print ("Error connecting to frontend")
                self.logger.error(self.log_prefix + "Error connecting to cluster", exc_info=True)
                self.mpi_cluster.change_status(4)
            finally:
                time.sleep(5)
        self.logger.info(self.log_prefix + "Connected to cluster...")

    def activate_toolset(self, toolset):
        self.logger.debug(self.log_prefix + "Activating " + toolset.display_name)
        while True:
            command = "p2c-tools activate {0}".format(toolset.p2ctool_name)
            try:
                tool_activator = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                tool_activator.stdin_write(settings.CLUSTER_PASSWORD + "\n")
                tool_activator.wait_for_result()
                self.logger.info(self.log_prefix + "{0} is now activated.".format(toolset.display_name))
                self.logger.debug(self.log_prefix + tool_activator.wait_for_result().output)

                # TODO: refactor

                self.mpi_cluster.activated_toolsets.add(toolset)
                # MPICluster.objects.filter(pk=self.mpi_pk).update(supported_tools=toolset)
                break
            except spur.RunProcessError as err:
                self.logger.error(self.log_prefix + "No response from server. Retrying command ({0})".format(command),
                                  exc_info=True)

            except spur.ssh.ConnectionError as err:
                self.logger.error(self.log_prefix + "Connection Error to MPI Cluster", exc_info=True)
            finally:
                time.sleep(5)

    def create_mpi_cluster(self):
        self.logger.info(self.log_prefix + "Creating MPI Cluster")

        self.logger.debug(self.log_prefix + "Execute vcluster-stop {0} {1}".format(self.mpi_cluster.cluster_name,
                                                                                   self.mpi_cluster.cluster_size))
        self.frontend_shell.run(["./vcluster-stop", self.mpi_cluster.cluster_name, str(self.mpi_cluster.cluster_size)],
                                cwd="vcluster")  # to remove duplicates in case server restart while creating

        self.logger.debug(self.log_prefix + "Execute vcluster-start {0} {1}".format(self.mpi_cluster.cluster_name,
                                                                                    self.mpi_cluster.cluster_size))
        result_cluster_ip = self.frontend_shell.run(
            ["./vcluster-start", self.mpi_cluster.cluster_name, str(self.mpi_cluster.cluster_size)],
            cwd="vcluster")

        self.logger.debug(self.log_prefix + result_cluster_ip.output)
        p = re.compile("(?P<username>\S+)@(?P<floating_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        m = p.search(result_cluster_ip.output)
        # self.cluster_username = m.group('username')
        # self.cluster_password = self.cluster_username
        cluster_ip = m.group('floating_ip')
        # print "%s@%s" % (self.cluster_username, self.cluster_ip)
        # self.print_to_console("Cluster ip: %s" % self.cluster_ip)

        self.mpi_cluster.cluster_ip = cluster_ip
        self.mpi_cluster.save()
        self.logger.debug(self.log_prefix + 'Obtained cluster ip: {0}'.format(cluster_ip))

    def run(self):
        # initialization.wait() block waiting for initialization event to be set
        while not self._stop.isSet():

            self.logger.debug('MPIThread # {0} Waiting 5 seconds, before processing again'.format(self.mpi_cluster.id))
            event_is_set = self._stop.wait(5)
            self.logger.debug('MPIThread # {0} stop event set: {1}'.format(self.mpi_cluster.id, event_is_set))

            if event_is_set:
                self.logger.info('MPIThread # {0} Terminating ...'.format(self.mpi_cluster.id))
            else:

                # Todo: process queue
                # print(__name__)
                current_task = self.task_queue.get()[1]
                self.logger.info('MPIThread # {0} Processing task id:{1}'.format(self.mpi_cluster.id, current_task.id))

                # mod = importlib.import_module('{0}.executables'.format(current_task.tool.toolset.package_name))
                # print(mod)
                # TODO: handle mpi destroy
                # cls = getattr(mod, "Dummy")
                # cls()
                # executable_obj = cls(shell=self.cluster_shell, task=current_task)
                # executable_obj.run_tool()

    def add_task_to_queue(self, task):
        self.task_queue.put((task.type, task))
        task.change_status(status_code=101, status_msg="Task queued")
        self.logger.debug(self.log_prefix + 'Queued task [id:{0},type:{1}]'.format(task.id, task.type))
