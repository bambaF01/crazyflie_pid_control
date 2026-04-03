# Flight Logs — Analyse de stabilité Crazyflie

Logs de vol et scripts d'analyse pour évaluer la stabilité en vol stationnaire d'un drone Crazyflie 2.x sous différentes configurations matérielles.

## Structure

```
flight_logs/
├── drone seul/            # Drone sans charge supplémentaire
├── drone+camera+lipo/     # Drone avec caméra et batterie LiPo externe
├── drone+20g/             # Drone avec surcharge de 20 g
├── 1080x720/              # Enregistrement caméra en 1080×720
├── 1920x1080/             # Enregistrement caméra en 1920×1080
├── plots_analyse/         # Graphiques générés
└── analyse_stabilite.py   # Script d'analyse principal
```

Chaque sous-dossier contient un ou plusieurs fichiers CSV nommés `height_vs_time_YYYYMMDD_HHMMSS.csv`.

## Format des CSV

| Colonne        | Description                    |
|----------------|-------------------------------|
| `flight_time_s` | Temps de vol (s)             |
| `vbat_v`        | Tension batterie (V)         |
| `x_m`           | Position X (m)               |
| `y_m`           | Position Y (m)               |
| `z_m`           | Altitude (m)                 |

Consigne d'altitude : **z = 0.3 m** (vol stationnaire).

## Analyse

```bash
python analyse_stabilite.py
```

Le script génère dans `plots_analyse/` :

| Graphique | Description |
|-----------|-------------|
| `stabilite_z_<config>.png` | Altitude z(t) par configuration |
| `histogramme_z.png` | Distribution de l'erreur en altitude |
| `boxplot_z.png` | Boxplot comparatif de l'altitude |
| `comparaison_z_overlay.png` | Superposition z(t) multi-configs |
| `comparaison_std_z_barplot.png` | Écart-type de l'altitude par config |
| `comparaison_rmse_z_barplot.png` | RMSE altitude par config |
| `vbat_3d_*.png` | Décharge batterie en 3D |
| `comparaison_vbat_drop_barplot.png` | Taux de décharge (mV/min) |

## Dépendances

```
numpy
matplotlib
```
