import ast
from pathlib import Path
from microcosm.evidence import make_evidence
from microcosm.normalize import edge_id
from .base import Adapter, iter_project_files
class PythonAstAdapter(Adapter):
    name='python-ast'
    def available(self, project_root): return next(iter_project_files(project_root, {'.py'}), None) is not None
    def scan(self, project_root):
        root=Path(project_root).resolve(); nodes=[]; edges=[]; observations=[]; evidence=[]
        for file in iter_project_files(root, {'.py'}):
            rel=file.relative_to(root).as_posix(); mod='module.'+rel[:-3].replace('/','.')
            ev=make_evidence(self.name, rel, level='E3', confidence=0.95, kind='python-module'); evidence.append(ev)
            nodes.append({'id':mod,'kind':'module','name':rel,'attributes':{'language':'python'},'evidence_refs':[ev['id']]})
            observations.append({'id':f'observation.{mod}','layer':'static','subject_ref':mod,'status':'observed','evidence_refs':[ev['id']]})
            try: tree=ast.parse(file.read_text(encoding='utf-8'))
            except Exception: continue
            for node in ast.walk(tree):
                names=[]
                if isinstance(node, ast.Import): names=[a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module: names=[node.module]
                for name in names:
                    dst='module.'+name; evid=make_evidence(self.name, rel, level='E3', line_start=getattr(node,'lineno',None), confidence=0.96, kind='import'); evidence.append(evid)
                    eid=edge_id(mod,'imports',dst)
                    edges.append({'id':eid,'from':mod,'to':dst,'relation':'imports','attributes':{},'evidence_refs':[evid['id']]})
                    observations.append({'id':f'observation.{eid}','layer':'static','subject_ref':eid,'status':'observed','evidence_refs':[evid['id']]})
        return {'nodes':nodes,'edges':edges,'observations':observations,'evidence':evidence,'inferred':[],'proposed':[]}
