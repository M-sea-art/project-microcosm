from .base import Adapter
class OpenclawAdapter(Adapter):
    name = 'openclaw'
    def available(self, project_root): return False
