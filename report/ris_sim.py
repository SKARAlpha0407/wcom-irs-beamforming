"""
Reproduction of the single-user results of
  Q. Wu and R. Zhang, "Intelligent Reflecting Surface Enhanced Wireless Network
  via Joint Active and Passive Beamforming," IEEE Trans. Wireless Commun., 2019.

System: M-antenna AP -> single-antenna user, helped by an N-element IRS.
Goal:   minimise AP transmit power subject to a receive-SNR target gamma.

Run:    python ris_sim.py            (full run, a few minutes on 8 cores)
        python ris_sim.py --quick    (small run for a smoke test)
Output: ../figures/*.png|pdf and ../figures/results.json
"""
import argparse
import json
import multiprocessing as mp
import os
import time

import cvxpy as cp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------------------------------------------------------
# Simulation parameters (see Table I of the report)
# ----------------------------------------------------------------------------
M = 4                 # AP antennas
D0 = 51.0             # AP-IRS distance [m]
DV = 2.0              # vertical offset of the user line [m]
C0_DB = -30.0         # path loss at the 1 m reference distance [dB]
ALPHA_AI = 2.0        # path-loss exponent AP-IRS   (LoS link)
ALPHA_IU = 2.8        # path-loss exponent IRS-user
ALPHA_AU = 3.5        # path-loss exponent AP-user  (obstructed direct link)
NOISE_DBM = -80.0     # receiver noise power [dBm]
GAMMA_DB = 10.0       # SNR target [dB]
N_RAND = 1000        # Gaussian randomisations for the SDR scheme (as in the paper)
AO_EPS = 1e-4         # stopping threshold of alternating optimisation
AO_MAX_IT = 50

SIGMA2 = 10 ** ((NOISE_DBM - 30) / 10)   # W
GAMMA = 10 ** (GAMMA_DB / 10)


def to_dbm(p_watt):
    return 10 * np.log10(p_watt) + 30


def pathloss(d, alpha):
    return 10 ** (C0_DB / 10) * d ** (-alpha)


def crandn(rng, *shape):
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2)


def gen_channels(rng, N, d, k_ai=np.inf):
    """One channel realisation for a user at horizontal distance d from the AP.

    G   (N x M): AP -> IRS, Rician with factor k_ai (default: pure LoS, rank one)
    hr  (N,)   : IRS -> user (this is h_r^H written as a row), Rayleigh
    hd  (M,)   : AP  -> user (this is h_d^H written as a row), Rayleigh
    """
    d_au = np.hypot(d, DV)
    d_iu = np.hypot(D0 - d, DV)
    # LoS AP-IRS link: outer product of half-wavelength array responses
    a_irs = np.exp(1j * np.pi * np.arange(N) * np.sin(rng.uniform(0, 2 * np.pi)))
    a_ap = np.exp(1j * np.pi * np.arange(M) * np.sin(rng.uniform(0, 2 * np.pi)))
    G = np.outer(a_irs, a_ap.conj())
    if np.isfinite(k_ai):
        G = np.sqrt(k_ai / (k_ai + 1)) * G + np.sqrt(1 / (k_ai + 1)) * crandn(rng, N, M)
    G = np.sqrt(pathloss(D0, ALPHA_AI)) * G
    hr = np.sqrt(pathloss(d_iu, ALPHA_IU)) * crandn(rng, N)
    hd = np.sqrt(pathloss(d_au, ALPHA_AU)) * crandn(rng, M)
    return G, hr, hd


def power_given_v(Phi, hd, v):
    """Min transmit power when the IRS uses reflection vector v (MRT at the AP).
    Effective channel row: h = v^H Phi + hd, optimum w = h^H/||h||."""
    h = v.conj() @ Phi + hd
    return GAMMA * SIGMA2 / np.linalg.norm(h) ** 2


def align_phases(Phi, hd, w):
    """Closed-form IRS phases for a fixed transmit beamformer w:
    make every reflected path add coherently with the direct path."""
    return np.exp(1j * (np.angle(Phi @ w) - np.angle(hd @ w)))


def quantise(v, bits):
    levels = 2 ** bits
    step = 2 * np.pi / levels
    return np.exp(1j * np.round(np.angle(v) / step) * step)


