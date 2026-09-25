"""Betweenness centrality over shortest computation paths (T-Control's BC_SCP, Eq. 1)
for a simrd trace, computed on the storage-level dependency graph.

Edge u -> v for every parent storage u of a tensor in storage v; edge weight = c(v),
so a path's length is the summed compute of the vertices after its source, matching
T-Control's length(p(s,t)) = sum c(v_i) + c(t).

Differences from T-Control, stated in PROTOCOL.md:
  * the graph is the WHOLE traced iteration (T-Control grows it layer by layer during
    the iteration), which gives the baseline more information, not less;
  * graphs above EXACT_MAX vertices use networkx's sampled estimator with k pivots and
    a fixed seed.
Results are cached in bc_cache/<model>.json.
"""
import json, math, os, sys
import networkx as nx

EXACT_MAX = 6000
K_PIVOTS = 1000
HERE = os.path.dirname(os.path.abspath(__file__))


def storage_graph(cb):
    from simrd.runtime import RuntimeV2EagerOptimized
    from simrd.heuristic import Heuristic
    rt = RuntimeV2EagerOptimized(math.inf, Heuristic(), stats=False, trace=False)
    cb(rt)
    G = nx.DiGraph()
    for t in rt.tensor_map.values():
        v = t.storage.root_id
        G.add_node(v)
        for p in t.parents:
            u = p.storage.root_id
            if u != v:
                G.add_edge(u, v, w=max(t.storage.compute, 1e-9))
    return G


def bc_for(model, cb):
    os.makedirs(os.path.join(HERE, 'bc_cache'), exist_ok=True)
    path = os.path.join(HERE, 'bc_cache', f'{model}.json')
    if os.path.exists(path):
        return {int(k): v for k, v in json.load(open(path))['bc'].items()}
    G = storage_graph(cb)
    n = G.number_of_nodes()
    if n <= EXACT_MAX:
        bc = nx.betweenness_centrality(G, weight='w', normalized=False)
        how = 'exact'
    else:
        bc = nx.betweenness_centrality(G, k=K_PIVOTS, seed=20260926, weight='w',
                                       normalized=False)
        how = f'sampled k={K_PIVOTS} seed=20260926'
    json.dump({'model': model, 'nodes': n, 'edges': G.number_of_edges(),
               'method': how, 'bc': {str(k): v for k, v in bc.items()}},
              open(path, 'w'))
    return bc


if __name__ == '__main__':
    sys.setrecursionlimit(1_000_000)
    import harness
    for m in sys.argv[1:]:
        cb, _ = harness.load(m)
        bc = bc_for(m, cb)
        meta = json.load(open(os.path.join(HERE, 'bc_cache', f'{m}.json')))
        print(m, meta['nodes'], meta['edges'], meta['method'], flush=True)
