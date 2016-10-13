from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_name = 'AutoDock Vina'
    package_name = __name__.replace('.install', '')
    p2ctool_name = 'vina'
    toolset_description = 'AutoDock Vina is an open-source program for doing molecular docking.'
    toolset_source_url = 'http://vina.scripps.edu/'

    toolset, created = ToolSet.objects.get_or_create(display_name=toolset_name, package_name=package_name,
                                                     p2ctool_name=p2ctool_name,
                                                     description=toolset_description, source_url=toolset_source_url)

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Vina',
         # 'executable_name': 'VinaExecutable',
         # 'view_name':'VinaView',

         },
        {'display_name': 'Vina split',
         # 'executable_name': 'VinaSplitExecutable',
         # 'view_name':'VinaSplitView',
         'description': 'You split the receptor into two parts: rigid and flexible, '
                        'with the latter represented somewhat similarly to how the ligand is represented.',
         },
    ]

    add_tools_to_toolset(tools, toolset)
