from .base import Adapter
class CodegraphAdapter(Adapter):
    name = 'codegraph'
    def available(self, project_root): return False
