from .base import Adapter
class AgentSkillsAdapter(Adapter):
    name = 'agent-skills'
    def available(self, project_root): return False
