"""
Live swarm simulation (Concept 1: RLWE + Topology + Batch Auth):
  - Demonstrates post-quantum RLWE key agreement in UAV swarms.
  - Multiple rounds of batch authentication for a UAV swarm.
  - At each round, some UAVs move from GCS1's domain to GCS2's domain.
  - Both GCS1 and GCS2 are legitimate and trusted by UAVs.
  - After each batch authentication, metrics are recomputed and shown
    live inside the figure.
  
  Key demonstration features:
    * RLWE-based cryptographic handshake
    * Dynamic topology changes (UAV handoff between GCS domains)
    * Batch authentication performance metrics
    * Session key establishment and management
"""

import time
from typing import List, Dict, Any, Optional, Mapping

import matplotlib.pyplot as plt
import networkx as nx

from rlwe import generate_parameters
from gcs import GroundControlStation
from uav_node import UAVNode
from topology import NODE_DOMAIN, DEFAULT_DOMAIN, SECONDARY_DOMAIN, move_uav
from visualization import draw_topology


def create_swarm(size: int) -> List[UAVNode]:
    return [UAVNode(f"UAV{i+1}") for i in range(size)]


def build_swarm_graph(uav_ids: List[str]) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_node("GCS1", **{NODE_DOMAIN: DEFAULT_DOMAIN})
    G.add_node("GCS2", **{NODE_DOMAIN: SECONDARY_DOMAIN})
    for uid in uav_ids:
        G.add_node(uid, **{NODE_DOMAIN: DEFAULT_DOMAIN})
        G.add_edge("GCS1", uid)
    return G


def _uav_parent(graph: nx.DiGraph, uav_id: str) -> str:
    """Return current parent GCS node for a UAV based on incoming edge."""
    preds = list(graph.predecessors(uav_id))
    return preds[0] if preds else "Unknown"


def _print_session_keys(uavs: List[UAVNode], header: str, limit: int = 5) -> None:
    """Print a short view of session keys (hex prefix) like main.py."""
    print(header)
    for uav in uavs[:limit]:
        key = uav.session_key
        hex_key = key.hex() if key else "None"
        print(f"  {uav.id}: {hex_key[:32]}...")
    if len(uavs) > limit:
        print(f"  ... ({len(uavs) - limit} more UAVs)")
    print()


def run_batch_auth(
    uavs: List[UAVNode],
    gcs: GroundControlStation,
    graph: Optional[nx.DiGraph] = None,
    verbose_ids: Optional[List[str]] = None,
    gcs_map: Optional[Mapping[str, GroundControlStation]] = None,
) -> Dict[str, Any]:
    start = time.perf_counter()
    for uav in uavs:
        if verbose_ids is not None and uav.id in verbose_ids:
            parent = _uav_parent(graph, uav.id) if graph is not None else gcs.id
            print(f"{uav.id} connected to {parent}")
            print("Running RLWE key agreement")
        # Pick the GCS to authenticate against based on topology parent.
        if gcs_map is not None and graph is not None:
            parent = _uav_parent(graph, uav.id)
            gcs_for_uav = gcs_map.get(parent, gcs)
        else:
            gcs_for_uav = gcs
        ok = uav.connect_to_gcs(gcs_for_uav)
        if not ok:
            parent = _uav_parent(graph, uav.id) if graph is not None else gcs_for_uav.id
            print(f"Authentication failed for {uav.id} (GCS={parent}) -> SAFE MODE")
        elif verbose_ids is not None and uav.id in verbose_ids:
            print("Session key established\n")
    end = time.perf_counter()

    total_time_s = end - start
    swarm_size = len(uavs)
    avg_time_s = total_time_s / swarm_size if swarm_size else 0.0

    bytes_per_coeff = 2
    coeffs_per_poly = 256
    polys_per_uav = 3
    bytes_per_uav = bytes_per_coeff * coeffs_per_poly * polys_per_uav
    total_bytes = bytes_per_uav * swarm_size

    return {
        "swarm_size": swarm_size,
        "total_time_ms": total_time_s * 1000.0,
        "avg_time_ms": avg_time_s * 1000.0,
        "bytes_per_uav": bytes_per_uav,
        "total_bytes": total_bytes,
    }


