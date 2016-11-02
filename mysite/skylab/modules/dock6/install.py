from skylab.bootskylab import add_tools_to_toolset
from skylab.models import ToolSet


def insert_to_db():
    toolset_dict = {
        'display_name': 'Dock 6',
        'package_name': __name__.replace('.install', ''),
        'p2ctool_name': 'dock6',
        'description': 'The new features of DOCK 6 include: additional scoring options during minimization; DOCK 3.5 scoring-including Delphi electrostatics, ligand conformational entropy corrections, ligand desolvation, receptor desolvation; Hawkins-Cramer-Truhlar GB/SA solvation scoring with optional salt screening; PB/SA solvation scoring; and AMBER scoring-including receptor flexibility, the full AMBER molecular mechanics scoring function with implicit solvent, conjugate gradient minimization, and molecular dynamics simulation capabilities. Because DOCK 6 is an extension of DOCK 5, it also includes all previous features. ',
        'source_url': 'http://dock.compbio.ucsf.edu/DOCK_6/index.htm'
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
        {'display_name': 'dock6',
         'description': 'Screen molecules for complementarily with receptor'
         },

        {'display_name': 'grid',
         'description': 'Precompute score grids for rapid dock evaluation'
         },
        # not yet supported
        # {'display_name': 'sphgen',
        #  'description': 'Site characterization negative image of the site',
        #  }
    ]

    add_tools_to_toolset(tools, toolset)
