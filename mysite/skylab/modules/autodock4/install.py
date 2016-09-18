from skylab.models import ToolSet, Tool


def insert_to_db():
    toolset_name = "AutoDock4"
    package_name = "autodock4"
    toolset_description = "AutoDock is a suite of automated docking tools. It is designed to predict how small molecules, such as substrates or drug candidates, bind to a receptor of known 3D structure."
    toolset_source_url = "http://autodock.scripps.edu/"

    toolset, created = ToolSet.objects.get_or_create(display_name=toolset_name, package_name=package_name,
                                                     description=toolset_description, source_url=toolset_source_url)

    tools = [
        {"display_name": "AutoGrid",
         "executable_name": "AutoGridExecutable",
         "description": "Pre-calculates grids to be used by AutoDock",
         "toolset": toolset
         },
        {"display_name": "AutoDock",
         "executable_name": "AutoDockExecutable",
         "description": "Performs the docking of the ligand to a set of grids describing the target protein",
         "toolset": toolset
         },
    ]

    for t in tools:
        tool = Tool.objects.get_or_create(display_name=t.get("display_name"),
                                          executable_name=t.get("executable_name", None),
                                          description=t.get("description", None), toolset=t.get("toolset"))
