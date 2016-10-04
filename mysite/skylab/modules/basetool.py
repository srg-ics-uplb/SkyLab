import os.path
import pkgutil
from abc import abstractmethod

import pika
from django import forms
from django.conf import settings

import skylab.modules
from skylab.models import SkyLabFile, Tool, ToolActivation


def install_toolsets():
	package = skylab.modules
	prefix = package.__name__ + "."
	for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
		if ispkg:  # for packages
			submod_prefix = modname + "."
			pkg = importer.find_module(modname).load_module(modname)
			for submodimporter, submodname, submodispkg in pkgutil.iter_modules(pkg.__path__, submod_prefix):
				if submodname.endswith(".install"):
					mod = submodimporter.find_module(submodname).load_module(submodname)
					mod.insert_to_db()


def add_tools_to_toolset(tools, toolset):
	for t in tools:
		Tool.objects.update_or_create(display_name=t.get("display_name"),
									  executable_name=t.get("executable_name",
														 t["display_name"].replace(' ', '') + 'Executable'),
									  description=t.get("description", None), toolset=toolset,
									  view_name=t.get("view_name", t["display_name"].title().replace(' ', '') + 'View'))


class MPIModelChoiceField(forms.ModelChoiceField):
	def __init__(self, *args, **kwargs):
		self.toolset = kwargs.pop("toolset", None)
		super(MPIModelChoiceField, self).__init__(*args, **kwargs)

	def label_from_instance(self, obj):
		if self.toolset is not None:
			status = ""
			try:
				tool_activation = ToolActivation.objects.get(mpi_cluster=obj, toolset=self.toolset)
				if tool_activation.activated:
					status = "Installed"
				else:
					status = "Queued for installation"
			except ToolActivation.DoesNotExist:
				status = "Not installed"
			return "{0} (nodes : {1}) ({2} status: {3})".format(obj.cluster_name, obj.cluster_size,
																self.toolset.display_name, status)

		return "{0} (nodes : {1}))".format(obj.cluster_name, obj.cluster_size)


# TODO: refactor
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


	def __init__(self, *args, **kwargs):
		self.shell = kwargs.get('shell')
		self.task = kwargs.get('task')
		self.logger = kwargs.get('logger')
		self.log_prefix = kwargs.get('log_prefix', '')
		self.working_dir = os.path.join(settings.REMOTE_BASE_DIR, self.task.task_dirname)

	def clear_or_create_dirs(self, **kwargs):
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
		if task_remote_subdirs:
			s_list = []
			for subdir in task_remote_subdirs:
				s_list.append('mkdir ' + subdir)

			command = ' && '.join(s_list)
			self.shell.run(['sh', '-c', command], cwd=self.working_dir)

		# create task output folder in skylab media dir
		try:
			os.makedirs(os.path.join(settings.MEDIA_ROOT, self.task.task_dirname + '/output'))
		except OSError:
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
