import os, torch, gsplat, pkg_resources, setuptools
print("python",__import__("sys").executable)
print("pkg_resources",pkg_resources.__file__)
print("setuptools",setuptools.__version__,setuptools.__file__)
print("torch",torch.__version__,torch.version.cuda)
print("gsplat",gsplat.__version__)
from gsplat.cuda import _backend
print("backend_import_pass",_backend.__file__)
