"""
Visualize UAV network topology using matplotlib and NetworkX.
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional

from topology import NODE_DOMAIN, DEFAULT_DOMAIN


def draw_topology(
    graph: nx.DiGraph,
    title: str = "UAV Network Topology",
    ax: Optional[plt.Axes] = None,
) -> None:
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    pos = _hierarchical_layout(graph)
    node_colors = []
    for n in graph.nodes():
        domain = graph.nodes[n].get(NODE_DOMAIN, DEFAULT_DOMAIN)
        node_colors.append("#2E86AB" if domain == DEFAULT_DOMAIN else "#E94F37")
    nx.draw_networkx_nodes(
        graph,
        pos,
        node_color=node_colors,
        node_size=1200,
        ax=ax,
    )
    nx.draw_networkx_labels(graph, pos, ax=ax, font_size=10)
    nx.draw_networkx_edges(
        graph,
        pos,
        ax=ax,
        edge_color="gray",
        arrows=True,
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
    )
    ax.set_title(title)
    ax.axis("off")


def _hierarchical_layout(graph: nx.DiGraph) -> dict:
    pos = {}
    if not graph.nodes:
        return pos
    roots = [n for n in graph.nodes() if graph.in_degree(n) == 0]
    if not roots:
        roots = list(graph.nodes())[:1]
    layers: list = [[]]
    seen = set()
    current = list(roots)
    while current:
        layers[-1].extend(current)
        seen.update(current)
        next_layer = []
        for n in current:
            for _, v in graph.out_edges(n):
                if v not in seen:
                    next_layer.append(v)
                    seen.add(v)
        current = next_layer
        if current:
            layers.append([])
    y_step = 1.0
    for i, layer in enumerate(layers):
        y = -i * y_step
        n_nodes = len(layer)
        for j, n in enumerate(layer):
            x = (j - (n_nodes - 1) / 2) * 1.2
            pos[n] = (x, y)
    return pos

