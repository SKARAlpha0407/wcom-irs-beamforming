"""Draws the system-model / simulation-geometry figure used in the report and slides."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")
os.makedirs(out, exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 3.6))
ax.set_xlim(-1.2, 11.2)
ax.set_ylim(-1.5, 4.4)
ax.axis("off")

NAVY, TEAL, RED, GREY = "#14324a", "#0e8a8a", "#c0392b", "#666666"

# AP
ax.add_patch(Rectangle((-0.5, 2.4), 1.0, 1.2, fc="#dfe9f1", ec=NAVY, lw=1.5))
for i in range(4):
    ax.plot([-0.35 + 0.23 * i] * 2, [3.6, 3.95], color=NAVY, lw=1.5)
    ax.plot(-0.35 + 0.23 * i, 3.98, marker="v", color=NAVY, ms=5)
ax.text(0, 2.2, "AP\n(M antennas)", ha="center", va="top", fontsize=10, color=NAVY)

# IRS
for i in range(8):
    for j in range(3):
        ax.add_patch(Rectangle((8.9 + 0.2 * i, 3.1 + 0.2 * j), 0.16, 0.16, fc=TEAL, ec="white", lw=0.3))
ax.text(9.7, 3.85, "IRS (N passive elements)", ha="center", va="bottom", fontsize=10, color=TEAL)

# user
ax.plot(6.5, 0.2, marker="o", ms=11, color=RED)
ax.text(6.5, -0.15, "User (1 antenna)", ha="center", va="top", fontsize=10, color=RED)

# obstacle
ax.add_patch(Rectangle((3.0, 0.9), 0.9, 1.0, fc="#bbbbbb", ec=GREY, hatch="///", lw=1))
ax.text(3.45, 0.75, "blockage", ha="center", va="top", fontsize=8, color=GREY)


def arrow(p, q, color, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.8, ls=ls))


arrow((0.55, 3.25), (8.85, 3.35), TEAL)
ax.text(4.6, 3.45, r"$\mathbf{G}$  (AP-IRS link, LoS)", ha="center", fontsize=10, color=TEAL)
arrow((9.3, 3.05), (6.65, 0.4), TEAL)
ax.text(8.35, 1.55, r"$\mathbf{h}_r^H$  (IRS-user link)", ha="left", fontsize=10, color=TEAL)
arrow((0.55, 2.7), (6.3, 0.3), RED, ls="--")
ax.text(1.75, 1.2, r"$\mathbf{h}_d^H$  (weak direct link)", ha="center", fontsize=10,
        color=RED, rotation=-22)

# dimensions
ax.annotate("", xy=(9.7, -0.95), xytext=(0, -0.95), arrowprops=dict(arrowstyle="<->", color=GREY))
ax.text(4.85, -1.0, r"$d_0 = 51$ m", ha="center", va="top", fontsize=9, color=GREY)
ax.annotate("", xy=(6.5, -0.6), xytext=(0, -0.6), arrowprops=dict(arrowstyle="<->", color=GREY))
ax.text(3.25, -0.55, r"$d$ (user position)", ha="center", va="bottom", fontsize=9, color=GREY)
ax.plot([0, 10.8], [0.2, 0.2], color=GREY, lw=0.6, ls=":")
ax.annotate("", xy=(10.6, 3.05), xytext=(10.6, 0.2), arrowprops=dict(arrowstyle="<->", color=GREY))
ax.text(10.7, 1.6, r"$d_v = 2$ m", ha="left", va="center", fontsize=9, color=GREY)

fig.tight_layout()
fig.savefig(os.path.join(out, "system_model.png"), dpi=220)
fig.savefig(os.path.join(out, "system_model.pdf"))
print("saved system_model")
