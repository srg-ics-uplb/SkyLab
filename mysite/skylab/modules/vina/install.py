from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'AutoDock Vina',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'vina',
        'description': 'AutoDock Vina is an open-source program for doing molecular docking. It was designed and implemented by Dr. Oleg Trott in the Molecular Graphics Lab at The Scripps Research Institute. ',
        'source_url': 'http://vina.scripps.edu/'
    }

    toolset, created = ToolSet.objects.update_or_create(package_name=toolset_dict['package_name'],
                                                        p2ctool_name=toolset_dict['p2ctool_name'],
                                                        defaults={'display_name': toolset_dict['display_name'],
                                                                  'description': toolset_dict.get('description',
                                                                                                  'No description provided'),
                                                                  'source_url': toolset_dict.get('source_url',
                                                                                                 'No link provided')
                                                                  }
                                                        )

    # if you followed the naming convention for classes, you do not need to provide values for executable_name and view_name
    tools = [
        {'display_name': 'Vina',
         'description': 'The main executable for AutoDock Vina'
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
