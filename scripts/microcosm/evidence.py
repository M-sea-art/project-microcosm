def evidence_id(adapter, path, line=None):
    safe = str(path).replace('\\','/').replace('/','-').replace(':','').strip('-') or 'root'
    return f"evidence.{adapter}.{safe}" + (f"-{line}" if line else "")
def make_evidence(adapter, path, level="E3", line_start=None, line_end=None, confidence=0.9, kind="source-location"):
    source={"path":str(path)}
    if line_start is not None: source["line_start"]=line_start
    if line_end is not None: source["line_end"]=line_end
    return {"id":evidence_id(adapter,path,line_start),"kind":kind,"level":level,"source":source,"collector":{"adapter":adapter,"version":"0.1.0"},"confidence":confidence}
