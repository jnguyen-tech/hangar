# charts.py
# Phase 4: turn the results into charts for the poster.
# Run load_data.py first to make sure the data loads.

import os
import matplotlib.pyplot as plt
from load_data import load_tracker

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CHARTS_FOLDER = os.path.join(PROJECT_FOLDER, "charts")

# Colors used in every chart, so they all match.
BLUE = "#2a78d6"        # the bar the chart is about
GRAY = "#c3c2b7"        # bars shown for comparison
TEXT = "#0b0b0b"        # titles and numbers
SOFT_TEXT = "#52514e"   # subtitles and axis labels
GRID = "#e1e0d9"        # faint grid lines
BACKGROUND = "#fcfcfb"


def count_on_time(tracker):
    """Count closed jobs that were on time against each of the three targets."""
    counts = {"closed": 0, "original": 0, "regular": 0, "final": 0}
    for job in tracker.jobs:
        if job.status != "closed":
            continue
        counts["closed"] += 1
        if job.actual_days <= tracker.get_original_estimate(job.job_id).target_days:
            counts["original"] += 1
        if job.actual_days <= tracker.get_last_regular_estimate(job.job_id).target_days:
            counts["regular"] += 1
        if job.actual_days <= tracker.get_current_estimate(job.job_id).target_days:
            counts["final"] += 1
    return counts


def style_chart(fig, ax, title, subtitle):
    """Apply the same clean look to every chart."""
    fig.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="x", length=0, labelsize=11, labelcolor=SOFT_TEXT)
    ax.tick_params(axis="y", length=0, labelsize=12, labelcolor=TEXT)
    ax.xaxis.grid(True, color=GRID, linewidth=1)
    ax.set_axisbelow(True)
    ax.set_title(title, loc="left", pad=30, fontsize=15, fontweight="bold", color=TEXT)
    ax.text(0, 1.04, subtitle, transform=ax.transAxes, fontsize=11, color=SOFT_TEXT)


def save_chart(fig, file_name):
    """Save a chart as a high-quality image in the charts folder."""
    os.makedirs(CHARTS_FOLDER, exist_ok=True)
    fig.savefig(os.path.join(CHARTS_FOLDER, file_name), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("Saved", file_name)


def chart_on_time(tracker):
    """Chart 1: how many jobs count as on time, measured against each of the three targets."""
    counts = count_on_time(tracker)
    labels = [
        "Original target",
        "Last target set\nbefore the job finished",
        "Final record\n(after-the-fact revisions)",
    ]
    jobs_on_time = [counts["original"], counts["regular"], counts["final"]]
    percents = []
    for number in jobs_on_time:
        percents.append(round(number / counts["closed"] * 100, 1))

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh(labels, percents, color=[BLUE, GRAY, GRAY], height=0.4)
    ax.invert_yaxis()

    for i in range(len(labels)):
        ax.text(percents[i] + 1.5, i - 0.08, f"{percents[i]}%", va="center",
                fontsize=14, fontweight="bold", color=TEXT)
        ax.text(percents[i] + 1.5, i + 0.13, f"{jobs_on_time[i]:,} jobs", va="center",
                fontsize=10, color=SOFT_TEXT)

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels(["0%", "20%", "40%", "60%", "80%", "100%"])
    style_chart(
        fig, ax,
        "The same jobs look more on time as the target moves",
        f"Share of {counts['closed']:,} completed jobs counted as on time, by the target they are measured against",
    )
    save_chart(fig, "on_time_three_ways.png")


if __name__ == "__main__":
    tracker = load_tracker()
    chart_on_time(tracker)