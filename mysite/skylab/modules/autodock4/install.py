from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_name = 'AutoDock 4'
    package_name = __name__.replace('.install', '')
    p2ctool_name = 'autodock'

    toolset_description = 'AutoDock is a suite of automated docking tools. It is designed to predict how small molecules, ' \
                          'such as substrates or drug candidates, bind to a receptor of known 3D structure.'
    toolset_source_url = 'http://autodock.scripps.edu/'

    toolset, created = ToolSet.objects.update_or_create(package_name=package_name,
                                                        p2ctool_name=p2ctool_name,
                                                        defaults={'display_name': toolset_name,
                                                                  'description': toolset_description,
                                                                  'source_url': toolset_source_url})

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'AutoGrid 4',
         # 'executable_name': 'AutoGrid4Executable',
         # 'view_name':'AutoGridView',
         'description': 'Pre-calculates grids to be used by AutoDock',
         },
        {'display_name': 'AutoDock 4',
         # 'executable_name': 'AutoDock4Executable',
         # 'view_name':'AutoDockView',
         'description': 'Performs the docking of the ligand to a set of grids describing the target protein',
         },
    ]

    add_tools_to_toolset(tools, toolset)