def alternating_opt(Phi, hd, return_trace=False):
    """Algorithm 1 of the paper: alternate between MRT and phase alignment."""
    w = hd.conj() / np.linalg.norm(hd)          # initialise with AP-user MRT
    v = align_phases(Phi, hd, w)
    trace = [GAMMA * SIGMA2 / abs((v.conj() @ Phi + hd) @ w) ** 2]   # iteration 0
    prev = np.inf
    for _ in range(AO_MAX_IT):
        v = align_phases(Phi, hd, w)
        h = v.conj() @ Phi + hd
        w = h.conj() / np.linalg.norm(h)
        p = GAMMA * SIGMA2 / np.linalg.norm(h) ** 2
        trace.append(p)
        if (prev - p) / p < AO_EPS:
            break
        prev = p
    return (p, v, trace) if return_trace else (p, v)


def solve_sdp(R):
    """max tr(R V)  s.t.  V >= 0 (PSD), V_nn = 1  (the relaxed problem)."""
    n = R.shape[0]
    scale = np.real(np.trace(R)) / n
    V = cp.Variable((n, n), hermitian=True)
    prob = cp.Problem(cp.Maximize(cp.real(cp.trace((R / scale) @ V))),
                      [V >> 0, cp.diag(V) == 1])
    prob.solve(solver=cp.SCS, eps=1e-5)
    return V.value, prob.value * scale


def sdr(Phi, hd, rng):
    """Semidefinite relaxation. Returns (lower bound on power, power after
    Gaussian randomisation)."""
    N = Phi.shape[0]
    R = np.zeros((N + 1, N + 1), dtype=complex)
    R[:N, :N] = Phi @ Phi.conj().T
    R[:N, N] = Phi @ hd.conj()
    R[N, :N] = R[:N, N].conj()
    R = (R + R.conj().T) / 2
    V, val = solve_sdp(R)
    gain_ub = val + np.linalg.norm(hd) ** 2
    p_lb = GAMMA * SIGMA2 / gain_ub
    # Gaussian randomisation: v_bar = U Sigma^(1/2) r, r ~ CN(0, I)
    V = (V + V.conj().T) / 2
    lam, U = np.linalg.eigh(V)
    L = U * np.sqrt(np.clip(lam, 0, None))
    r = crandn(rng, N + 1, N_RAND)
    vb = L @ r
    cand = np.exp(1j * np.angle(vb[:N] / vb[N]))            # N x N_RAND
    h = cand.conj().T @ Phi + hd                            # N_RAND x M
    p_rand = GAMMA * SIGMA2 / np.max(np.sum(np.abs(h) ** 2, axis=1))
    return p_lb, p_rand


def one_realisation(rng, N, d, with_sdr=True, bits=()):
    G, hr, hd = gen_channels(rng, N, d)
    Phi = hr[:, None] * G                    # diag(h_r^H) G
    out = {}
    out["Without IRS"] = GAMMA * SIGMA2 / np.linalg.norm(hd) ** 2
    out["Alternating optimization"], v_ao = alternating_opt(Phi, hd)
    # AP-user MRT: beam at the user, IRS aligns to it
    w = hd.conj() / np.linalg.norm(hd)
    v = align_phases(Phi, hd, w)
    out["AP-user MRT"] = GAMMA * SIGMA2 / abs((v.conj() @ Phi + hd) @ w) ** 2
    # AP-IRS MRT: beam at the IRS (G is rank one -> its row space direction)
    w = G[0].conj() / np.linalg.norm(G[0])
    v = align_phases(Phi, hd, w)
    out["AP-IRS MRT"] = GAMMA * SIGMA2 / abs((v.conj() @ Phi + hd) @ w) ** 2
    # Random IRS phases, MRT on the resulting channel
    v = np.exp(1j * rng.uniform(0, 2 * np.pi, N))
    out["Random phase shift"] = power_given_v(Phi, hd, v)
    if with_sdr:
        out["Lower bound (SDR)"], out["SDR + randomization"] = sdr(Phi, hd, rng)
    for b in bits:
        out[f"{b}-bit phase shifters"] = power_given_v(Phi, hd, quantise(v_ao, b))
    return out


def average(rng, N, d, n_real, **kw):
    if isinstance(rng, int):                 # called from a worker process
        rng = np.random.default_rng(rng)
    acc = {}
    for _ in range(n_real):
        for k, p in one_realisation(rng, N, d, **kw).items():
            acc.setdefault(k, []).append(p)
    return {k: float(to_dbm(np.mean(v))) for k, v in acc.items()}


