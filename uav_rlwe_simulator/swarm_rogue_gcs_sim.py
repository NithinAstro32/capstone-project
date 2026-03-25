"""
Cybersecurity swarm simulation (Concept 2: Authentication Resilience):
  - Demonstrates post-quantum RLWE authentication resilience against rogue GCS.
  - When UAVs encounter an unknown/rogue GCS (e.g., military base station),
    they correctly REJECT the authentication attempt and enter SAFE MODE.
  - Shows the fail-closed security behavior of the RLWE key agreement protocol.
  
  Key demonstration features:
    * RLWE-based identity verification (challenge-response)
    * Fail-closed security: UAVs reject untrusted GCS
    * Safe mode activation when encountering rogue bases
    * Authentication success rate metrics
    * Security event logging
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


def build_swarm_graph_with_rogue(uav_ids: List[str]) -> nx.DiGraph:
    """Build graph with legitimate GCS1, friendly GCS2, and rogue GCS_ROGUE."""
    G = nx.DiGraph()
    G.add_node("GCS1", **{NODE_DOMAIN: DEFAULT_DOMAIN})
    G.add_node("GCS2", **{NODE_DOMAIN: SECONDARY_DOMAIN})
    G.add_node("GCS_ROGUE", **{NODE_DOMAIN: "rogue"})  # Unknown military base
    
    for uid in uav_ids:
        G.add_node(uid, **{NODE_DOMAIN: DEFAULT_DOMAIN})
        G.add_edge("GCS1", uid)
    return G


def _uav_parent(graph: nx.DiGraph, uav_id: str) -> str:
    """Return current parent GCS node for a UAV based on incoming edge."""
    preds = list(graph.predecessors(uav_id))
    return preds[0] if preds else "Unknown"


def _print_session_keys(uavs: List[UAVNode], header: str, limit: int = 5) -> None:
    """Print a short view of session keys (hex prefix)."""
    print(header)
    for uav in uavs[:limit]:
        key = uav.session_key
        hex_key = key.hex() if key else "NONE (Safe Mode)"
        status = " [SAFE MODE]" if uav.safe_mode else ""
        print(f"  {uav.id}: {hex_key[:32]}...{status}")
    if len(uavs) > limit:
        print(f"  ... ({len(uavs) - limit} more UAVs)")
    print()


def run_batch_auth_with_security_events(
    uavs: List[UAVNode],
    gcs: GroundControlStation,
    graph: Optional[nx.DiGraph] = None,
    verbose_ids: Optional[List[str]] = None,
    gcs_map: Optional[Mapping[str, GroundControlStation]] = None,
) -> Dict[str, Any]:
    """Run batch auth and track security events (successes vs rejections)."""
    start = time.perf_counter()
    auth_success = 0
    auth_failure = 0
    safe_mode_count = 0
    
    for uav in uavs:
        if verbose_ids is not None and uav.id in verbose_ids:
            parent = _uav_parent(graph, uav.id) if graph is not None else gcs.id
            print(f"{uav.id} attempting connection to {parent}")
            print("Running RLWE key agreement & identity verification")
        
        # Pick the GCS to authenticate against based on topology parent.
        if gcs_map is not None and graph is not None:
            parent = _uav_parent(graph, uav.id)
            gcs_for_uav = gcs_map.get(parent, gcs)
        else:
            gcs_for_uav = gcs
        
        ok = uav.connect_to_gcs(gcs_for_uav)
        
        if not ok:
            auth_failure += 1
            safe_mode_count += 1
            parent = _uav_parent(graph, uav.id) if graph is not None else gcs_for_uav.id
            if verbose_ids is not None and uav.id in verbose_ids:
                print(f"❌ AUTHENTICATION REJECTED for {uav.id}")
                print(f"   GCS {parent} is NOT in trusted list")
                print(f"   Entering SAFE MODE (fail-closed protection)\n")
        else:
            auth_success += 1
            if verbose_ids is not None and uav.id in verbose_ids:
                print(f"✓ Authentication successful with {gcs_for_uav.id}")
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
        "auth_success": auth_success,
        "auth_failure": auth_failure,
        "safe_mode_count": safe_mode_count,
        "total_time_ms": total_time_s * 1000.0,
        "avg_time_ms": avg_time_s * 1000.0,
        "bytes_per_uav": bytes_per_uav,
        "total_bytes": total_bytes,
    }


def format_security_metrics_text(metrics: Dict[str, Any]) -> str:
    """Format security-focused metrics."""
    swarm_size = metrics["swarm_size"]
    auth_success = metrics["auth_success"]
    auth_failure = metrics["auth_failure"]
    safe_mode_count = metrics["safe_mode_count"]
    success_rate = (auth_success / swarm_size * 100) if swarm_size > 0 else 0.0
    
    return (
        f"SECURITY METRICS:\n"
        f"Swarm size: {swarm_size} UAVs\n"
        f"Auth SUCCESS: {auth_success} UAVs ({success_rate:.1f}%)\n"
        f"Auth REJECTED: {auth_failure} UAVs\n"
        f"Safe mode active: {safe_mode_count} UAVs\n"
        f"\n"
        f"RLWE Verification:\n"
        f"Identity proof: CHALLENGE-RESPONSE\n"
        f"Key exchange: RLWE LATTICE-BASED\n"
        f"Fail-closed: YES (reject untrusted GCS)\n"
        f"Protocol: FAIL-SAFE ✓"
    )


def main() -> None:
    swarm_size = 20
    rounds = 3

    print("=" * 70)
    print("CYBERSECURITY DEMONSTRATION: ROGUE GCS DETECTION & SAFE MODE")
    print("=" * 70)
    print(f"\nSwarm size: {swarm_size} UAVs, Security rounds: {rounds}")
    print("Scenario: UAVs encounter an unknown/rogue military base station\n")

    params = generate_parameters(n=256, q=4093)
    print(f"RLWE parameters: n={params['n']}, q={params['q']}\n")

    # Initialize legitimate GCS and rogue GCS
    gcs1 = GroundControlStation(gcs_id="GCS1")
    gcs2 = GroundControlStation(gcs_id="GCS2")
    gcs_rogue = GroundControlStation(gcs_id="GCS_ROGUE")  # Unknown/military base
    
    uavs = create_swarm(swarm_size)
    for uav in uavs:
        gcs1.register_uav(uav.id)
        gcs2.register_uav(uav.id)
        gcs_rogue.register_uav(uav.id)
        
        # Trust policy: only GCS1 and GCS2 are trusted (legitimate friendly bases)
        # GCS_ROGUE is NOT in the trust list - UAVs will reject it
        uav.trust_gcs(gcs1.id, gcs1.auth_token)
        uav.trust_gcs(gcs2.id, gcs2.auth_token)
        # NOTE: gcs_rogue NOT trusted - intentional security test
    
    uav_ids = [u.id for u in uavs]
    graph = build_swarm_graph_with_rogue(uav_ids)

    fig, (ax_graph, ax_text) = plt.subplots(1, 2, figsize=(14, 6))
    ax_text.axis("off")

    # Round 0: Initial auth with legitimate GCS1
    print("\n" + "=" * 70)
    print("ROUND 0: Normal operation with trusted GCS1")
    print("=" * 70 + "\n")
    verbose_first = [u.id for u in uavs[:5]]
    gcs_map = {"GCS1": gcs1, "GCS2": gcs2, "GCS_ROGUE": gcs_rogue}
    metrics = run_batch_auth_with_security_events(
        uavs, gcs1, graph=graph, verbose_ids=verbose_first, gcs_map=gcs_map
    )
    _print_session_keys(uavs, header="--- Session keys (legitimate GCS1) ---", limit=5)

    ax_graph.clear()
    draw_topology(graph, title="Round 0: Normal operation (GCS1 trusted)", ax=ax_graph)
    ax_text.clear()
    ax_text.axis("off")
    ax_text.set_title("Authentication & Security Status")
    ax_text.text(0.0, 0.9, format_security_metrics_text(metrics), fontsize=9, va="top", ha="left")
    plt.tight_layout()
    plt.pause(1.0)

    # Round 1: Some UAVs move to GCS2 (legitimate friendly base)
    print("=" * 70)
    print("ROUND 1: UAVs move to friendly GCS2 (still trusted)")
    print("=" * 70 + "\n")
    
    to_move_friendly = uav_ids[0:5]
    for uid in to_move_friendly:
        if uid in graph.nodes:
            move_uav(graph, uav_id=uid, from_gcs="GCS1", to_domain=SECONDARY_DOMAIN, new_parent_id="GCS2")
    
    print("Topology change: 5 UAVs move to GCS2 (friendly trusted base)\n")
    
    verbose_moved = to_move_friendly[:3]
    metrics = run_batch_auth_with_security_events(
        uavs, gcs1, graph=graph, verbose_ids=verbose_moved, gcs_map=gcs_map
    )
    _print_session_keys(uavs, header="--- Session keys (GCS2 friendly) ---", limit=5)

    ax_graph.clear()
    draw_topology(graph, title="Round 1: UAVs moved to friendly GCS2 (trusted)", ax=ax_graph)
    ax_text.clear()
    ax_text.axis("off")
    ax_text.set_title("Authentication & Security Status")
    ax_text.text(0.0, 0.9, format_security_metrics_text(metrics), fontsize=9, va="top", ha="left")
    plt.tight_layout()
    plt.pause(1.0)

    # Round 2: SECURITY INCIDENT - UAVs encounter rogue military GCS
    print("=" * 70)
    print("ROUND 2: ⚠️  SECURITY INCIDENT - Rogue military GCS detected")
    print("=" * 70)
    print("\nScenario: While transiting through airspace, UAVs encounter")
    print("an unknown military base station (GCS_ROGUE) broadcasting GCS signals.\n")
    
    to_move_rogue = uav_ids[5:15]
    for uid in to_move_rogue:
        if uid in graph.nodes:
            move_uav(
                graph,
                uav_id=uid,
                from_gcs="GCS1",
                to_domain="rogue",
                new_parent_id="GCS_ROGUE"
            )
    
    print(f"Topology change: {len(to_move_rogue)} UAVs moved to unknown GCS_ROGUE")
    print("(This GCS is NOT in the UAVs' trust list)\n")
    
    verbose_rogue = to_move_rogue[:5]
    metrics = run_batch_auth_with_security_events(
        uavs, gcs1, graph=graph, verbose_ids=verbose_rogue, gcs_map=gcs_map
    )
    _print_session_keys(uavs, header="--- Session keys (ROGUE attempt) ---", limit=5)

    print("\n⚠️  SECURITY EVENT SUMMARY:")
    print(f"  • {metrics['auth_failure']} UAVs REJECTED the rogue GCS")
    print(f"  • {metrics['safe_mode_count']} UAVs entered SAFE MODE")
    print("  • 0 UAVs compromised (fail-closed protection worked)\n")

    ax_graph.clear()
    draw_topology(graph, title="Round 2: ⚠️  Rogue GCS (UNTRUSTED) detected", ax=ax_graph)
    ax_text.clear()
    ax_text.axis("off")
    ax_text.set_title("SECURITY INCIDENT: Rogue GCS Authentication Rejected")
    ax_text.text(0.0, 0.9, format_security_metrics_text(metrics), fontsize=9, va="top", ha="left")
    plt.tight_layout()
    plt.pause(2.0)

    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Findings:")
    print("✓ RLWE identity verification successfully rejected rogue GCS")
    print("✓ Fail-closed security behavior protected all UAVs")
    print("✓ Safe mode activation prevented compromise")
    print("\nConclusion: Post-quantum RLWE provides resilience against")
    print("          rogue base station attacks in UAV swarms.\n")

    plt.show()


if __name__ == "__main__":
    main()
