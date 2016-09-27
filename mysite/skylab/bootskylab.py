from __future__ import print_function

import Queue  # queue for python 3
import importlib
import json
import logging
import logging.config
import os
import threading

from skylab.models import MPICluster, Task


def populate_tools():
    pass


class MPIThreadManager(object):
    def __init__(self):
        self.threadHash = {}
        self.logger = logging.getLogger(__name__)
        clusters = MPICluster.objects.exclude(status=5)
        self.logger.info("Creating MPIThreads")
        for cluster in clusters:

            if cluster.id not in self.threadHash:
                print(cluster.cluster_name)
                t = MPIThread(cluster)

                self.threadHash[cluster.id] = t
                t.start()


        super(MPIThreadManager, self).__init__()

    def receive_task_from_post_save_signal(self, sender, instance, **kwargs):
        # logging.info()
        print('Received Task #{0} for MPI #{1}'.format(instance.id, instance.mpi_cluster.cluster_name))

        # TODO: append to queue
        # self.threadHash[cluster_id].add_task(instance)
        # instance.change_status(status_code=101, status_msg="Task queued")
        pass

    def receive_mpi_cluster_from_post_save_signal(self, sender, instance, **kwargs):
        print("Received MPICluster #{0},{1}".format(instance.id, instance.cluster_name))
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

class MPIThread(threading.Thread):
    # TODO: implement connect and create to cluster functions
    def __init__(self, mpi_cluster):
        # current implementation. task_queue only has a single consumer.
        # This design can be improved and cater multiple consumers for this queue
        self.task_queue = Queue.PriorityQueue()

        self._stop = threading.Event()
        self.mpi_cluster = mpi_cluster
        self.logger = logging.getLogger(__name__)
        self.log_prefix = 'MPI [id:{0},name:{1}] : '.format(self.mpi_cluster.id, self.mpi_cluster.cluster_name)

        self.logger.info(self.log_prefix + 'Spawned MPI Thread')
        # add the handlers to the logger


        self.logger.info(self.log_prefix + "Populating task queue")

        # get tasks that are not finished yet
        tasks = Task.objects.filter(mpi_cluster=self.mpi_cluster.id).exclude(tasklog__status_code=200).exclude(
            tasklog__status_code=400)
        for task in tasks:
            self.logger.debug(self.log_prefix + 'Queueing task [id:{0},type:{1}]'.format(task.id, task.type))
            # print(self.log_prefix+'Queueing task [id:{0},type:{1}]'.format(task.id, task.type))
            self.add_task_to_queue(task)

        super(MPIThread, self).__init__()

    def add_task_to_queue(self, task):
        self.task_queue.put((task.type, task))

    def run(self):
        while not self._stop.isSet():

            self.logger.debug('MPIThread # {0} Waiting 5 seconds, before processing again'.format(self.mpi_cluster.id))
            event_is_set = self._stop.wait(5)
            self.logger.debug('MPIThread # {0} stop event set: {1}'.format(self.mpi_cluster.id, event_is_set))

            if event_is_set:
                self.logger.info('MPIThread # {0} Terminating ...'.format(self.mpi_cluster.id))
            else:
                self.logger.info('MPIThread # {0} Processing ...'.format(self.mpi_cluster.id))
                # Todo: process queue
                print(__name__)
                current_task = self.task_queue.get()[1]

                mod = importlib.import_module('{0}.executables'.format(current_task.tool.toolset.package_name))
                print(mod)
                # TODO: handle mpi destroy
                # cls = getattr(mod, "Dummy")
                # cls()
                # executable_obj = cls(shell=self.cluster_shell, task=current_task)
                # executable_obj.run_tool()
