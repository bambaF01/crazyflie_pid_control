#!/usr/bin/env python3
"""
Analyse de stabilité d'un drone Crazyflie en vol stationnaire.
Génère des courbes de :
  1. Stabilité d'altitude z(t)
  2. Analyse de précision (histogramme, boxplot)
  3. Comparaisons multi-configs (superposition z(t), barplot écart-type)
"""

import csv
from pathlib import Path
from typing import Dict, List, Tuple, Tuple

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (utilisé par _plot_vbat_3d_group)

# ── Configuration ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
SETPOINT_Z = 0.3  # consigne d'altitude (m)
OUTPUT_DIR = ROOT / "plots_analyse"
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIGS = {
    "drone seul":        ROOT / "drone seul",
    "drone+camera+lipo": ROOT / "drone+camera+lipo",
    "drone+20g":         ROOT / "drone+20g",
    "1080x720":          ROOT / "1080x720",
    "1920x1080":         ROOT / "1920x1080",
}

COLORS = {
    "drone seul":        "#1f77b4",
    "drone+camera+lipo": "#ff7f0e",
    "drone+20g":         "#2ca02c",
    "1080x720":          "#d62728",
    "1920x1080":         "#9467bd",
}


# ── Chargement des données ───────────────────────────────────────────────────
def load_csv(path: Path) -> Dict[str, np.ndarray]:
    t, vbat, x, y, z = [], [], [], [], []
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t.append(float(row["flight_time_s"]))
                vbat.append(float(row["vbat_v"]))
                x.append(float(row["x_m"]))
                y.append(float(row["y_m"]))
                z.append(float(row["z_m"]))
            except (KeyError, ValueError):
                continue
    return {
        "t": np.array(t), "vbat": np.array(vbat),
        "x": np.array(x), "y": np.array(y), "z": np.array(z),
    }


def load_all() -> Dict[str, List[Dict[str, np.ndarray]]]:
    """Charge tous les CSV par configuration. Retourne {config_name: [run1, run2, ...]}."""
    data = {}
    for name, folder in CONFIGS.items():
        csvs = sorted(folder.glob("*.csv"))
        if csvs:
            data[name] = [load_csv(c) for c in csvs]
    return data


def concat_runs(runs: List[Dict[str, np.ndarray]]) -> Dict[str, np.ndarray]:
    """Concatène tous les runs d'une config."""
    return {k: np.concatenate([r[k] for r in runs]) for k in runs[0]}


# ── 1. STABILITÉ DE POSITION ────────────────────────────────────────────────

def plot_position_vs_time(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """z(t) pour chaque config (premier run)."""
    for name, runs in data.items():
        run = runs[0]
        fig, ax = plt.subplots(figsize=(12, 4))
        fig.suptitle(f"Altitude vs temps — {name}", fontsize=14)

        ax.plot(run["t"], run["z"], color=COLORS[name], linewidth=0.5)
        ax.axhline(SETPOINT_Z, color="gray", linestyle="--", linewidth=1, label=f"Consigne z={SETPOINT_Z} m")
        ax.set_ylabel("z (m)")
        ax.set_xlabel("Temps (s)")
        ax.legend(loc="upper right")

        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / f"stabilite_z_{name.replace('+','_').replace(' ','_')}.png", dpi=150)
        plt.close(fig)


# ── 2. ANALYSE DE PRÉCISION ─────────────────────────────────────────────────

def plot_histogram_z(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Histogramme de z pour chaque config (erreur par rapport à la consigne)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle("Distribution de l'altitude — toutes configs", fontsize=14)

    for name, runs in data.items():
        d = concat_runs(runs)
        err = d["z"] - SETPOINT_Z
        ax.hist(err, bins=80, alpha=0.5, color=COLORS[name], label=name, density=True)
    ax.set_xlabel("Erreur z (m)")
    ax.set_ylabel("Densité")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "histogramme_z.png", dpi=150)
    plt.close(fig)


