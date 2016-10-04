from __future__ import print_function

import Queue  # queue for python 3
import importlib
import json
import logging
import logging.config
import math
import os
import re
import threading
import time

import spur
from django.conf import settings
from django.db.models.signals import post_save

from skylab.models import MPICluster, Task, ToolSet, ToolActivation, SkyLabFile

def populate_tools():
    pass


MAX_WAIT = settings.TRY_WHILE_NOT_EXIT_MAX_TIME

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
                t = MPIThread(cluster, self)

                self.threadHash[cluster.id] = t
                t.start()

        post_save.connect(receiver=self.receive_mpi_cluster_from_post_save_signal, sender=MPICluster,
                          dispatch_uid="receive_mpi_from_post_save_signal")
        post_save.connect(receiver=self.receive_task_from_post_save_signal, sender=Task,
                          dispatch_uid="receive_task_from_post_save_signal")

        # this may lead to duplicates on mpi create,
        # activate_toolset checks if the toolset is activated before execution
        post_save.connect(receiver=self.receive_toolactivation_from_post_save_signal, sender=ToolActivation,
                          dispatch_uid="receive_toolactivation_from_post_save_signal")

        super(MPIThreadManager, self).__init__()

    def connect_to_frontend(self):
        if self.frontend_shell is None:
            self.frontend_shell = spur.SshShell(hostname=settings.FRONTEND_IP,
                                                username=settings.FRONTEND_USERNAME,
                                                password=settings.FRONTEND_PASSWORD,
                                                missing_host_key=spur.ssh.MissingHostKey.accept)
            retries = 0
            exit_loop = False
            while not exit_loop:
                try:
                    self.logger.info("Connecting to frontend...")
                    # check if connection is sucessful
                    # from : http://stackoverflow.com/questions/28288533/check-if-paramiko-ssh-connection-is-still-alive
                    channel = self.frontend_shell._get_ssh_transport().send_ignore()
                    self._connected_to_frontend.set()
                    exit_loop = True  # exit loop

                except (spur.ssh.ConnectionError, EOFError) as e:
                    self.logger.error("Error connecting to frontend", exc_info=True)

                finally:
                    if not exit_loop:
                        retries += 1
                        wait_time = min(math.pow(2, retries), MAX_WAIT)
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

            self.logger.info("Connected to frontend...")

        return self.frontend_shell

    def get_frontend_shell(self):
        self._connected_to_frontend.wait()
        return self.frontend_shell

    def receive_toolactivation_from_post_save_signal(self, sender, instance, created, **kwargs):
        if created:
            logging.info(
                'Received ToolActivation #{0} ({1}) for MPI #{2}'.format(instance.id, instance.toolset.display_name,
                                                                         instance.mpi_cluster_id))
            print('Received ToolActivation #{0} ({1}) for MPI #{2}'.format(instance.id, instance.toolset.display_name,
                                                                           instance.mpi_cluster_id))

            self.threadHash[instance.mpi_cluster_id].add_task_to_queue(1, "self.activate_tool({0})".format(
                instance.toolset_id))

    def receive_task_from_post_save_signal(self, sender, instance, created, **kwargs):
        if created:
            logging.info('Received Task #{0} for MPI #{1}'.format(instance.id, instance.mpi_cluster.cluster_name))

            # append to queue
            self.threadHash[instance.mpi_cluster_id].add_task_to_queue(instance.priority, instance)

    def receive_mpi_cluster_from_post_save_signal(self, sender, instance, created, **kwargs):
        if created:
            print("Received MPICluster #{0},{1}".format(instance.id, instance.cluster_name))
            t = MPIThread(instance, self)
            self.threadHash[instance.id] = t
            t.start()



