# -*- coding: utf-8 -*-
"""Plot hauteur(t) a partir d'un ou plusieurs CSV."""
import csv
import os
import sys
import time
from collections import defaultdict

try:
    import matplotlib
    if "--show" not in sys.argv:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception as e:
    print("[ERR] matplotlib est requis pour tracer les courbes:", e)
    sys.exit(1)


def load_data(csv_path):
    series = defaultdict(list)
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = float(row["time_s"])
                h = float(row["height_m"])
                kp = float(row["kp"])
            except (KeyError, ValueError):
                continue
            series[kp].append((t, h))
    return series


def load_single_series(csv_path):
    data = []
    kp_values = set()
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t = float(row["time_s"])
                h = float(row["height_m"])
            except (KeyError, ValueError):
                continue
            data.append((t, h))
            try:
                kp_values.add(float(row["kp"]))
            except (KeyError, ValueError):
                pass
    kp_label = None
    if len(kp_values) == 1:
        kp_label = "Kp={:.2f}".format(next(iter(kp_values)))
    return data, kp_label


def plot_series(series, out_path=None, show=False):
    if not series:
        print("[ERR] Aucune donnee a tracer")
        return

    plt.figure()
    for kp in sorted(series.keys()):
        data = series[kp]
        if not data:
            continue
        data.sort(key=lambda x: x[0])
        t_vals = [t for t, _ in data]
        h_vals = [h for _, h in data]
        plt.plot(t_vals, h_vals, label="Kp={:.2f}".format(kp))

    plt.xlabel("Temps (s)")
    plt.ylabel("Hauteur (m)")
    plt.title("Hauteur en fonction du temps pour differentes valeurs de Kp")
    plt.legend()
    plt.grid(True, alpha=0.3)

    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print("[OK] Figure sauvegardee: {}".format(out_path))
    if show:
        plt.show()
    plt.close()


def plot_multi_csv(csv_paths, out_path=None, show=False):
    if not csv_paths:
        print("[ERR] Aucune donnee a tracer")
        return

    plt.figure()
    for csv_path in csv_paths:
        data, kp_label = load_single_series(csv_path)
        if not data:
            continue
        data.sort(key=lambda x: x[0])
        t_vals = [t for t, _ in data]
        h_vals = [h for _, h in data]
        base = os.path.splitext(os.path.basename(csv_path))[0]
        if kp_label:
            label = "{} ({})".format(base, kp_label)
        else:
            label = base
        plt.plot(t_vals, h_vals, label=label)

    plt.xlabel("Temps (s)")
    plt.ylabel("Hauteur (m)")
    plt.title("Hauteur en fonction du temps (une courbe par CSV)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    if out_path:
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print("[OK] Figure sauvegardee: {}".format(out_path))
    if show:
        plt.show()
    plt.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plot_k_height.py <csv_path> [<csv_path> ...] [--show] [--combine]")
        sys.exit(1)

    show = "--show" in sys.argv[1:]
    combine = "--combine" in sys.argv[1:]
    csv_paths = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if not csv_paths:
        print("[ERR] Aucun CSV fourni")
        sys.exit(1)

    for csv_path in csv_paths:
        if not os.path.isfile(csv_path):
            print("[ERR] Fichier introuvable:", csv_path)
            sys.exit(1)

    if len(csv_paths) == 1:
        out_dir = os.path.join(os.path.dirname(csv_paths[0]), "plots")
        os.makedirs(out_dir, exist_ok=True)
        series = load_data(csv_paths[0])
        base = os.path.splitext(os.path.basename(csv_paths[0]))[0]
        out_path = os.path.join(out_dir, "{}.png".format(base))
        plot_series(series, out_path=out_path, show=show)
    elif combine:
        out_dir = os.path.join(os.path.dirname(csv_paths[0]), "plots")
        os.makedirs(out_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(out_dir, "multi_csv_{}.png".format(ts))
        plot_multi_csv(csv_paths, out_path=out_path, show=show)
    else:
        for csv_path in csv_paths:
            out_dir = os.path.join(os.path.dirname(csv_path), "plots")
            os.makedirs(out_dir, exist_ok=True)
            series = load_data(csv_path)
            base = os.path.splitext(os.path.basename(csv_path))[0]
            out_path = os.path.join(out_dir, "{}.png".format(base))
            plot_series(series, out_path=out_path, show=show)
