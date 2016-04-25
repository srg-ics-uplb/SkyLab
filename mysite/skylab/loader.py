# from modules._base_tool import *
# from modules.impi import *
# http://stackoverflow.com/questions/951124/dynamic-loading-of-python-modules

def loadModules():
    res = {}
    import os
    # check subfolders
    lst = os.listdir("modules")
    dir = []
    for d in lst:
        s = os.path.abspath("modules") + os.sep + d
        if os.path.isdir(s) and os.path.exists(s + os.sep + "__init__.py"):
            dir.append(d)
    # load the modules
    for d in dir:
        res[d] = __import__("modules." + d, fromlist = ["*"])
    return res

def getClassByName(module, className):
    if not module:
        if className.startswith("modules."):
            className = className.split("modules.")[1]
        l = className.split(".")
        m = __services__[l[0]]
        return getClassByName(m, ".".join(l[1:]))
    elif "." in className:
        l = className.split(".")
        m = getattr(module, l[0])
        return getClassByName(m, ".".join(l[1:]))
    else:
        return getattr(module, className)

mods = loadModules()
print mods
cls = getClassByName(mods["impi"], "Dummy")
obj = cls()
obj.talk()
# print mods
# def cluster_shit(cluster_name, cluster_size):
#     cls = getClassByName(mods["_base_tool"], "_MPICluster")
#     newtool = cls(cluster_name=cluster_name, cluster_size=cluster_size)
#     newtool.create_cluster()





