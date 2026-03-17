"""
Ground Control Station (GCS) that manages UAV nodes and RLWE key agreement.
"""

from typing import Dict, List, Optional, Any


class GroundControlStation:
    """GCS that registers UAVs, authenticates them, and stores session keys."""

    def __init__(self, gcs_id: str = "GCS"):
        self.id = gcs_id
        self.registered_uavs: List[str] = []
        self.active_sessions: Dict[str, bytes] = {}
        self._keypair: Optional[tuple] = None
        self._rlwe_secret: Optional[Any] = None
        self._rlwe_params: Optional[Dict[str, Any]] = None

    def register_uav(self, uav_id: str) -> None:
        if uav_id not in self.registered_uavs:
            self.registered_uavs.append(uav_id)

    def authenticate_uav(self, uav: Any) -> bool:
        if uav.id not in self.registered_uavs:
            self.register_uav(uav.id)
        return uav.authenticate()

    def store_session_key(self, uav_id: str, session_key: bytes) -> None:
        self.active_sessions[uav_id] = session_key

    def get_session_key(self, uav_id: str) -> Optional[bytes]:
        return self.active_sessions.get(uav_id)

