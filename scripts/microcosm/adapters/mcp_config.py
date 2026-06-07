from .base import Adapter
class McpConfigAdapter(Adapter):
    name = 'mcp-config'
    def available(self, project_root): return False
