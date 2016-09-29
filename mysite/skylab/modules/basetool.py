import os.path
import pkgutil
from abc import abstractmethod

import pika
from django import forms

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
		Tool.objects.get_or_create(display_name=t.get("display_name"),
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

	# raise not

	@abstractmethod
	def handle_output_files(self, *args, **kwargs):
		pass

	@abstractmethod
	def change_status(self, status):
		pass
