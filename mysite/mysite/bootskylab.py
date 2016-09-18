import Queue  # queue for python 3
import threading
import time

from skylab.models import MPICluster


def populate_tools():
    pass


class MPIThreadManager(threading.Thread):
    def __init__(self):
        super(MPIThreadManager, self).__init__()
        self.threadHash = {}

    def addMPIThread(self, thread):
        self.threadHash[thread.mpi_cluster.id] = thread

    def removeMPIThread(self, id):
        self.threadHash.pop(id, None)

    def run(self):
        clusters = MPICluster.objects.exclude(status=4)


class MPIThread(threading.Thread):
    def __init__(self):
        super(MPIThread, self).__init__()
        self.task_queue = Queue.Queue()
        self.stop_request = threading.Event()
        self.connected = False

        # self.mpi_cluster = get mpi_cluster
        self.frontend_shell = None
        self.cluster_shell = None
        # TODO: populate queue from current tasks in database

    def run(self):
        pass
        # while not self.stop_request.isSet():
        #   try: pop queue except empty
        #  TODO: make priority queue highest= tool task, lowest = delete cluster

    def connect_to_cluster(self, initialize=False):
        pass

    def create_cluster(self):
        pass

    def delete_cluster(self):
        self.stop_request.set()
        pass

    def print_to_console(self, msg, prprint=False):
        localtime = time.asctime(time.localtime(time.time()))
        if prprint:
            # print("MPI Thread {0} ({1}): {2}".format(self.mpi_cluster_id, localtime, pprint.pformat(msg)))
            pass
        else:
            #  print("MPI Thread {0} ({1}): {2}".format(self.mpi_cluster_id, localtime, msg))
            pass
