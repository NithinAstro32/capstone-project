"""
Main entry point: simulate Post-Quantum RLWE Key Agreement for Dynamic
Topology Changes in UAV Networks.
"""

import copy

from rlwe import generate_parameters
from gcs import GroundControlStation
from uav_node import UAVNode
from topology import create_network, move_uav, detect_topology_change, SECONDARY_DOMAIN
from visualization import draw_topology
import matplotlib.pyplot as plt


def main() -> None:
    print("Initializing UAV Network")
    print("Generating RLWE parameters\n")

    params = generate_parameters(n=256, q=4093)
    print(f"RLWE parameters: n={params['n']}, q={params['q']}\n")

    gcs = GroundControlStation(gcs_id="GCS")
    uav1 = UAVNode("UAV1")
    uav2 = UAVNode("UAV2")
    uav3 = UAVNode("UAV3")
    uavs = [uav1, uav2, uav3]

    for uav in uavs:
        gcs.register_uav(uav.id)

    graph_initial = create_network(gcs_id="GCS", uav_ids=["UAV1", "UAV2", "UAV3"])

    for uav in uavs:
        print(f"{uav.id} connected to GCS")
        print("Running RLWE key agreement")
        success = uav.connect_to_gcs(gcs)
        if success:
            print("Session key established\n")
        else:
            print("Session key failed\n")

    print("--- Session keys (hex) ---")
    for uav in uavs:
        key = uav.session_key
        hex_key = key.hex() if key else "None"
        print(f"  {uav.id}: {hex_key[:32]}...")
    print()

    graph_after = copy.deepcopy(graph_initial)
    move_uav(
        graph_after,
        uav_id="UAV1",
        from_gcs="GCS",
        to_domain=SECONDARY_DOMAIN,
        new_parent_id="GCS2",
    )

    changed, _ = detect_topology_change(graph_initial, graph_after)
    if changed:
        print("Topology change detected")
        print("UAV1 moved to new domain\n")

    print("Re-running RLWE key agreement")
    uav1.connected_gcs = gcs
    uav1.authenticate()
    print("New session key generated\n")

    print("--- Session keys after topology change (hex) ---")
    for uav in uavs:
        key = uav.session_key
        hex_key = key.hex() if key else "None"
        print(f"  {uav.id}: {hex_key[:32]}...")
    print()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    draw_topology(graph_initial, title="Initial Topology (GCS → UAV1, UAV2, UAV3)", ax=ax1)
    draw_topology(
        graph_after,
        title="Topology After UAV1 Moved to New Domain (GCS2)",
        ax=ax2,
    )
    plt.tight_layout()
    fig.savefig("topology_before_after.png", dpi=120)
    print("Topology graphs saved to topology_before_after.png")
    plt.show()


if __name__ == "__main__":
    main()

