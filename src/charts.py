"""PNG charts for the README (the interactive version is the Power BI report)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, ORANGE, GREY = "#1F3A5F", "#E07B39", "#9AA5B1"


def bar(t, x, y, title, path, color=BLUE, fmt="{:,.0f}"):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.barh(t[x][::-1], t[y][::-1], color=color)
    for i, v in enumerate(t[y][::-1]):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=8)
    ax.set_title(title, loc="left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def women_by_level(t, path):
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.bar(t["job_level"], t["women_share_pct"], color=ORANGE)
    for i, v in enumerate(t["women_share_pct"]):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=8)
    ax.set_ylim(0, 60); ax.set_ylabel("% women")
    ax.set_title("Women share by job level (31 Dec 2025)", loc="left", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
