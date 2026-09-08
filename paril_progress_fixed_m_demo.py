import os

os.environ.setdefault("XDG_CACHE_HOME", "/tmp")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

N = 50
K = 5
m = 0.1
lambda_s = 1.0
lambda_a = 100.0

base_progress = np.linspace(0.0, 1.0, N)
local_wave = np.zeros(N)
local_wave[7:11] = np.array([0.00, 0.012, -0.010, 0.00])
local_wave[12:17] = np.array([0.00, 0.015, -0.010, 0.012, 0.00])
local_wave[17:20] = np.array([0.00, -0.014, 0.00])
local_wave[20:25] = np.array([0.00, -0.018, 0.014, -0.012, 0.00])
local_wave[24:27] = np.array([0.00, 0.013, 0.00])
local_wave[34:37] = np.array([0.00, -0.015, 0.00])
local_wave[36:41] = np.array([0.00, 0.012, -0.016, 0.010, 0.00])
local_wave[41:45] = np.array([0.00, -0.011, 0.014, 0.00])

large_wave = np.zeros(N)
large_wave[26:35] = np.array([
    0.00, 0.075, 0.125, 0.060, -0.025,
    -0.095, -0.125, -0.055, 0.00
])

true_progress = np.clip(base_progress + local_wave + large_wave, 0.0, 1.0)
true_progress[0] = 0.0
true_progress[-1] = 1.0

edges = []
comparison_matrix = np.full((N, N), np.nan)
for i in range(N):
    for j in range(i + 1, min(i + K + 1, N)):
        diff = true_progress[j] - true_progress[i]
        if diff > 1e-9:
            r = 1
        elif diff < -1e-9:
            r = -1
        else:
            r = 0
        edges.append((i, j, r))
        comparison_matrix[i, j] = r


def visualize_comparison_matrix(matrix, output_path="original_comparison_matrix.png"):
    masked_matrix = np.ma.masked_invalid(matrix)

    fig, ax = plt.subplots(figsize=(9, 7))
    cmap = plt.get_cmap("coolwarm").copy()
    cmap.set_bad(color="#f2f2f2")
    image = ax.imshow(masked_matrix, cmap=cmap, vmin=-1, vmax=1)

    ax.set_title("Original Pairwise Progress Matrix")
    ax.set_xlabel("j")
    ax.set_ylabel("i")
    tick_step = 5
    ax.set_xticks(np.arange(0, N, tick_step))
    ax.set_yticks(np.arange(0, N, tick_step))
    ax.set_xticks(np.arange(-0.5, N, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, N, 1), minor=True)
    ax.tick_params(axis="x", labelrotation=90)
    ax.grid(which="minor", color="white", linewidth=0.5)

    cbar = fig.colorbar(image, ax=ax, ticks=[-1, 0, 1])
    cbar.ax.set_yticklabels(["backward", "equal", "forward"])

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    return fig


def visualize_progress_curve(true_values, optimized_values, output_path="final_progress_curve.png"):
    samples = np.arange(len(true_values))

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(samples, true_values, marker="o", linewidth=2, label="Synthetic true progress")
    ax.plot(samples, optimized_values, marker="s", linewidth=2, label="Optimized P")
    ax.set_title("Final Progress Curve")
    ax.set_xlabel("sample")
    ax.set_ylabel("progress")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(np.arange(0, len(true_values), 5))
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    return fig


def objective(P):
    pair_loss = sum(
        (P[j] - P[i] - m * r) ** 2
        for i, j, r in edges
    )

    smooth_loss = np.sum(
        (P[2:] - 2.0 * P[1:-1] + P[:-2]) ** 2
    )

    anchor_loss = P[0] ** 2 + (P[-1] - 1.0) ** 2

    return (
        pair_loss
        + lambda_s * smooth_loss
        + lambda_a * anchor_loss
    )

P_init = np.linspace(0.0, 1.0, N)

result = minimize(
    objective,
    P_init,
    method="L-BFGS-B",
    bounds=[(0.0, 1.0)] * N,
)

P_star = result.x
delta_P = np.r_[np.diff(P_star), np.nan]

df = pd.DataFrame({
    "sample": np.arange(N),
    "synthetic_true_progress": np.round(true_progress, 3),
    "optimized_P": np.round(P_star, 3),
    "Delta_P_next": np.round(delta_P, 3),
})

print("Optimization success:", result.success)
print("Final objective:", result.fun)
print(df.to_string(index=False))

visualize_comparison_matrix(comparison_matrix)
visualize_progress_curve(true_progress, P_star)
print("Saved visualizations:")
print("  original_comparison_matrix.png")
print("  final_progress_curve.png")

if plt.get_backend().lower() != "agg":
    plt.show()
