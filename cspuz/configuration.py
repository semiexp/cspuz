from distutils.util import strtobool
import os
from typing import Optional


def _get_default(infer_from_env, env_key, default):
    if infer_from_env:
        return os.environ.get(env_key, default)
    else:
        return default


class Config(object):
    default_backend: str
    backend_path: Optional[str]
    use_graph_primitive: bool
    solver_timeout: Optional[float]

    def __init__(self, infer_from_env=True):
        self.default_backend = _get_default(infer_from_env,
                                            'CSPUZ_DEFAULT_BACKEND', 'sugar')
        self.backend_path = _get_default(infer_from_env, 'CSPUZ_BACKEND_PATH',
                                         None)
        self.use_graph_primitive = strtobool(
            _get_default(infer_from_env, 'CSPUZ_USE_GRAPH_PRIMITIVE', 'False'))
        self.solver_timeout = None


config = Config()
