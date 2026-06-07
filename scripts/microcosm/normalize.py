def node_id(kind, name):
    return f"{kind}.{str(name).replace(' ', '-').replace('_', '-').lower()}"
def edge_id(src, relation, dst):
    return "edge." + "-".join([src, relation, dst]).replace('.', '-').replace('/', '-')
