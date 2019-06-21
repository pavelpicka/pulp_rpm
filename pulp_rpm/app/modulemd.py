import json
from pulp_rpm.app.constants import PULP_MODULE_ATTR

import gi
gi.require_version('Modulemd', '2.0')
from gi.repository import Modulemd as mmdlib


def _get_modules(file, module_index):
    """Get modulemd names."""
    module_str = file.open().read().decode()
    ret, fails = module_index.update_from_string(module_str, True)
    if ret:
        return module_index.get_module_names()
    else:
        return list()


def _get_nsvca(modules, module_index):
    """Get modulemd NSVCA, artifacts and dependencies."""
    ret = list()
    for module in modules:
        m = module_index.get_module(module)
        for s in m.get_all_streams():
            tmp = {}
            keys = [
                PULP_MODULE_ATTR.NAME,
                PULP_MODULE_ATTR.STREAM,
                PULP_MODULE_ATTR.VERSION,
                PULP_MODULE_ATTR.CONTEXT,
                PULP_MODULE_ATTR.ARCH,
                ]
            nsvca = s.get_NSVCA().split(':')
            for k in keys:
                tmp[k] = nsvca.pop(0)

            tmp[PULP_MODULE_ATTR.ARTIFACTS] = json.dumps(s.get_rpm_artifacts())

            deps_list = s.get_dependencies()
            deps = {}
            for dep in deps_list:
                d_list = dep.get_runtime_modules()
                for dependecy in d_list:
                    deps[dependecy] = dep.get_runtime_streams(dependecy)
            tmp[PULP_MODULE_ATTR.DEPENDENCIES] = json.dumps(deps)
            ret.append(tmp)
    return ret
