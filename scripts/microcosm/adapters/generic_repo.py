from pathlib import Path
from microcosm.evidence import make_evidence
from microcosm.normalize import node_id
from .base import Adapter, iter_project_paths
HEURISTICS={'SKILL.md':('skill','HEURISTIC-SKILL-001',0.82,'Skill manifest detected'),'AGENTS.md':('agent','HEURISTIC-AGENT-CONFIG-001',0.72,'Agent configuration source detected'),'mcp.json':('mcp-server','HEURISTIC-MCP-001',0.70,'MCP configuration detected')}
DIR_HEURISTICS={'memory':('memory','HEURISTIC-MEMORY-001',0.58),'memories':('memory','HEURISTIC-MEMORY-001',0.58),'long_term_memory':('memory','HEURISTIC-MEMORY-001',0.58),'tools':('tool','HEURISTIC-TOOLS-001',0.55),'workflows':('workflow','HEURISTIC-WORKFLOW-001',0.55),'queue':('queue','HEURISTIC-QUEUE-001',0.52),'policies':('policy','HEURISTIC-POLICY-001',0.52)}
class GenericRepoAdapter(Adapter):
    name='generic-repo'
    def scan(self, project_root):
        root=Path(project_root).resolve(); evidence=[]; nodes=[]; observations=[]; inferred=[]; proposed=[]
        ev=make_evidence(self.name, root, level='E3', confidence=1.0, kind='project-root'); evidence.append(ev)
        nodes.append({'id':'project.root','kind':'project','name':root.name,'attributes':{'root':str(root)},'evidence_refs':[ev['id']]})
        observations.append({'id':'observation.project-root','layer':'static','subject_ref':'project.root','status':'observed','evidence_refs':[ev['id']]})
        for p in iter_project_paths(root):
            rel=p.relative_to(root).as_posix()
            if p.is_file() and p.name in HEURISTICS:
                kind,rule,conf,reason=HEURISTICS[p.name]
                eid=make_evidence(self.name, rel, level='E2', confidence=conf, kind='manifest'); evidence.append(eid)
                nid=node_id(kind, p.parent.name if p.name=='SKILL.md' else p.stem)
                inferred.append({'id':nid,'kind':kind,'name':p.parent.name if p.name=='SKILL.md' else p.name,'rule_id':rule,'confidence':conf,'reason':reason,'evidence_refs':[eid['id']]})
                proposed.append({'id':f'proposal.{nid}','subject_ref':nid,'status':'proposed','reason':reason,'confidence':conf})
            if p.is_dir() and p.name in DIR_HEURISTICS:
                kind,rule,conf=DIR_HEURISTICS[p.name]
                eid=make_evidence(self.name, rel, level='E1', confidence=conf, kind='directory-heuristic'); evidence.append(eid)
                nid=node_id(kind, p.name)
                inferred.append({'id':nid,'kind':kind,'name':p.name,'rule_id':rule,'confidence':conf,'reason':'directory name suggests system role','evidence_refs':[eid['id']]})
        return {'nodes':nodes,'edges':[],'observations':observations,'evidence':evidence,'inferred':inferred,'proposed':proposed}
