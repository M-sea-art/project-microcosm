from microcosm.findings import FindingBuilder
from . import operators
DISPATCH={'forbidden-edge':operators.forbidden_edge,'single-writer':operators.single_writer,'no-cycle':operators.no_cycle,'max-fanout':operators.max_fanout,'required-path':operators.required_path,'permission-subset':operators.permission_subset}
def run_invariants(mir, invariants):
    fb=FindingBuilder(); findings=[]
    for inv in invariants:
        fn=DISPATCH.get(inv.get('operator'))
        if not fn:
            findings.append(fb.make('adapter-failure','low',0.6,inv.get('operator') or 'unknown',{'supported':sorted(DISPATCH)},{'operator':inv.get('operator')},[])); continue
        findings.extend(fn(mir, inv, fb))
    return findings
