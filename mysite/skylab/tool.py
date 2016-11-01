import re
import sys

import spur


class _MPICluster(object):
	frontend_ip = "10.0.3.101"
	frontend_username = "user"
	frontend_password = "excellence"

	def __init__(self, **kwargs):
		self.cluster_name = kwargs.get('cluster_name', 'skylab-default')
		self.cluster_username = kwargs.get('cluster_username', 'mpiuser')
		self.cluster_password = kwargs.get('cluster_password', 'mpiuser')
		self.cluster_size = kwargs.get('cluster_size', '1')
		self.connect_to_frontend()

	def connect_to_frontend(self):
		self.frontend_shell = spur.SshShell(hostname=_MPICluster.frontend_ip,
											username=_MPICluster.frontend_username,
											password=_MPICluster.frontend_password,
											missing_host_key=spur.ssh.MissingHostKey.accept)

		return self.frontend_shell

	def create_cluster(self):
		try:
			print "Creating MPI Cluster"
			self.connect_to_frontend()
			# self.changeStatus("Creating MPI Cluster")
			result_cluster_ip = self.frontend_shell.run(
				["./vcluster-start", self.cluster_name, self.cluster_size],
				cwd="vcluster")
			p = re.compile("(?P<username>\S+)@(?P<floating_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
			m = p.search(result_cluster_ip.output)
			self.cluster_username = m.group('username')
			self.cluster_password = self.cluster_username
			self.cluster_ip = m.group('floating_ip')
			# print "%s@%s" % (self.cluster_username, self.cluster_ip)

		except:  # spur.ssh.ConnectionError
			print sys.exc_info()
			# self.changeStatus("Error: Failed to connect to frontend.")
			return None

	def connect_to_cluster(self, **kwargs):
		self.cluster_ip = kwargs.get('cluster_ip', self.cluster_ip)
		if self.cluster_ip is not None:
			try:
				self.cluster_shell = spur.SshShell(hostname=self.cluster_ip, username=self.cluster_username,
												   password=self.cluster_password,
												   missing_host_key=spur.ssh.MissingHostKey.accept)
				print "Connecting to MPI Cluster"
				self.update_p2c()
				return self.cluster_shell
			except:  # spur.ssh.ConnectionError
				print sys.exc_info()
				# self.changeStatus("Error: Failed to connect to MPI cluster.")
				return None

	def destroy_cluster(self):
		self.connect_to_frontend()
		print "Destroying MPI Cluster"
		# self.changeStatus("Destroying MPI Cluster")
		self.frontend_shell.run(["./vcluster-stop", self.cluster_name, self.cluster_size], cwd="vcluster")

	def activate_tool(self, tool_name):
		self.connect_to_cluster()
		print "Activating p2c-tools %s" % tool_name
		# self.changeStatus("Activating p2c-tools %s" % self.tool_name)
		self.cluster_shell.run(["p2c-tools", "activate", tool_name])

	def update_p2c(self):
		print "Updating p2c-tools"
		self.cluster_shell.run(["wget", "10.0.3.10/downloads/p2c/p2c-tools"])
		self.cluster_shell.run(["chmod", "755", "p2c-tools"])
		p2c_updater = self.cluster_shell.spawn(["./p2c-tools"], use_pty=True)
		p2c_updater.stdin_write(self.cluster_password + "\n")
		print p2c_updater.wait_for_result().output
		print self.cluster_shell.run(["p2c-tools"]).output


class P2CToolGeneric(object):
	def __init__(self, **kwargs):
		self.tool_name = kwargs.get('tool_name', "untitled_tool")
		mpi_cluster_name = kwargs.get('mpi_cluster_name',"testcluster")
		mpi_cluster_size = kwargs.get('mpi_cluster_size',"1")
		self.auto_destroy = kwargs.get('auto_destroy', True)
		self.mpi_cluster = _MPICluster(cluster_name=mpi_cluster_name, cluster_size=mpi_cluster_size)
		# self.changeStatus("Status: Initializing")
		# self.create_mpi_cluster(mpi_cluster_name, mpi_cluster_size)
		# self.activate_tool()

	def create_mpi_cluster(self):
		self.mpi_cluster.create_cluster()

	def destroy_mpi_cluster(self):
		self.mpi_cluster.destroy_cluster()

	def connect_to_cluster(self):
		self.cluster_shell = self.mpi_cluster.connect_to_cluster()



	def handle_input_files(self, **kwargs):
		raise NotImplementedError
		# raise not implemented error

	def run_tool(self, **kwargs):
		raise NotImplementedError
		#raise not implemented error

	def handle_output_files(self, **kwargs):
		raise NotImplementedError

	def changeStatus(self, status):
		self.status = status

# class Impi(P2CToolGeneric):
# 	# 6, 11, 12 (segmentation fault) inherent error
# 	# 3, 4 secondary numeric input needed
# 	def __init__(self, **kwargs):
# 		mpi_cluster_name = kwargs.get('mpi_cluster_name',"impi-cluster")
# 		mpi_cluster_size = kwargs.get('mpi_cluster_size',"1")
# 		auto_destroy = kwargs.get('auto_destroy',True)
# 		super(Impi, self).__init__(tool_name="impi", mpi_cluster_name=mpi_cluster_name, mpi_cluster_size=mpi_cluster_size, auto_destroy=auto_destroy)
#
# 	def handle_input_files(self, **kwargs):
#         input_file = kwargs.get('param_input_files', "Lenna.jpg")
# 		with self.cluster_shell.open("/mirror/impi/" + input_file, "wb") as remote_file:
# 			with open(input_file,"rb") as local_file:
# 				shutil.copyfileobj(local_file, remote_file)
# 				local_file.close()
# 			remote_file.close()
#
# 	def run_tool(self, **kwargs):
# 		input_file = kwargs.get('param_input_files', "Lenna.jpg")
# 		output_file = kwargs.get('output_file', "custom_out.jpg")
# 		parameters = kwargs.get('parameters', [])
# 		self.create_mpi_cluster()
# 		self.activate_toolset()
# 		self.handle_input_files(input_file=input_file)
#
# 		self.tool_shell = self.cluster_shell.spawn(["./"+self.tool_name, input_file], cwd="/mirror/impi")
#
# 		parameters.append("0")	#append exit option
# 		for i in range(len(parameters)):
# 			time.sleep(0.1)
# 			self.tool_shell.stdin_write("%s\n" % parameters[i])
# 			if parameters[i] == 3 or parameters[i] == 4:	#requires additional parameter
# 				i += 1
# 				time.sleep(0.1)
# 				self.tool_shell.stdin_write("%s\n" % parameters[i])
#
# 		print "Finished looping"
#
# 		print "Waiting for shell to terminate"
# 		self.tool_shell.wait_for_result()
# 		print "Sending output file"
# 		self.handle_output_files(output_file=output_file)
#
# 		if self.auto_destroy:
# 			self.mpi_cluster.destroy_cluster()
#
# 	def handle_output_files(self, **kwargs):
# 		output_file = kwargs.get('output_file', "custom_out.jpg")
# 		with self.cluster_shell.open("/mirror/impi/test_out.jpg", "rb") as remote_file:
# 			with open(output_file,"wb") as local_file: 			#TODO: edit to storage location
# 				shutil.copyfileobj(remote_file, local_file)
# 				local_file.close()
# 			remote_file.close()
#
# newtool = Impi(auto_destroy=True)
# newtool.run_tool(input_file="test.jpg",parameters=["1","2","4","5","7"])

# cluster = _MPICluster()
# cluster.create_cluster()
