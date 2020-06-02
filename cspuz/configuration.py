import os
from distutils.util import strtobool


def _get_default(infer_from_env, env_key, default):
    if infer_from_env:
        return os.environ.get(env_key, default)
    else:
        return default


class Config(object):
    def __init__(self, infer_from_env=True):
        self.default_backend = _get_default(infer_from_env, 'CSPUZ_DEFAULT_BACKEND', 'sugar')
        self.backend_path = _get_default(infer_from_env, 'CSPUZ_BACKEND_PATH', None)
        self.use_graph_primitive = strtobool(_get_default(infer_from_env, 'CSPUZ_USE_GRAPH_PRIMITIVE', 'False'))
        self.solver_timeout = None


config = Config()