def convergence(seed, N, d, k_ai, n_real, n_it):
    """Average power after each AO iteration and the average SDR lower bound."""
    rng = np.random.default_rng(seed)
    tr, lb = np.zeros(n_it + 1), 0.0
    for _ in range(n_real):
        G, hr, hd = gen_channels(rng, N, d, k_ai)
        Phi = hr[:, None] * G
        t = alternating_opt(Phi, hd, return_trace=True)[2]
        t = t + [t[-1]] * (n_it + 1)
        tr += np.array(t[:n_it + 1])
        lb += sdr(Phi, hd, rng)[0]
    return to_dbm(tr / n_real).tolist(), float(to_dbm(lb / n_real))


STYLE = {
    "Lower bound (SDR)": dict(color="k", ls="--", marker=None),
    "SDR + randomization": dict(color="tab:red", ls="-", marker="o", mfc="none"),
    "Alternating optimization": dict(color="tab:blue", ls="-", marker="x"),
    "AP-user MRT": dict(color="tab:green", ls="-", marker="s", mfc="none"),
    "AP-IRS MRT": dict(color="tab:purple", ls="-", marker="^", mfc="none"),
    "Random phase shift": dict(color="tab:brown", ls="-", marker="d", mfc="none"),
    "Without IRS": dict(color="tab:gray", ls="-", marker="*"),
}


