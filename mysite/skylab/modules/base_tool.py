import os.path
from abc import abstractmethod

import pika
from django import forms

from skylab.models import SkyLabFile


class MPIModelChoiceField(forms.ModelChoiceField):
	def label_from_instance(self, obj):
		return "%s (nodes : %d)" % (obj.cluster_name, obj.cluster_size)


def create_input_skylab_file(tool_activity, directory, file):
	new_file = SkyLabFile.objects.create(upload_path="tool_activity_%d/%s" % (tool_activity.id, directory),
										 file=file,
										 filename=file.name)
	tool_activity.input_files.add(new_file)
	return "%s/%s" % (new_file.upload_path, new_file.filename)


# source: http://stackoverflow.com/questions/14819681/upload-files-using-sftp-in-python-but-create-directories-if-path-doesnt-exist
def mkdir_p(sftp, remote_directory):
	"""Change to this directory, recursively making new folders if needed.
	Returns True if any folders were created."""
	if remote_directory == '/':
		# absolute path so change directory to root
		sftp.chdir('/')
		return
	if remote_directory == '':
		# top-level relative directory must exist
		return
	try:
		sftp.chdir(remote_directory)  # sub-directory exists
	except IOError:
		dirname, basename = os.path.split(remote_directory.rstrip('/'))
		mkdir_p(sftp, dirname)  # make parent directories
		sftp.mkdir(basename)  # sub-directory missing, so created it
		sftp.chdir(basename)
		return True


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
