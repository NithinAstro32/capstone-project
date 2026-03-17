"""
Simplified Ring Learning With Errors (RLWE) cryptographic model for educational simulation.

RLWE is a post-quantum lattice-based primitive. Security relies on the hardness of
distinguishing (a, a*s + e) from random, where a is random, s and e are small secrets.
"""

import numpy as np
from typing import Tuple, Dict, Any


def generate_parameters(n: int = 256, q: int = 4093) -> Dict[str, Any]:
    """
    Initialize RLWE parameters.

    Args:
        n: Polynomial ring dimension (degree of x^n + 1). Higher n = more security.
        q: Modulus for coefficients. Should be prime, large enough for security.

    Returns:
        Dictionary with 'n', 'q', and optional metadata.
    """
    return {"n": n, "q": q}


def _poly_add(a: np.ndarray, b: np.ndarray, q: int) -> np.ndarray:
    """Add two polynomials in Z_q (coefficient-wise addition mod q)."""
    return np.mod(a + b, q)


def _poly_mul_ring(a: np.ndarray, b: np.ndarray, q: int) -> np.ndarray:
    """
    Multiply polynomials in the ring Z_q[x]/(x^n + 1).
    Uses negacyclic convolution: product mod (x^n + 1).
    """
    n = len(a)
    c = np.zeros(n, dtype=np.int64)
    for i in range(n):
        for j in range(n):
            idx = i + j
            if idx < n:
                c[idx] += a[i] * b[j]
            else:
                # x^n = -1 in the ring
                c[idx - n] -= a[i] * b[j]
    return np.mod(c, q)


def _sample_uniform(n: int, q: int, rng: np.random.Generator) -> np.ndarray:
    """Sample polynomial with coefficients uniform in [0, q-1]."""
    return rng.integers(0, q, size=n)


def _sample_small(n: int, bound: int, rng: np.random.Generator) -> np.ndarray:
    """Sample polynomial with small coefficients in [-bound, bound] (for secret and error)."""
    return rng.integers(-bound, bound + 1, size=n)


def generate_keypair(
    params: Dict[str, Any],
    rng: np.random.Generator = None,
) -> Tuple[Tuple[np.ndarray, np.ndarray], np.ndarray]:
    """
    Generate RLWE keypair using equation: b = a*s + e (all in ring Z_q[x]/(x^n+1)).

    Args:
        params: From generate_parameters(), must have 'n' and 'q'.
        rng: Random number generator for reproducibility.

    Returns:
        (public_key, secret_key) where public_key = (a, b), secret_key = s.
    """
    if rng is None:
        rng = np.random.default_rng()
    n, q = params["n"], params["q"]
    bound = min(2, q // 8)

    a = _sample_uniform(n, q, rng)
    s = _sample_small(n, bound, rng)
    e = _sample_small(n, bound, rng)

    b = _poly_add(_poly_mul_ring(a, s, q), e, q)
    public_key = (a, b)
    secret_key = s
    return public_key, secret_key


def reconcile_shared(raw_shared: np.ndarray, q: int) -> np.ndarray:
    """
    Reconcile raw shared polynomial to a common bit string (rounding).
    Simple method: round coefficient to 0 or 1 based on q/2 threshold.
    """
    half = q // 2
    bits = (raw_shared > half).astype(np.uint8)
    return bits


def key_exchange_uav_side(
    params: Dict[str, Any],
    a: np.ndarray,
    b: np.ndarray,
    rng: np.random.Generator = None,
) -> Tuple[np.ndarray, bytes]:
    """
    UAV side of RLWE key exchange: compute u = a*r + e1 and shared value v = b*r + e2,
    reconcile v to get session key, return u (to send) and key.
    """
    if rng is None:
        rng = np.random.default_rng()
    n, q = params["n"], params["q"]
    bound = min(2, q // 8)

    r = _sample_small(n, bound, rng)
    e1 = _sample_small(n, bound, rng)
    e2 = _sample_small(n, bound, rng)

    u = _poly_add(_poly_mul_ring(a, r, q), e1, q)
    v = _poly_add(_poly_mul_ring(b, r, q), e2, q)

    bits = reconcile_shared(v, q)
    key = bits.tobytes()
    return u, key


def key_exchange_gcs_side(
    params: Dict[str, Any],
    s: np.ndarray,
    u: np.ndarray,
) -> bytes:
    """
    GCS side of RLWE key exchange: compute w = u*s, reconcile to get session key.
    """
    n, q = params["n"], params["q"]
    _ = n
    w = _poly_mul_ring(u, s, q)
    bits = reconcile_shared(w, q)
    return bits.tobytes()

