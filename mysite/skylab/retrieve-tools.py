import os

dirs = [(lst,lst) for lst in os.listdir('modules') if not os.path.isfile(lst) and lst]
# tool_list = []
# for subdir in dirs:
# 	if subdir:	#if not empty string
# 		# print subdir
# 		tool_list.append(subdir)
#
# print tool_list
print dirs