class MPIThread(threading.Thread):
    def __init__(self, mpi_cluster, manager):
        # current implementation. task_queue only has a single consumer.

        """"
        This design can be improved and cater multiple consumers for this queue
        In multiple consumers, this thread would be the producer
        Consumers consume task queue, pass cluster_shell to consumer instances
        Recommendation: Dynamic consumers spawn based on task intensity
        If current task is light on resources regardless of expected running time,
        A new consumer is signalled that it is allowed to consume
        """

        self.task_queue = Queue.PriorityQueue()

        self._stop = threading.Event()
        self._ready = threading.Event()
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
            print(self.log_prefix + 'Queueing task [id:{0},priority:{1}]'.format(task.id, task.priority))
            self.add_task_to_queue(task.priority, task)

        unactivated_toolsets = self.mpi_cluster.toolsets.filter(toolactivation__activated=False)
        for toolset in unactivated_toolsets:
            self.add_task_to_queue(1, "self.activate_toolset({0})".format(toolset.id))

        init_thread = threading.Thread(target=self.connect_or_create)
        init_thread.start()  # sets event _connection on finish

        super(MPIThread, self).__init__()

    # TODO: implement connect and create to cluster functions
    def connect_or_create(self):

        self.frontend_shell = self.manager.get_frontend_shell()  # get working frontend_shell
        if self.mpi_cluster.status == 0:  # create
            self.create_mpi_cluster()
        else:
            self.mpi_cluster.change_status(1)

        self.connect_to_cluster()  #get working cluster shell

        if self.mpi_cluster.status == 0:  # create
            self.install_dependencies()  #zip
            self.mpi_cluster.change_status(1)

        self.mpi_cluster.change_status(2)  # cluster available
        self._ready.set()

    def connect_to_cluster(self):
        self.cluster_shell = spur.SshShell(hostname=self.mpi_cluster.cluster_ip, username=settings.CLUSTER_USERNAME,
                                           password=settings.CLUSTER_PASSWORD,
                                           missing_host_key=spur.ssh.MissingHostKey.accept)  # TODO: test timeout
        self.test_cluster_connection()

    def test_cluster_connection(self):
        retries = 0
        exit_loop = False
        while not exit_loop:
            try:
                self.logger.info(self.log_prefix + "Testing connection to cluster...")
                # check if connection is sucessful
                # from : http://stackoverflow.com/questions/28288533/check-if-paramiko-ssh-connection-is-still-alive
                channel = self.cluster_shell._get_ssh_transport().send_ignore()
                exit_loop = True  # exit loop

            except (spur.ssh.ConnectionError, EOFError) as e:
                # print ("Error connecting to frontend")
                self.logger.error(self.log_prefix + "Error connecting to cluster", exc_info=True)
                self.mpi_cluster.change_status(4)

            finally:
                if not exit_loop:
                    retries += 1
                    wait_time = min(math.pow(2, retries), MAX_WAIT)
                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                    time.sleep(wait_time)

        self.logger.info(self.log_prefix + "Connected to cluster...")

    def install_dependencies(self):
        retries = 0
        exit_loop = False
        while not exit_loop:
            command = "sudo ifconfig eth0 mtu 1440"
            ssh_fix = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
            ssh_fix.stdin_write(settings.CLUSTER_PASSWORD + "\n")
            self.logger.debug(self.log_prefix + 'Set mtu to 1440')

            try:
                # update p2c-tools
                self.logger.debug(self.log_prefix + "Updating p2c-tools")
                command = "rm p2c-tools*"
                self.cluster_shell.run(["sh", "-c", command])
                print("Updating p2c-tools")
                self.cluster_shell.run(["wget", "10.0.3.10/downloads/p2c/p2c-tools"])
                self.cluster_shell.run(["chmod", "755", "p2c-tools"])
                p2c_updater = self.cluster_shell.spawn(["./p2c-tools"], use_pty=True)
                p2c_updater.stdin_write(settings.CLUSTER_PASSWORD + "\n")
                print(p2c_updater.wait_for_result().output)
                print(self.cluster_shell.run(["p2c-tools"]).output)
                self.logger.debug(self.log_prefix + "Updated p2c-tools")

                # sudo apt-get update
                self.logger.debug(self.log_prefix + "Updating apt-get")
                command = "sudo apt-get update"
                apt_get_update_shell = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                apt_get_update_shell.stdin_write(settings.CLUSTER_PASSWORD + "\n")
                self.logger.debug(self.log_prefix + apt_get_update_shell.wait_for_result().output)
                self.logger.debug(self.log_prefix + "Updated apt-get")

                # install zip
                self.logger.debug(self.log_prefix + "Installing zip")
                command = "sudo apt-get install zip -y"
                zip_shell = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                zip_shell.stdin_write(settings.CLUSTER_PASSWORD + "\n")
                # zip_shell.stdin_write("Y\n")
                self.logger.debug(self.log_prefix + zip_shell.wait_for_result().output)
                self.logger.debug(self.log_prefix + "Installed zip")
                exit_loop = True  # exit loop

            except spur.RunProcessError:
                # run process error with return code -1 (no value returned) is returned during unresponsive connection
                self.logger.error(self.log_prefix + 'No response from cluster.',
                                  exc_info=True)

            except spur.ssh.ConnectionError:
                self.logger.error(self.log_prefix + "Connection Error to MPI Cluster", exc_info=True)

            finally:
                if not exit_loop:
                    retries += 1
                    wait_time = min(math.pow(2, retries), MAX_WAIT)
                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                    time.sleep(wait_time)

    def activate_toolset(self, toolset_id):
        # check if toolset is already activated
        tool_activation_instance = ToolActivation.objects.get(toolset=toolset_id, mpi_cluster=self.mpi_cluster.id)
        if not tool_activation_instance.activated:
            toolset = ToolSet.objects.get(pk=toolset_id)

            self.logger.debug(self.log_prefix + "Activating " + toolset.display_name)
            retries = 0
            exit_loop = False
            while not exit_loop:
                command = "p2c-tools activate {0}".format(toolset.p2ctool_name)
                try:
                    tool_activator = self.cluster_shell.spawn(["sh", "-c", command], use_pty=True)
                    tool_activator.stdin_write(settings.CLUSTER_PASSWORD + "\n")
                    tool_activator.wait_for_result()
                    self.logger.info(self.log_prefix + "{0} is now activated.".format(toolset.display_name))
                    self.logger.debug(self.log_prefix + tool_activator.wait_for_result().output)
                    print(self.log_prefix + tool_activator.wait_for_result().output)

                    # set activated to true after installation
                    tool_activation_instance.refresh_from_db()
                    tool_activation_instance.activated = True
                    tool_activation_instance.save()

                    exit_loop = True  #exit loop
                except spur.RunProcessError:
                    self.logger.error(
                        self.log_prefix + "No response from server. Command: ({0})".format(command),
                        exc_info=True)

                except spur.ssh.ConnectionError:
                    self.logger.error(self.log_prefix + "Connection Error to MPI Cluster", exc_info=True)

                finally:
                    if not exit_loop:
                        retries += 1
                        wait_time = min(math.pow(2, retries), MAX_WAIT)
                        self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                        time.sleep(wait_time)

    def create_mpi_cluster(self):
        # TODO: test if works
        self.logger.info(self.log_prefix + "Creating MPI Cluster")

        retries = 0
        exit_loop = False
        while not exit_loop:
            command = "./vcluster-stop {0} {1}".format(self.mpi_cluster.cluster_name, self.mpi_cluster.cluster_size)
            try:
                self.logger.debug(self.log_prefix + "Execute " + command)
                self.frontend_shell.run(["sh", "-c", command], cwd="vcluster")
                # self.frontend_shell.run(["./vcluster-stop", self.mpi_cluster.cluster_name, str(self.mpi_cluster.cluster_size)],
                #                         cwd="vcluster")  # to remove duplicates in case server restart while creating

                command = "./vcluster-start {0} {1}".format(self.mpi_cluster.cluster_name,
                                                            self.mpi_cluster.cluster_size)
                self.logger.debug(self.log_prefix + "Execute " + command)
                result_cluster_ip = self.frontend_shell.run(["sh", "-c", command], cwd="vcluster")

                exit_loop = True  # exit loop
            except spur.RunProcessError:
                self.logger.error(
                    self.log_prefix + "No response from server. Command: ({0})".format(command),
                    exc_info=True)

            except spur.ssh.ConnectionError:
                self.logger.error(self.log_prefix + "Connection Error to MPI Cluster", exc_info=True)
            finally:
                if not exit_loop:
                    retries += 1
                    wait_time = min(math.pow(2, retries), MAX_WAIT)
                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                    time.sleep(wait_time)

        print(self.log_prefix + result_cluster_ip.output)
        self.logger.debug(self.log_prefix + result_cluster_ip.output)
        p = re.compile("(?P<username>\S+)@(?P<floating_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        m = p.search(result_cluster_ip.output)
        # self.cluster_username = m.group('username')
        # self.cluster_password = self.cluster_username
        cluster_ip = m.group('floating_ip')
        # print "%s@%s" % (self.cluster_username, self.cluster_ip)
        # self.print_to_console("Cluster ip: %s" % self.cluster_ip)
        self.mpi_cluster.refresh_from_db()
        self.mpi_cluster.cluster_ip = cluster_ip
        self.mpi_cluster.save()
        self.logger.debug(self.log_prefix + 'Obtained cluster ip: {0}'.format(cluster_ip))

    def run(self):
        # block waiting for connected event to be set
        print("Waiting for connection")
        self._ready.wait()

        while not self._stop.isSet():

            self.logger.debug(self.log_prefix + 'Waiting 5 seconds, before processing again')
            event_is_set = self._stop.wait(5)

            # test cluster connection before processing
            self.test_cluster_connection()

            if event_is_set:
                self.logger.info(self.log_prefix + 'Terminating ...')
            else:
                try:
                    print("Getting queue object")
                    queue_obj = self.task_queue.get()

                    if queue_obj[0] == 1:  # p2c-tools activate are always priority # 1
                        self.logger.debug(self.log_prefix + "Running " + queue_obj[1])
                        exec (queue_obj[1])

                    elif isinstance(queue_obj[1], Task):
                        current_task = queue_obj[1]
                        current_task.refresh_from_db()  # refresh instance
                        task_log_prefix = '[Task {0} ({1})] : '.format(current_task.id, current_task.tool.display_name)
                        self.logger.info('{0}Processing {1}'.format(self.log_prefix, task_log_prefix))

                        # clean task output skylabfile, with a signal receiver deleting the actual files
                        self.logger.debug(self.log_prefix)
                        SkyLabFile.objects.filter(task=current_task, type=2).delete()
                        mod = importlib.import_module('{0}.executables'.format(current_task.tool.toolset.package_name))
                        print(mod)

                        cls = getattr(mod, current_task.tool.executable_name)
                        # cls()
                        executable_obj = cls(shell=self.cluster_shell, task=current_task, logger=self.logger,
                                             log_prefix=self.log_prefix + task_log_prefix)
                        executable_obj.run_tool()
                        # executable_obj.clear_or_create_dirs()
                        # executable_obj.handle_input_files()

                    self.task_queue.task_done()
                except Queue.Empty:
                    if self.mpi_cluster.queued_for_deletion:  # if queue is empty and cluster is queued for deletion
                        self._stop.set()
                        self.logger.info(self.log_prefix + "Deleting MPI Cluster")

                        retries = 0
                        exit_loop = False
                        while not exit_loop:
                            command = "./vcluster-stop {0} {1}".format(self.mpi_cluster.cluster_name,
                                                                       self.mpi_cluster.cluster_size)
                            try:
                                self.logger.debug(self.log_prefix + "Execute " + command)
                                self.frontend_shell.run(["sh", "-c", command], cwd="vcluster")
                                # self.frontend_shell.run(["./vcluster-stop", self.mpi_cluster.cluster_name,
                                # str(self.mpi_cluster.cluster_size)],
                                #                         cwd="vcluster")  # to remove duplicates in case server restart while creating
                                exit_loop = True  # exit loop

                            except spur.RunProcessError:
                                self.logger.error(
                                    self.log_prefix + "No response from server. Command: ({0})".format(command),
                                    exc_info=True)

                            except spur.ssh.ConnectionError:
                                self.logger.error(self.log_prefix + "Connection Error to MPI Cluster", exc_info=True)

                            finally:
                                if not exit_loop:
                                    retries += 1
                                    wait_time = min(math.pow(2, retries), MAX_WAIT)
                                    self.logger.debug('Waiting {0}s until next retry'.format(wait_time))
                                    time.sleep(wait_time)

                        self.mpi_cluster.toolsets.clear()  # clear toolsets, toolactivation
                        self.mpi_cluster.change_status(5)

    def add_task_to_queue(self, priority, task):
        self.task_queue.put((priority, task))
        if isinstance(task, Task):
            task.change_status(status_code=101, status_msg="Task queued")
            self.logger.debug(self.log_prefix + 'Queued task [id:{0},priority:{1}]'.format(task.id, priority))
