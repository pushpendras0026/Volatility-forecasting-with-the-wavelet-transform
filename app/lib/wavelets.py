"""Port of submission/R/wavelets.R (filters, DWT/MODWT pyramid, prefix MRA)."""
from __future__ import annotations

import numpy as np

# Same numeric coefficients as wavelets.R (checked there against PyWavelets' source).
SCALING = {
    "haar": np.array([1.0, 1.0]) / np.sqrt(2.0),
    "db4": np.array([.23037781330889650, .71484657055291565, .63088076792985891, -.027983769416859854,
                     -.18703481171909308, .030841381835560764, .032883011666885200, -.010597401785069032]),
    "db6": np.array([.11154074335010946, .49462389039845309, .75113390802109535, .31525035170919763,
                     -.22626469396543982, -.12976686756726194, .097501605587323049, .027522865530305729,
                     -.031582039317486030, .00055384220116149614, .0047772575109455106, -.0010773010853084796]),
}


def wavelet_filter(name: str):
    g = SCALING[name]
    L = len(g)
    h = g[::-1] * (-1.0) ** np.arange(L)
    return g, h


def circular_filter(x, weights, step=1, forward=False):
    n = len(x)
    idx = np.arange(n)
    out = np.zeros(n)
    d = 1 if forward else -1
    for k, w in enumerate(weights):
        out += w * x[(idx + d * step * k) % n]
    return out


def dwt_decompose(x, J, g, h):
    W, v = [], x
    for _ in range(J):
        keep = np.arange(1, len(v), 2)
        W.append(circular_filter(v, h)[keep])
        v = circular_filter(v, g)[keep]
    return W, v


def dwt_synthesis_step(w, v, g, h):
    n = 2 * len(v)
    uw, uv = np.zeros(n), np.zeros(n)
    uw[1::2] = w
    uv[1::2] = v
    return circular_filter(uw, h, forward=True) + circular_filter(uv, g, forward=True)


def modwt_decompose(x, J, g, h):
    W, v = [], x
    for j in range(1, J + 1):
        step = 2 ** (j - 1)
        W.append(circular_filter(v, h / np.sqrt(2), step))
        v = circular_filter(v, g / np.sqrt(2), step)
    return W, v


def modwt_synthesis_step(w, v, j, g, h):
    step = 2 ** (j - 1)
    return circular_filter(w, h / np.sqrt(2), step, forward=True) + circular_filter(v, g / np.sqrt(2), step, forward=True)


def decompose_prefix(x, method="modwt", filt="haar", J=2, reflect=True):
    """Additive MRA components {A_J, D_J..D_1} of x, with reflection of the available prefix."""
    x = np.asarray(x, float)
    g, h = wavelet_filter(filt)
    n = len(x)
    pad = (2 ** J - n % 2 ** J) % 2 ** J if method == "dwt" else 0
    padded = np.concatenate([x[:pad][::-1], x]) if pad else x
    ext = np.concatenate([padded, padded[::-1]]) if reflect else padded
    if method == "dwt" and len(ext) % 2 ** J:
        raise ValueError("length")
    W, V = dwt_decompose(ext, J, g, h) if method == "dwt" else modwt_decompose(ext, J, g, h)

    def rec(keep):
        v = V if keep == 0 else np.zeros_like(V)
        for j in range(J, 0, -1):
            w = W[j - 1] if j == keep else np.zeros_like(W[j - 1])
            v = dwt_synthesis_step(w, v, g, h) if method == "dwt" else modwt_synthesis_step(w, v, j, g, h)
        return v[pad: pad + n]

    out = {f"A{J}": rec(0)}
    for j in range(J, 0, -1):
        out[f"D{j}"] = rec(j)
    return out, (W, V)
