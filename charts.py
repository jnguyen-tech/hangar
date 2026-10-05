# charts.py
# Phase 4: turn the results into charts for the poster.
# Run load_data.py first to make sure the data loads.

import os
import matplotlib.pyplot as plt
from load_data import load_tracker

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CHARTS_FOLDER = os.path.join(PROJECT_FOLDER, "charts")

# Colors used in every chart, so they all match.
BLUE = "#1f4e9e"        # the bar the chart is about
GOLD = "#e0a100"        # changes made after the job finished
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

def chart_slip_by_cause(tracker):
    """Chart 2: which causes added the most delay days."""
    totals = tracker.total_days_by_category(tracker.delay_events)

    # Put the causes in order, biggest first. Tuples sort by their first value.
    pairs = []
    for category in tracker.categories:
        pairs.append((totals[category], category))
    pairs.sort(reverse=True)

    total_days = 0
    for days, category in pairs:
        total_days += days

    labels = []
    percents = []
    for days, category in pairs:
        labels.append(category.replace("_", " ").capitalize())
        percents.append(round(days / total_days * 100, 1))

    colors = [BLUE]
    for i in range(len(pairs) - 1):
        colors.append(GRAY)

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.barh(labels, percents, color=colors, height=0.5)
    ax.invert_yaxis()

    for i in range(len(pairs)):
        ax.text(percents[i] + 0.8, i - 0.1, f"{percents[i]}%", va="center",
                fontsize=14, fontweight="bold", color=TEXT)
        ax.text(percents[i] + 0.8, i + 0.17, f"{pairs[i][0]:,} days", va="center",
                fontsize=10, color=SOFT_TEXT)

    ax.set_xlim(0, 60)
    ax.set_xticks([0, 10, 20, 30, 40, 50, 60])
    ax.set_xticklabels(["0%", "10%", "20%", "30%", "40%", "50%", "60%"])
    style_chart(
        fig, ax,
        "Work discovered mid-job is the biggest cause of delay",
        f"Share of {total_days:,} total delay days across all jobs, by cause",
    )
    save_chart(fig, "slip_by_cause.png")

def chart_job_timeline(tracker, job_id):
    """Chart 3: one job's target date, version by version."""
    job = tracker.find_job(job_id)
    estimates = tracker.get_estimates_for_job(job_id)
    original_days = estimates[0].target_days
    days_late = job.actual_days - original_days

    labels = []
    targets = []
    colors = []
    text_colors = []
    for estimate in estimates:
        if estimate.version == 1:
            labels.append("v1  Original plan")
            colors.append(BLUE)
            text_colors.append("white")
        elif estimate.after_completion:
            labels.append(f"v{estimate.version}  Changed after\nthe job finished")
            colors.append(GOLD)
            text_colors.append(TEXT)
        else:
            labels.append(f"v{estimate.version}  {estimate.reason.capitalize()}")
            colors.append(GRAY)
            text_colors.append(TEXT)
        targets.append(estimate.target_days)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh(labels, targets, color=colors, height=0.5)
    ax.invert_yaxis()

    # Write each target inside the end of its bar, with how far it moved.
    for i in range(len(targets)):
        text = f"{targets[i]} days"
        if i > 0:
            text = f"+{targets[i] - targets[i - 1]}  =  " + text
        ax.text(targets[i] - 3, i, text, va="center", ha="right",
                fontsize=11, color=text_colors[i])

    # A line for the day the job actually finished.
    ax.axvline(job.actual_days, color=TEXT, linewidth=1.5)
    ax.text(job.actual_days + 3, -0.55, f"Finished: day {job.actual_days}",
            fontsize=11, fontweight="bold", color=TEXT)

    # An arrow showing the gap between the original plan and the real finish.
    ax.annotate("", xy=(job.actual_days, 0), xytext=(original_days, 0),
                arrowprops={"arrowstyle": "<->", "color": TEXT})
    ax.text((original_days + job.actual_days) / 2, -0.12, f"{days_late} days late",
            ha="center", fontsize=11, fontweight="bold", color=TEXT)

    ax.set_xlim(0, 270)
    ax.set_ylim(len(targets) - 0.5, -0.8)
    ax.set_xlabel("Days after the job opened", fontsize=11, color=SOFT_TEXT)
    style_chart(
        fig, ax,
        f"This job finished {days_late} days late, but its record says on time",
        f"Job {job_id}: each bar is one version of the target finish date",
    )
    save_chart(fig, "job_timeline.png")

if __name__ == "__main__":
    tracker = load_tracker()
    chart_on_time(tracker)

    chart_slip_by_cause(tracker)

    chart_job_timeline(tracker, "JOB-0000058")