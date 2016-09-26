from __future__ import print_function

import Queue  # queue for python 3
import json
import logging
import logging.config
import os
import threading

from skylab.models import MPICluster


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


setup_logging()

class MPIThread(threading.Thread):
    def __init__(self, mpi_cluster):
        self._stop = threading.Event()
        self.task_queue = Queue.PriorityQueue()
        self.mpi_cluster = mpi_cluster
        self.logger = logging.getLogger(__name__)


        self.logger.info("Created thread for MPI #{0}({1})".format(self.mpi_cluster.id, self.mpi_cluster.cluster_name))
        # add the handlers to the logger

        # TODO: populate task_queue with tasks


        super(MPIThread, self).__init__()

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
