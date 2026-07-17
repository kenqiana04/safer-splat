import importlib.util, sys
print("python",sys.executable)
for n in ("pkg_resources","setuptools","gsplat","torch","nerfstudio"):
 print(n,importlib.util.find_spec(n))
try:
 import pkg_resources
 print("pkg_resources_pass",pkg_resources.__file__)
except Exception as e: print("pkg_resources_fail",repr(e))