def plot_boxplot_z(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Boxplot comparatif de l'altitude z par configuration."""
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.suptitle("Boxplot de l'altitude par configuration", fontsize=14)

    config_names = list(data.keys())
    for i, name in enumerate(config_names):
        d = concat_runs(data[name])
        vals = d["z"] - SETPOINT_Z
        bp = ax.boxplot([vals], positions=[i], patch_artist=True, showfliers=False, widths=0.6)
        bp["boxes"][0].set_facecolor(COLORS[name])
        bp["boxes"][0].set_alpha(0.6)
    ax.set_xticks(range(len(config_names)))
    ax.set_xticklabels([n.replace("+", "+\n") for n in config_names])
    ax.set_ylabel("Erreur z (m)")
    ax.grid(True, alpha=0.3, axis="y")
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "boxplot_z.png", dpi=150)
    plt.close(fig)


# ── 3. COMPARAISONS MULTI-CONFIGS ───────────────────────────────────────────

def plot_z_overlay(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Superposition de z(t) pour toutes les configs (premier run)."""
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.set_title("Altitude z(t) — comparaison multi-configs (1er run)")
    for name, runs in data.items():
        run = runs[0]
        ax.plot(run["t"], run["z"], linewidth=0.5, color=COLORS[name], label=name, alpha=0.8)
    ax.axhline(SETPOINT_Z, color="gray", linestyle="--", linewidth=1, label=f"Consigne ({SETPOINT_Z} m)")
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("z (m)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comparaison_z_overlay.png", dpi=150)
    plt.close(fig)


def plot_std_barplot(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Barplot de l'écart-type de z par configuration."""
    config_names = list(data.keys())
    std_z = []
    for name in config_names:
        d = concat_runs(data[name])
        std_z.append(np.std(d["z"]))

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(config_names, std_z, color=[COLORS[n] for n in config_names], alpha=0.8)
    for bar, val in zip(bars, std_z):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0005,
                f"{val*100:.2f} cm", ha="center", va="bottom", fontsize=9)
    ax.set_xticklabels([n.replace("+", "+\n") for n in config_names])
    ax.set_ylabel("Écart-type z (m)")
    ax.set_title("Écart-type de l'altitude par configuration")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comparaison_std_z_barplot.png", dpi=150)
    plt.close(fig)


