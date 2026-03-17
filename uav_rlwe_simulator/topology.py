"""
UAV network topology using NetworkX.
"""

import networkx as nx
from typing import Tuple, Optional, List

NODE_DOMAIN = "domain"
DEFAULT_DOMAIN = "primary"
SECONDARY_DOMAIN = "secondary"


def create_network(
    gcs_id: str = "GCS",
    uav_ids: Optional[List[str]] = None,
) -> nx.DiGraph:
    if uav_ids is None:
        uav_ids = ["UAV1", "UAV2", "UAV3"]
    G = nx.DiGraph()
    G.add_node(gcs_id, **{NODE_DOMAIN: DEFAULT_DOMAIN})
    for uav_id in uav_ids:
        G.add_node(uav_id, **{NODE_DOMAIN: DEFAULT_DOMAIN})
        G.add_edge(gcs_id, uav_id)
    return G


def move_uav(
    graph: nx.DiGraph,
    uav_id: str,
    from_gcs: str,
    to_domain: str = SECONDARY_DOMAIN,
    new_parent_id: Optional[str] = None,
) -> nx.DiGraph:
    if graph.has_edge(from_gcs, uav_id):
        graph.remove_edge(from_gcs, uav_id)
    if uav_id in graph.nodes:
        graph.nodes[uav_id][NODE_DOMAIN] = to_domain
    if new_parent_id is not None:
        if not graph.has_node(new_parent_id):
            graph.add_node(new_parent_id, **{NODE_DOMAIN: to_domain})
        graph.add_edge(new_parent_id, uav_id)
    return graph


def detect_topology_change(
    graph_before: nx.DiGraph,
    graph_after: nx.DiGraph,
) -> Tuple[bool, List[str]]:
    changed = False
    affected: List[str] = []
    edges_before = set(graph_before.edges())
    edges_after = set(graph_after.edges())
    if edges_before != edges_after:
        changed = True
        for u, v in edges_before ^ edges_after:
            if v not in affected:
                affected.append(v)
            if u not in affected:
                affected.append(u)
    nodes_before = set(graph_before.nodes())
    nodes_after = set(graph_after.nodes())
    for n in nodes_before | nodes_after:
        if n not in nodes_before or n not in nodes_after:
            changed = True
            if n not in affected:
                affected.append(n)
        elif n in nodes_before and n in nodes_after:
            d_before = graph_before.nodes[n].get(NODE_DOMAIN)
            d_after = graph_after.nodes[n].get(NODE_DOMAIN)
            if d_before != d_after:
                changed = True
                if n not in affected:
                    affected.append(n)
    return changed, affected

