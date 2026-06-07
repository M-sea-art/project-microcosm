from collections import defaultdict
from microcosm.findings import FindingBuilder

def _match(edge, spec): return all(edge.get(k)==v for k,v in spec.items() if k in {'from','to','relation'})
def forbidden_edge(mir, inv, fb):
    out=[]
    for e in mir.get('edges',[]):
        if _match(e, inv.get('match',{})):
            out.append(fb.make('authority-violation','critical',0.96,e['id'],{'forbidden_edge':inv.get('match',{})},{'observed_edge':e},e.get('evidence_refs',[])))
    return out
def single_writer(mir, inv, fb):
    target=inv.get('target'); allowed=set(inv.get('allowed_writers',[])); writers=[e for e in mir.get('edges',[]) if e.get('to')==target and e.get('relation')=='writes']
    bad=[e for e in writers if e.get('from') not in allowed]
    if len(writers)>1 or bad:
        refs=[]
        for e in writers: refs.extend(e.get('evidence_refs',[]))
        return [fb.make('multiple-writers','high',0.94,target,{'allowed_writers':sorted(allowed)},{'observed_writers':[e.get('from') for e in writers]},refs)]
    return []
def no_cycle(mir, inv, fb):
    rels=set(inv.get('relation',[])); graph=defaultdict(list); refs={}; findings=[]; seen=set()
    for e in mir.get('edges',[]):
        if e.get('relation') in rels: graph[e['from']].append(e['to']); refs[(e['from'],e['to'])]=e.get('evidence_refs',[])
    def dfs(n,path):
        if n in path:
            cyc=path[path.index(n):]+[n]; ev=[]
            for a,b in zip(cyc,cyc[1:]): ev.extend(refs.get((a,b),[]))
            findings.append(fb.make('cyclic-dependency','high',0.93,n,{'acyclic_relations':sorted(rels)},{'cycle':cyc},ev)); return
        if n in seen: return
        seen.add(n)
        for nxt in graph.get(n,[]): dfs(nxt,path+[n])
    for n in list(graph): dfs(n,[])
    return findings
def max_fanout(mir, inv, fb):
    hits=[e for e in mir.get('edges',[]) if e.get('from')==inv.get('node') and e.get('relation')==inv.get('relation')]
    limit=int(inv.get('value',0))
    if len(hits)>limit:
        refs=[]
        for e in hits: refs.extend(e.get('evidence_refs',[]))
        return [fb.make('excessive-fanout','medium',0.90,inv.get('node'),{'max':limit},{'actual':len(hits),'targets':[e['to'] for e in hits]},refs)]
    return []
def required_path(mir, inv, fb):
    src=inv.get('from'); dst=inv.get('to'); must=inv.get('must_include',[]); graph=defaultdict(list); paths=[]
    for e in mir.get('edges',[]): graph[e['from']].append(e['to'])
    def walk(n,path):
        if len(path)>20: return
        if n==dst: paths.append(path); return
        for nxt in graph.get(n,[]):
            if nxt not in path: walk(nxt,path+[nxt])
    walk(src,[src])
    if not any(all(m in p for m in must) for p in paths):
        return [fb.make('missing-required-path','high',0.88,f'{src}->{dst}',{'must_include':must},{'paths':paths[:5]},[])]
    return []
def permission_subset(mir, inv, fb):
    subject=inv.get('subject'); allowed=set(inv.get('allowed',[])); denied=set(inv.get('denied',[])); bad=[]
    for e in mir.get('edges',[]):
        if e.get('from')==subject:
            rel=e.get('relation'); cap=rel if rel!='writes' else 'writes-long-term-memory'
            if rel not in allowed or cap in denied: bad.append(e)
    if bad:
        refs=[]
        for e in bad: refs.extend(e.get('evidence_refs',[]))
        return [fb.make('authority-violation','critical',0.92,subject,{'allowed':sorted(allowed),'denied':sorted(denied)},{'observed':[{'relation':e['relation'],'to':e['to']} for e in bad]},refs)]
    return []
