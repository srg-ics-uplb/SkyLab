import shutil
import time

from skylab.modules.base_tool import P2CToolGeneric


class impi_executable(P2CToolGeneric):
	# 6, 11, 12 (segmentation fault) inherent error
	# 3, 4 secondary numeric input needed
	def __init__(self, **kwargs):
		mpi_cluster_name = kwargs.get('mpi_cluster_name',"impi-cluster")
		mpi_cluster_size = kwargs.get('mpi_cluster_size',"1")
		auto_destroy = kwargs.get('auto_destroy',True)
		super(impi_executable, self).__init__(tool_name="impi", mpi_cluster_name=mpi_cluster_name,
											  mpi_cluster_size=mpi_cluster_size, auto_destroy=auto_destroy)

	def handle_input_files(self, **kwargs):
        input_file = kwargs.get('param_input_file', "Lenna.jpg")
		with self.cluster_shell.open("/mirror/impi/" + input_file, "wb") as remote_file:
			with open(input_file,"rb") as local_file:
				shutil.copyfileobj(local_file, remote_file)
				local_file.close()
			remote_file.close()

	def run_tool(self, **kwargs):
        input_file = kwargs.get('param_input_file', "Lenna.jpg")
		output_file = kwargs.get('output_file', "custom_out.jpg")
		parameters = kwargs.get('parameters', [])
		self.create_mpi_cluster()
		self.activate_tool()
		self.handle_input_files(input_file=input_file)

		self.tool_shell = self.cluster_shell.spawn(["./"+self.tool_name, input_file], cwd="/mirror/impi")

		parameters.append("0")	#append exit option
		for i in range(len(parameters)):
			time.sleep(0.1)
			self.tool_shell.stdin_write("%s\n" % parameters[i])
			if parameters[i] == 3 or parameters[i] == 4:	#requires additional parameter
				i += 1
				time.sleep(0.1)
				self.tool_shell.stdin_write("%s\n" % parameters[i])

		print "Finished looping"

		print "Waiting for shell to terminate"
		self.tool_shell.wait_for_result()
		print "Sending output file"
		self.handle_output_files(output_file=output_file)

		if self.auto_destroy:
			self.destroy_mpi_cluster()

	def handle_output_files(self, **kwargs):
		output_file = kwargs.get('output_file', "custom_out.jpg")
		with self.cluster_shell.open("/mirror/impi/test_out.jpg", "rb") as remote_file:
			with open(output_file,"wb") as local_file: 			#TODO: edit to storage location
				shutil.copyfileobj(remote_file, local_file)
				local_file.close()
			remote_file.close()

class Dummy(object):
	def talk(self):
		print "Hello, Im a dummy"