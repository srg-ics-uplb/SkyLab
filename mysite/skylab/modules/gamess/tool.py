from skylab.modules.base_tool import P2CToolGeneric


class gamess_tool(P2CToolGeneric):
    def __init__(self, **kwargs):
        self.shell = kwargs.get('shell')
        self.id = kwargs.get('id')
        pass

    def handle_input_files(self, **kwargs):
        self.shell.run["mkdir", "act%d" % self.id,]
        pass
    # raise not implemented error

    def run_tool(self, **kwargs):
        if kwargs.get('command') is None:
            raise KeyError("No command passed")



    #   get_input_files()
    #   run command
    #   send_output_files back to server
    # raise not

    def handle_output_files(self, **kwargs):
        pass

    def changeStatus(self, status, **kwargs):
        pass