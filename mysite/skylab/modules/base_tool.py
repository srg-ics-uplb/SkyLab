from abc import abstractmethod

class P2CToolGeneric(object):
	# frontend_ip = "10.0.3.101"
	# frontend_username = "user"
	# frontend_password = "excellence"

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def handle_input_files(self, **kwargs):
        pass
		# raise not implemented error

    @abstractmethod
    def run_tool(self, **kwargs):
        pass
		#raise not

    @abstractmethod
    def handle_output_files(self, **kwargs):
        pass

	def changeStatus(self, status):
		self.status = status