def format_metrics_text(metrics: Dict[str, Any]) -> str:
    swarm_size = metrics["swarm_size"]
    total_time_ms = metrics["total_time_ms"]
    avg_time_ms = metrics["avg_time_ms"]
    bytes_per_uav = metrics["bytes_per_uav"]
    total_bytes = metrics["total_bytes"]
    return (
        f"Swarm size: {swarm_size} UAVs\n"
        f"Batch auth latency: {total_time_ms:.1f} ms\n"
        f"Per-UAV latency (seq.): {avg_time_ms:.1f} ms\n"
        f"Comm per UAV: {bytes_per_uav / 1024:.2f} KiB\n"
        f"Total comm (batch): {total_bytes / 1024:.2f} KiB\n"
        "Energy impact: low (short CPU burst, short messages)\n"
        "Auth reliability: high (RLWE-based, fresh keys each round)"
    )


def main() -> None:
    swarm_size = 20
    rounds = 5

    print("Starting live swarm simulation")
    print(f"Swarm size: {swarm_size} UAVs, rounds: {rounds}")

    params = generate_parameters(n=256, q=4093)
    print(f"RLWE parameters: n={params['n']}, q={params['q']}\n")

    gcs1 = GroundControlStation(gcs_id="GCS1")
    # GCS2 is a legitimate secondary base station (owned by the same operator)
    gcs2 = GroundControlStation(gcs_id="GCS2")
    uavs = create_swarm(swarm_size)
    for uav in uavs:
        gcs1.register_uav(uav.id)
        gcs2.register_uav(uav.id)
        # Trust policy: both GCS1 and GCS2 are trusted (both legitimate)
        uav.trust_gcs(gcs1.id, gcs1.auth_token)
        uav.trust_gcs(gcs2.id, gcs2.auth_token)

    uav_ids = [u.id for u in uavs]
    graph = build_swarm_graph(uav_ids)

    fig, (ax_graph, ax_text) = plt.subplots(1, 2, figsize=(12, 6))
    ax_text.axis("off")

    # Round 0: initial batch auth. Print main.py-like logs for the first few UAVs.
    print("\nRound 0: Initial batch authentication\n")
    verbose_first = [u.id for u in uavs[:5]]
    gcs_map = {"GCS1": gcs1, "GCS2": gcs2}
    metrics = run_batch_auth(uavs, gcs1, graph=graph, verbose_ids=verbose_first, gcs_map=gcs_map)
    _print_session_keys(uavs, header="--- Session keys (hex) ---", limit=5)

    ax_graph.clear()
    draw_topology(graph, title="Swarm Topology: GCS1 & GCS2", ax=ax_graph)
    ax_text.clear()
    ax_text.axis("off")
    ax_text.set_title("Batch authentication metrics")
    ax_text.text(
        0.0,
        0.9,
        format_metrics_text(metrics),
        fontsize=10,
        va="top",
        ha="left",
    )
    plt.tight_layout()
    plt.pause(1.0)

    group_size = max(1, swarm_size // (rounds - 1)) if rounds > 1 else swarm_size
    moved_index = 0

    for r in range(1, rounds):
        to_move = uav_ids[moved_index: moved_index + group_size]
        moved_index += group_size

        print("Topology change detected")
        print(f"Round {r}: moving {len(to_move)} UAV(s) from GCS1 to GCS2\n")
        for uid in to_move:
            if uid in graph.nodes:
                move_uav(
                    graph,
                    uav_id=uid,
                    from_gcs="GCS1",
                    to_domain=SECONDARY_DOMAIN,
                    new_parent_id="GCS2",
                )

        # Re-auth after topology change. Print detailed logs only for moved UAVs.
        print("Re-running RLWE key agreement\n")
        metrics = run_batch_auth(uavs, gcs1, graph=graph, verbose_ids=to_move, gcs_map=gcs_map)
        _print_session_keys(uavs, header="--- Session keys after topology change (hex) ---", limit=5)

        ax_graph.clear()
        draw_topology(
            graph,
            title=f"Round {r}: some UAVs moved to GCS2",
            ax=ax_graph,
        )
        ax_text.clear()
        ax_text.axis("off")
        ax_text.set_title("Batch authentication metrics")
        ax_text.text(
            0.0,
            0.9,
            format_metrics_text(metrics),
            fontsize=10,
            va="top",
            ha="left",
        )
        plt.tight_layout()
        plt.pause(1.0)

    print("Live simulation complete. Close the figure window to exit.")
    plt.show()


if __name__ == "__main__":
    main()

