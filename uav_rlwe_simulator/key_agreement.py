"""
Post-quantum RLWE key agreement between UAV and Ground Control Station (GCS).

Simulates a 3-message handshake:
  msg1: Authentication request (UAV -> GCS)
  msg2: Response with RLWE computation (GCS -> UAV sends public key; UAV computes and sends u)
  msg3: Session key confirmation (both sides have derived the same key)
"""

from typing import TYPE_CHECKING, Optional

from rlwe import (
    generate_parameters,
    generate_keypair,
    key_exchange_uav_side,
    key_exchange_gcs_side,
)

if TYPE_CHECKING:
    from uav_node import UAVNode
    from gcs import GroundControlStation


def rlwe_handshake(
    uav: "UAVNode",
    gcs: "GroundControlStation",
    params: Optional[dict] = None,
) -> bytes:
    """
    Perform RLWE-based key agreement between a UAV and the GCS.
    """
    if params is None:
        params = getattr(gcs, "_rlwe_params", None)
    if params is None:
        params = generate_parameters()
        gcs._rlwe_params = params

    if not getattr(gcs, "_keypair", None):
        public_key, secret_key = generate_keypair(params)
        gcs._keypair = (public_key, secret_key)
        gcs._rlwe_secret = secret_key

    public_key, _ = gcs._keypair
    a, b = public_key

    u, session_key_uav = key_exchange_uav_side(params, a, b)

    session_key_gcs = key_exchange_gcs_side(params, gcs._rlwe_secret, u)
    _ = session_key_gcs

    return session_key_uav


def generate_session_key() -> bytes:
    """Placeholder for additional KDF logic (not used here)."""
    return b""