def save(fig, outdir, name):
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, name + ".png"), dpi=200)
    fig.savefig(os.path.join(outdir, name + ".pdf"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    n_real = 20 if args.quick else 1000   # channel realisations per point
    n_sdr = 8 if args.quick else 200      # realisations for the SDP-based curves
    rng = np.random.default_rng(args.seed)
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")
    os.makedirs(outdir, exist_ok=True)
    results = {"params": dict(M=M, d0=D0, dv=DV, C0_dB=C0_DB, alpha_AI=ALPHA_AI,
                              alpha_Iu=ALPHA_IU, alpha_AU=ALPHA_AU,
                              noise_dBm=NOISE_DBM, gamma_dB=GAMMA_DB,
                              realisations=n_real, realisations_sdr=n_sdr, randomisations=N_RAND,
                              seed=args.seed)}
    plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.4})

    # ---- Experiment 1: transmit power vs AP-user horizontal distance -------
    t0 = time.time()
    N1 = 40
    d_grid = [15, 20, 25, 30, 35, 40, 43, 45, 47, 49, 50]
    seeds = [int(x) for x in rng.integers(0, 2 ** 31, len(d_grid))]
    with mp.Pool(min(len(d_grid), os.cpu_count())) as pool:   # SDPs are slow
        res1 = pool.starmap(average, [(sd, N1, d, n_sdr) for sd, d in zip(seeds, d_grid)])
    results["exp1_power_vs_distance"] = {"N": N1, "d": d_grid, "curves": {
        k: [r[k] for r in res1] for k in STYLE}}
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for k, st in STYLE.items():
        ax.plot(d_grid, [r[k] for r in res1], label=k, lw=1.5, **st)
    ax.set_xlabel("AP-user horizontal distance, d (m)")
    ax.set_ylabel("AP transmit power (dBm)")
    ax.set_title(f"M = {M}, N = {N1}, SNR target = {GAMMA_DB:.0f} dB")
    ax.legend(fontsize=8.5)
    save(fig, outdir, "fig1_power_vs_distance")
    print(f"exp1 done in {time.time() - t0:.0f}s")

    # ---- Experiment 2: transmit power vs number of IRS elements ------------
    t0 = time.time()
    N_grid = [10, 20, 30, 40, 50, 60, 80, 100, 120, 160]
    d_list = [15, 41, 50]          # user positions of Fig. 4 in the paper
    res2 = {d: [average(rng, N, d, n_real, with_sdr=False) for N in N_grid]
            for d in d_list}
    results["exp2_power_vs_N"] = {"N": N_grid, "curves": {
        f"d={d}": {k: [r[k] for r in res2[d]]
                   for k in ("Alternating optimization", "Without IRS")}
        for d in d_list}}
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    cols = {15: "tab:green", 41: "tab:orange", 50: "tab:blue"}
    for d in d_list:
        ax.semilogx(N_grid, [r["Alternating optimization"] for r in res2[d]],
                    color=cols[d], marker="o", mfc="none", lw=1.5,
                    label=f"Joint beamforming (AO), d = {d} m")
        ax.semilogx(N_grid, [r["Without IRS"] for r in res2[d]],
                    color=cols[d], ls=":", lw=1.2, label=f"Without IRS, d = {d} m")
    ref = res2[50][-1]["Alternating optimization"]
    ax.semilogx(N_grid, ref - 20 * np.log10(np.array(N_grid) / N_grid[-1]),
                "k--", lw=1.2, label=r"$N^{-2}$ reference (6 dB per doubling)")
    ax.set_xticks(N_grid)
    ax.set_xticklabels([str(n) for n in N_grid], fontsize=8)
    ax.minorticks_off()
    ax.set_xlabel("Number of IRS elements, N")
    ax.set_ylabel("AP transmit power (dBm)")
    ax.set_title(f"M = {M}, SNR target = {GAMMA_DB:.0f} dB")
    ax.legend(fontsize=8)
    save(fig, outdir, "fig2_power_vs_N")
    print(f"exp2 done in {time.time() - t0:.0f}s")

    # ---- Experiment 3: convergence of alternating optimisation -------------
    # The AP-IRS link is varied from pure LoS (rank one) to Rayleigh (full rank)
    t0 = time.time()
    d3, n_it = 45, 6
    k_list = [np.inf, 10.0, 0.0]
    k_name = {np.inf: "LoS (K = inf)", 10.0: "Rician (K = 10 dB)", 0.0: "Rayleigh (K = 0)"}
    seeds = [int(x) for x in rng.integers(0, 2 ** 31, len(k_list))]
    with mp.Pool(len(k_list)) as pool:
        res3 = pool.starmap(convergence, [(sd, N1, d3, k, n_sdr, n_it)
                                          for sd, k in zip(seeds, k_list)])
    results["exp3_convergence"] = {"N": N1, "d": d3, "curves": {
        k_name[k]: {"AO": r[0], "lower_bound": r[1]} for k, r in zip(k_list, res3)}}
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for k, r, c in zip(k_list, res3, ["tab:blue", "tab:orange", "tab:green"]):
        ax.plot(range(n_it + 1), r[0], marker="o", color=c, label="AO, " + k_name[k])
        ax.axhline(r[1], color=c, ls="--", lw=1)
    ax.plot([], [], "k--", lw=1, label="SDR lower bound (same colour)")
    ax.set_xlabel("Alternating-optimization iteration (0 = AP-user MRT start)")
    ax.set_ylabel("AP transmit power (dBm)")
    ax.set_title(f"Convergence of Algorithm 1 (M = {M}, N = {N1}, d = {d3} m)")
    ax.legend(fontsize=9)
    save(fig, outdir, "fig3_convergence")
    print(f"exp3 done in {time.time() - t0:.0f}s")

    # ---- Experiment 4 (extension): finite-resolution phase shifters --------
    t0 = time.time()
    N4 = [10, 20, 40, 80, 160]
    res4 = [average(rng, N, 50, n_real, with_sdr=False, bits=(1, 2, 3)) for N in N4]
    keys4 = ["Alternating optimization", "3-bit phase shifters",
             "2-bit phase shifters", "1-bit phase shifters", "Without IRS"]
    results["exp4_discrete_phase"] = {"N": N4, "d": 50, "curves": {
        k: [r[k] for r in res4] for k in keys4}}
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    mk = ["o", "v", "s", "^", "*"]
    for k, m in zip(keys4, mk):
        lab = "Continuous phase (AO)" if k.startswith("Alt") else k
        ax.semilogx(N4, [r[k] for r in res4], marker=m, mfc="none", lw=1.5, label=lab)
    ax.set_xticks(N4)
    ax.set_xticklabels([str(n) for n in N4])
    ax.minorticks_off()
    ax.set_xlabel("Number of IRS elements, N")
    ax.set_ylabel("AP transmit power (dBm)")
    ax.set_title(f"Effect of phase quantization (d = 50 m, M = {M})")
    ax.legend(fontsize=9)
    save(fig, outdir, "fig4_discrete_phase")
    print(f"exp4 done in {time.time() - t0:.0f}s")

    with open(os.path.join(outdir, "results.json"), "w") as f:
        json.dump(results, f, indent=1)
    print("saved figures and results.json to", os.path.abspath(outdir))


if __name__ == "__main__":
    main()
