"""
UAV (Unmanned Aerial Vehicle) node for the simulated network.
"""

from typing import Optional, Any


class UAVNode:
    """Represents a UAV node that can connect to a GCS and establish an RLWE session key."""

    def __init__(self, node_id: str):
        self.id = node_id
        self.session_key: Optional[bytes] = None
        self.connected_gcs: Optional[Any] = None
        self._domain: Optional[str] = None

    def connect_to_gcs(self, gcs: Any) -> bool:
        self.connected_gcs = gcs
        return self.authenticate()

    def authenticate(self) -> bool:
        if self.connected_gcs is None:
            return False
        from key_agreement import rlwe_handshake

        self.session_key = rlwe_handshake(self, self.connected_gcs)
        self.connected_gcs.store_session_key(self.id, self.session_key)
        return True

    def update_session_key(self, new_key: bytes) -> None:
        self.session_key = new_key
        if self.connected_gcs is not None:
            self.connected_gcs.store_session_key(self.id, new_key)

    def set_domain(self, domain: str) -> None:
        self._domain = domain

    def get_domain(self) -> Optional[str]:
        return self._domain