def plot_rmse_barplot(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Barplot du RMSE z par configuration (erreur par rapport à la consigne)."""
    config_names = list(data.keys())
    rmse_vals = []
    for name in config_names:
        d = concat_runs(data[name])
        err_z = d["z"] - SETPOINT_Z
        rmse = np.sqrt(np.mean(err_z**2))
        rmse_vals.append(rmse)

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(config_names, rmse_vals, color=[COLORS[n] for n in config_names], alpha=0.8)
    for bar, val in zip(bars, rmse_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0005,
                f"{val*100:.2f} cm", ha="center", va="bottom", fontsize=9)
    ax.set_xticklabels([n.replace("+", "+\n") for n in config_names])
    ax.set_ylabel("RMSE z (m)")
    ax.set_title("RMSE altitude par configuration")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comparaison_rmse_z_barplot.png", dpi=150)
    plt.close(fig)


# ── 4. BATTERIE (logique 3D identique à plot_vbat_3d.py) ─────────────────────

def _average_series(
    runs: List[Dict[str, np.ndarray]],
) -> Tuple[np.ndarray, np.ndarray]:
    """Moyenne les courbes vbat(t) de plusieurs runs sur une grille commune."""
    series = [(r["t"], r["vbat"]) for r in runs if len(r["t"]) >= 2]
    if not series:
        return np.array([]), np.array([])

    t_start = min(s[0][0] for s in series)
    t_end = max(s[0][-1] for s in series)
    dt = max(float(np.median(np.diff(s[0]))) for s in series)
    grid = np.arange(t_start, t_end + 1e-9, dt)

    vals = np.full((len(series), len(grid)), np.nan)
    for i, (t, v) in enumerate(series):
        mask = (grid >= t[0]) & (grid <= t[-1])
        if np.any(mask):
            vals[i, mask] = np.interp(grid[mask], t, v)

    avg = np.nanmean(vals, axis=0)
    return grid, avg


def _plot_vbat_3d_group(
    data: Dict[str, List[Dict[str, np.ndarray]]],
    group_configs: List[str],
    out_name: str,
) -> None:
    """Plot 3D pour un groupe de configs : X=temps, Y=config, Z=vbat."""
    Z_BASE = 3.0
    SPACING = 0.15

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    y_pos = {name: i * SPACING for i, name in enumerate(group_configs)}
    z_max = Z_BASE + 0.1

    for idx, name in enumerate(group_configs):
        if name not in data:
            continue
        avg_t, avg_v = _average_series(data[name])
        if len(avg_t) == 0:
            continue

        # Forcer la courbe à atteindre Z_BASE à la fin
        dt = avg_t[1] - avg_t[0] if len(avg_t) > 1 else 0.05
        if avg_v[-1] != Z_BASE:
            t_end = min(avg_t[-1] + dt, 1000.0)
            if t_end > avg_t[-1]:
                avg_t = np.append(avg_t, t_end)
                avg_v = np.append(avg_v, Z_BASE)
            else:
                avg_v[-1] = Z_BASE

        ys = np.full_like(avg_t, y_pos[name])
        color = COLORS[name]

        # Courbe principale
        ax.plot(avg_t, ys, avg_v, color=color, linewidth=2.0, alpha=0.85,
                label=f"{name} (moy.)")

        # Projection sur le plan z=Z_BASE
        ax.plot(avg_t, ys, np.full_like(avg_t, Z_BASE),
                color=color, linewidth=1.2, alpha=0.45)

        # Lignes verticales de chute
        stride = max(1, len(avg_t) // 120)
        for i in range(0, len(avg_t), stride):
            ax.plot([avg_t[i], avg_t[i]],
                    [y_pos[name], y_pos[name]],
                    [Z_BASE, avg_v[i]],
                    color=color, linewidth=0.8, alpha=0.35)

        z_max = max(z_max, avg_v.max())

    ax.set_xlabel("Temps (s)")
    ax.set_ylabel("")
    ax.set_zlabel("Batterie (V)")
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(group_configs)
    ax.set_xlim(0, 1000)
    ax.set_zlim(Z_BASE, z_max)
    ax.set_proj_type("ortho")
    ax.view_init(elev=25, azim=-60)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / out_name, dpi=200)
    plt.close(fig)


def plot_vbat_3d(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Deux plots 3D séparés (même logique que plot_vbat_3d.py)."""
    config_names = list(data.keys())
    group_a = [n for n in ["drone+20g", "drone seul"] if n in config_names]
    group_b = [n for n in config_names if n not in group_a]

    if group_a:
        _plot_vbat_3d_group(data, group_a, "vbat_3d_drone_seul_plus_20g.png")
    if group_b:
        _plot_vbat_3d_group(data, group_b, "vbat_3d_autres.png")


def plot_vbat_drop_barplot(data: Dict[str, List[Dict[str, np.ndarray]]]) -> None:
    """Barplot du taux de décharge (mV/min) par configuration."""
    config_names = list(data.keys())
    drop_rates = []
    for name in config_names:
        rates = []
        for run in data[name]:
            dt_min = (run["t"][-1] - run["t"][0]) / 60.0
            if dt_min > 0:
                dv = run["vbat"][0] - run["vbat"][-1]
                rates.append(dv / dt_min * 1000)
        drop_rates.append(np.mean(rates))

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(config_names, drop_rates, color=[COLORS[n] for n in config_names], alpha=0.8)
    for bar, val in zip(bars, drop_rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                f"{val:.1f} mV/min", ha="center", va="bottom", fontsize=9)
    ax.set_xticklabels([n.replace("+", "+\n") for n in config_names])
    ax.set_ylabel("Taux de décharge (mV/min)")
    ax.set_title("Vitesse de décharge batterie par configuration")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "comparaison_vbat_drop_barplot.png", dpi=150)
    plt.close(fig)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Chargement des données...")
    data = load_all()
    print(f"  {len(data)} configurations chargées : {', '.join(data.keys())}")

    print("1. Stabilité d'altitude...")
    plot_position_vs_time(data)

    print("2. Analyse de précision...")
    plot_histogram_z(data)
    plot_boxplot_z(data)

    print("3. Comparaisons multi-configs...")
    plot_z_overlay(data)
    plot_std_barplot(data)
    plot_rmse_barplot(data)

    print("4. Batterie...")
    plot_vbat_3d(data)
    plot_vbat_drop_barplot(data)

    print(f"\nTerminé ! {len(list(OUTPUT_DIR.glob('*.png')))} graphiques sauvegardés dans {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
