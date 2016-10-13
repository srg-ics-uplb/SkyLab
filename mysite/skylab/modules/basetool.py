import os.path
from abc import abstractmethod

import pika
from django.conf import settings

from skylab.models import SkyLabFile


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


class P2CToolGeneric(object):  # parent class for all skylab.modules.-.executables
	# functions are made to be as generic as possible for future simplification of executable creation process

	def __init__(self, **kwargs):
		self.shell = kwargs.get('shell')  # cluster shell
		self.task = kwargs.get('task')
		self.logger = kwargs.get('logger')
		self.log_prefix = kwargs.get('log_prefix', '')
		self.remote_task_dir = os.path.join(settings.REMOTE_BASE_DIR, self.task.task_dirname)
		self.working_dir = self.remote_task_dir  # dir where tool commands will be executed

	def clear_or_create_dirs(self, **kwargs):
		# clean task output skylabfile, with a signal receiver deleting the actual files
		self.logger.debug(self.log_prefix + "Clearing attached output files if any")
		SkyLabFile.objects.filter(task=self.task, type=2).delete()

		additional_dirs = kwargs.get('additional_dirs', [])
		task_remote_subdirs = kwargs.get('task_remote_subdirs', [])

		clear_or_create = 'if [ -d {0} ]; then rm -rf {0}/*; else mkdir -p {0}; fi'
		if additional_dirs:
			for directory in additional_dirs:
				if directory.startswith('/mirror/'):  # restrict to dirs for /mirror/
					self.logger.debug(self.log_prefix + 'Clear or create {0}'.format(directory))
					self.shell.run(
						['sh', '-c', clear_or_create.format(directory)])
				else:
					self.logger.warning(
						self.log_prefix + 'Ignored {0}. Directory must start with /mirror/'.format(directory))

		# ssh shell delete is faster than sftp:
		# reference: http://superuser.com/questions/1015430/why-does-deleting-a-directory-take-so-long-on-sftp

		# sftp version
		# remote_path = self.working_dir
		# sftp = self.shell._open_sftp_client()
		# remote_files = sftp.listdir(path=remote_path)
		# for remote_file in remote_files:
		#     remote_filepath = os.path.join(remote_path, remote_file)
		#     sftp.remove(remote_filepath)  # delete after transfer
		# sftp.close()

		self.logger.debug(self.log_prefix + 'Clear or create task folder')
		# clear or create task folder
		self.shell.run(
			['sh', '-c', clear_or_create.format(self.working_dir)])

		# create task subdirectories
		self.logger.debug(self.log_prefix + 'Create task subdirs')
		if task_remote_subdirs:
			s_list = []
			for subdir in task_remote_subdirs:
				s_list.append('mkdir -p ' + subdir)

			command = ' && '.join(s_list)
			self.shell.run(['sh', '-c', command], cwd=self.remote_task_dir)


		# create task output folder in skylab media dir
		try:
			os.makedirs(os.path.join(settings.MEDIA_ROOT, self.task.task_dirname + '/output'))
		except OSError:
			# output dir already exists
			pass

	@abstractmethod
	def run_commands(self, **kwargs):
		pass

	@abstractmethod
	def handle_input_files(self, *args, **kwargs):
		pass

	# raise not implemented error

	@abstractmethod
	def run_tool(self, *args, **kwargs):
		pass

	# raise not

	@abstractmethod
	def handle_output_files(self, *args, **kwargs):
		pass
