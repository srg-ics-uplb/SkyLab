from skylab.models import ToolSet, Tool

def insert_to_db():
    toolset_name = "AutoDock4"
    package_name = __name__.replace(".install", '')
    toolset_description = "AutoDock is a suite of automated docking tools. It is designed to predict how small molecules, such as substrates or drug candidates, bind to a receptor of known 3D structure."
    toolset_source_url = "http://autodock.scripps.edu/"

    toolset, created = ToolSet.objects.get_or_create(display_name=toolset_name, package_name=package_name,
                                                     description=toolset_description, source_url=toolset_source_url)

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {"display_name": "AutoGrid",
         # "executable_name": "AutoGridExecutable",
         # "view_name":"AutoGridView",
         "description": "Pre-calculates grids to be used by AutoDock",
         "toolset": toolset
         },
        {"display_name": "AutoDock",
         # "executable_name": "AutoDockExecutable",
         #"view_name":"AutoDockView",
         "description": "Performs the docking of the ligand to a set of grids describing the target protein",
         "toolset": toolset
         },
    ]

    for t in tools:
        tool = Tool.objects.get_or_create(display_name=t.get("display_name"),
                                          executable_name=t.get("executable_name",
                                                                t["display_name"].replace(' ', '') + 'Executable'),
                                          description=t.get("description", None), toolset=t.get("toolset"),
                                          view_name=t.get("view_name", t["display_name"].replace(' ', '') + 'View'))
