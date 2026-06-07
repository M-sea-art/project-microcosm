from .base import Adapter
class CodexAdapter(Adapter):
    name = 'codex'
    def available(self, project_root): return False
