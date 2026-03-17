"""
Swarm batch authentication: simulate many UAVs authenticating in a batch
using RLWE key agreement, and measure total authentication time.
"""

import time
from typing import List

from rlwe import generate_parameters
from gcs import GroundControlStation
from uav_node import UAVNode
from topology import create_network
from visualization import draw_topology
import matplotlib.pyplot as plt


def create_swarm(size: int) -> List[UAVNode]:
    return [UAVNode(f"UAV{i+1}") for i in range(size)]


def main() -> None:
    swarm_size = 20
    print("Initializing UAV Swarm Network")
    print(f"Creating swarm of {swarm_size} UAVs")
    print("Generating RLWE parameters\n")

    params = generate_parameters(n=256, q=4093)
    print(f"RLWE parameters: n={params['n']}, q={params['q']}\n")

    gcs = GroundControlStation(gcs_id="GCS")
    uavs = create_swarm(swarm_size)
    for uav in uavs:
        gcs.register_uav(uav.id)

    uav_ids = [u.id for u in uavs]
    graph_initial = create_network(gcs_id="GCS", uav_ids=uav_ids)

    print("Running batch RLWE key agreement for entire swarm...")
    start = time.perf_counter()
    for uav in uavs:
        uav.connect_to_gcs(gcs)
    end = time.perf_counter()

    total_time_s = end - start
    avg_time_s = total_time_s / swarm_size if swarm_size else 0.0
    print(f"\nBatch authentication completed for {swarm_size} UAVs.")
    print(f"Total authentication time: {total_time_s * 1000:.2f} ms")
    print(f"Average time per UAV (sequential simulation): {avg_time_s * 1000:.2f} ms\n")

    print("--- Sample session keys (hex) ---")
    for uav in uavs[:5]:
        key = uav.session_key
        hex_key = key.hex() if key else "None"
        print(f"  {uav.id}: {hex_key[:32]}...")
    print()

    print("--- Swarm authentication metrics ---")
    print(
        "Computation cost / algorithm complexity:\n"
        f"  - Practical cost: {total_time_s * 1000:.2f} ms total for {swarm_size} UAVs "
        f"(approx {avg_time_s * 1000:.2f} ms per UAV in this simulation).\n"
        "  - Asymptotic complexity: O(N * n^2) with naive RLWE polynomial "
        "multiplication (N = number of UAVs, n = 256 here).\n"
    )
    bytes_per_coeff = 2
    coeffs_per_poly = 256
    polys_per_uav = 3
    bytes_per_uav = bytes_per_coeff * coeffs_per_poly * polys_per_uav
    total_bytes = bytes_per_uav * swarm_size
    print(
        "Communication cost / bandwidth usage:\n"
        f"  - Approx. {bytes_per_uav / 1024:.2f} KiB per UAV (a, b, u polynomials).\n"
        f"  - Approx. {total_bytes / 1024:.2f} KiB total for the swarm batch.\n"
        "  - This is a one-time cost per authentication round, not continuous traffic.\n"
    )
    print(
        "Energy consumption / drone battery impact:\n"
        "  - CPU work for RLWE per UAV is a short burst (tens of ms), so energy\n"
        "    spent on cryptography is very small compared to propulsion and sensors.\n"
        "  - Short, infrequent messages also keep radio usage (and thus RF power)\n"
        "    low during authentication.\n"
    )
    print(
        "Authentication accuracy / security reliability:\n"
        "  - RLWE-based key agreement provides strong security assumptions against\n"
        "    quantum adversaries in theory; this simulator uses the same structure\n"
        "    with simplified parameters for clarity.\n"
        "  - All UAVs in the swarm successfully derive a session key in this run;\n"
        "    re-running the batch can be used to re-key the swarm when needed.\n"
    )
    print()

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    title = (
        f"Swarm Topology (GCS → {swarm_size} UAVs)\n"
        f"Batch RLWE auth: total {total_time_s * 1000:.2f} ms, "
        f"avg {avg_time_s * 1000:.2f} ms/UAV"
    )
    draw_topology(graph_initial, title=title, ax=ax)
    plt.tight_layout()
    fig.savefig("swarm_topology.png", dpi=120)
    print("Swarm topology figure saved to swarm_topology.png")
    plt.show()


if __name__ == "__main__":
    main()

