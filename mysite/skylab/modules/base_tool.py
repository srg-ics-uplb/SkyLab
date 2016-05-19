from abc import abstractmethod

import pika

def send_mpi_message(routing_key, body):
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
                          ))

    print(" [x] Sent %r:%r" % (routing_key, "body:%r" % body))
    connection.close()

class P2CToolGeneric(object):
	# frontend_ip = "10.0.3.101"
	# frontend_username = "user"
	# frontend_password = "excellence"

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def handle_input_files(self, *args, **kwargs):
        pass
		# raise not implemented error

    @abstractmethod
    def run_tool(self, *args, **kwargs):
        pass
		#raise not

    @abstractmethod
    def handle_output_files(self, *args, **kwargs):
        pass

    @abstractmethod
    def changeStatus(self, status):
        pass
