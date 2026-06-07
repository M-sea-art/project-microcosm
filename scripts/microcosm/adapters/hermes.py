from .base import Adapter
class HermesAdapter(Adapter):
    name = 'hermes'
    def available(self, project_root): return False
