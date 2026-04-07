"""
Visualization Module.

Generates charts, graphs, and visual analysis for abuse patterns,
court case timelines, financial analysis, and scorecards.
All charts are saved as images for embedding in reports.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from datetime import datetime


class ReportVisualizer:
    """Generates all charts and graphs for the analysis report."""

    def __init__(self, output_dir="output/charts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.generated_charts = []

        # Style
        plt.rcParams.update({
            "figure.facecolor": "white",
            "axes.facecolor": "#f8f9fa",
            "axes.grid": True,
            "grid.alpha": 0.3,
            "font.size": 10,
        })

    def _save(self, fig, name):
        path = os.path.join(self.output_dir, f"{name}.png")
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        self.generated_charts.append(path)
        return path

    # ------------------------------------------------------------------
    # Abuse pattern charts
    # ------------------------------------------------------------------

    def plot_abuse_timeline(self, df, date_col="date", score_col="severity_score"):
        """Plot abuse incidents over time with severity."""
        if df.empty or date_col not in df.columns:
            return None

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        fig, ax = plt.subplots(figsize=(14, 6))

        if score_col in df.columns:
            scores = df[score_col].fillna(0).astype(float)
            colors = ["#2ecc71" if s < 3 else "#f39c12" if s < 6 else "#e74c3c" for s in scores]
            ax.scatter(df[date_col], scores, c=colors, s=80, zorder=5, edgecolors="white", linewidth=0.5)
            ax.plot(df[date_col], scores, color="#3498db", alpha=0.4, linewidth=1)

            # Trend line
            x_num = mdates.date2num(df[date_col])
            if len(x_num) >= 2:
                z = np.polyfit(x_num, scores.values, 1)
                p = np.poly1d(z)
                ax.plot(df[date_col], p(x_num), "--", color="#e74c3c", alpha=0.7,
                        linewidth=2, label="Trend")

            ax.set_ylabel("Severity Score")
        else:
            ax.scatter(df[date_col], [1] * len(df), c="#e74c3c", s=60, zorder=5)
            ax.set_ylabel("Incidents")

        ax.set_xlabel("Date")
        ax.set_title("Abuse Incident Timeline with Severity", fontsize=14, fontweight="bold")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        fig.autofmt_xdate()

        return self._save(fig, "abuse_timeline")

    def plot_abuse_type_distribution(self, df, type_col="primary_abuse_type"):
        """Pie chart of abuse type distribution."""
        if df.empty or type_col not in df.columns:
            return None

        counts = df[type_col].value_counts()
        if counts.empty:
            return None

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set2(np.linspace(0, 1, len(counts)))
        wedges, texts, autotexts = ax.pie(
            counts.values, labels=counts.index, autopct="%1.1f%%",
            colors=colors, startangle=90, pctdistance=0.85
        )
        for t in autotexts:
            t.set_fontsize(9)
        ax.set_title("Distribution of Abuse Types", fontsize=14, fontweight="bold")

        return self._save(fig, "abuse_type_distribution")

    def plot_severity_heatmap(self, df, date_col="date", score_col="severity_score"):
        """Monthly severity heatmap."""
        if df.empty or date_col not in df.columns or score_col not in df.columns:
            return None

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col])
        df["year"] = df[date_col].dt.year
        df["month"] = df[date_col].dt.month

        pivot = df.pivot_table(values=score_col, index="year", columns="month",
                               aggfunc="mean")
        if pivot.empty:
            return None

        fig, ax = plt.subplots(figsize=(14, max(4, len(pivot) * 0.8 + 2)))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        pivot.columns = [month_names[m - 1] for m in pivot.columns]

        im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index.astype(int))
        plt.colorbar(im, ax=ax, label="Avg Severity")
        ax.set_title("Monthly Abuse Severity Heatmap", fontsize=14, fontweight="bold")

        return self._save(fig, "severity_heatmap")

    def plot_cycle_prediction(self, predictions, historical_df=None,
                              date_col="date", score_col="severity_score"):
        """Plot historical data with predicted future cycles."""
        fig, ax = plt.subplots(figsize=(14, 6))

        # Historical
        if historical_df is not None and not historical_df.empty:
            df = historical_df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col]).sort_values(date_col)
            if score_col in df.columns:
                ax.plot(df[date_col], df[score_col].astype(float), "o-",
                        color="#3498db", label="Historical", markersize=5)

        # Predictions
        if predictions and isinstance(predictions, list):
            pred_dates = pd.to_datetime([p["predicted_date"] for p in predictions])
            pred_scores = [p["predicted_severity"] for p in predictions]
            pred_early = pd.to_datetime([p["earliest_date"] for p in predictions])
            pred_late = pd.to_datetime([p["latest_date"] for p in predictions])

            ax.plot(pred_dates, pred_scores, "s--", color="#e74c3c",
                    label="Predicted", markersize=8)
            ax.fill_between(pred_dates, [0] * len(pred_dates), pred_scores,
                            alpha=0.1, color="#e74c3c")

            # Confidence window
            for i, (early, late, score) in enumerate(zip(pred_early, pred_late, pred_scores)):
                ax.axvspan(early, late, alpha=0.05, color="red")
                ax.annotate(
                    f"Cycle {i + 1}\n{predictions[i]['confidence']:.0%} conf",
                    xy=(pred_dates[i], score),
                    xytext=(0, 15), textcoords="offset points",
                    fontsize=8, ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.8),
                )

        ax.set_xlabel("Date")
        ax.set_ylabel("Severity Score")
        ax.set_title("Abuse Cycle Analysis — Historical & Predicted",
                      fontsize=14, fontweight="bold")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        fig.autofmt_xdate()

        return self._save(fig, "cycle_prediction")

    # ------------------------------------------------------------------
    # Court case charts
    # ------------------------------------------------------------------

    def plot_filing_timeline(self, filings_df, date_col="date"):
        """Plot court filings over time."""
        if filings_df.empty or date_col not in filings_df.columns:
            return None

        df = filings_df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[2, 1])

        # Timeline scatter
        type_col = None
        for c in ["type", "filing_type", "action"]:
            if c in df.columns:
                type_col = c
                break

        if type_col:
            types = df[type_col].fillna("Other").astype(str)
            unique_types = types.unique()
            color_map = {t: plt.cm.tab10(i / max(len(unique_types), 1))
                         for i, t in enumerate(unique_types)}
            colors = [color_map[t] for t in types]
            ax1.scatter(df[date_col], types, c=colors, s=60, zorder=5)
        else:
            ax1.scatter(df[date_col], [0] * len(df), s=60, c="#3498db")

        ax1.set_title("Court Filing Timeline", fontsize=14, fontweight="bold")
        ax1.set_xlabel("Date")
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

        # Monthly filing counts
        monthly = df.set_index(date_col).resample("ME").size()
        ax2.bar(monthly.index, monthly.values, width=25, color="#3498db", alpha=0.7)
        ax2.set_ylabel("Filings per Month")
        ax2.set_title("Monthly Filing Volume", fontsize=12)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

        fig.autofmt_xdate()
        fig.tight_layout()
        return self._save(fig, "filing_timeline")

    def plot_officials_involvement(self, officials_summary_df):
        """Bar chart of official involvement levels."""
        if officials_summary_df.empty:
            return None

        df = officials_summary_df.sort_values("total_appearances", ascending=True).tail(20)

        fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.4)))
        colors = ["#e74c3c" if r in ("judge", "magistrate") else
                  "#f39c12" if "gal" in r or "guardian" in r else
                  "#3498db"
                  for r in df["role"].str.lower()]

        bars = ax.barh(df["name"], df["total_appearances"], color=colors, edgecolor="white")
        ax.set_xlabel("Number of Appearances")
        ax.set_title("Court Officials — Case Involvement", fontsize=14, fontweight="bold")

        # Add role labels
        for bar, role in zip(bars, df["role"]):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    f" ({role})", va="center", fontsize=8, color="#555")

        fig.tight_layout()
        return self._save(fig, "officials_involvement")

    def plot_financial_breakdown(self, costs_data):
        """Bar chart of financial costs per party and per official."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Per party
        ax1 = axes[0]
        per_party = costs_data.get("per_party", {})
        if per_party:
            names = list(per_party.keys())
            values = list(per_party.values())
            ax1.barh(names, values, color="#e74c3c")
            ax1.set_xlabel("Amount ($)")
            ax1.set_title("Costs by Party")
            for i, v in enumerate(values):
                ax1.text(v + 100, i, f"${v:,.0f}", va="center", fontsize=9)
        else:
            ax1.text(0.5, 0.5, "No party cost data", ha="center", va="center",
                     transform=ax1.transAxes)

        # Per official
        ax2 = axes[1]
        per_official = costs_data.get("per_official", {})
        if per_official:
            names = list(per_official.keys())
            values = list(per_official.values())
            ax2.barh(names, values, color="#f39c12")
            ax2.set_xlabel("Amount ($)")
            ax2.set_title("Earnings by Official")
            for i, v in enumerate(values):
                ax2.text(v + 100, i, f"${v:,.0f}", va="center", fontsize=9)
        else:
            ax2.text(0.5, 0.5, "No official earnings data", ha="center", va="center",
                     transform=ax2.transAxes)

        fig.suptitle("Financial Analysis", fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, "financial_breakdown")

    def plot_violation_summary(self, violations):
        """Chart of procedural violations by type and severity."""
        if not violations:
            return None

        df = pd.DataFrame(violations)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # By type
        type_counts = df["type"].value_counts()
        ax1.barh(type_counts.index, type_counts.values, color="#9b59b6")
        ax1.set_xlabel("Count")
        ax1.set_title("Violations by Type")

        # By severity
        if "severity" in df.columns:
            sev_counts = df["severity"].value_counts()
            colors = {"CRITICAL": "#c0392b", "HIGH": "#e74c3c",
                      "MODERATE": "#f39c12", "LOW": "#2ecc71"}
            sev_colors = [colors.get(s, "#3498db") for s in sev_counts.index]
            ax2.bar(sev_counts.index, sev_counts.values, color=sev_colors)
            ax2.set_ylabel("Count")
            ax2.set_title("Violations by Severity")

        fig.suptitle("Procedural Violations Summary", fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self._save(fig, "violations_summary")

    # ------------------------------------------------------------------
    # Scorecard visuals
    # ------------------------------------------------------------------

    def plot_scorecards(self, scorecards_df):
        """Visual scorecard comparison for all officials."""
        if scorecards_df.empty:
            return None

        df = scorecards_df.sort_values("overall_score", ascending=True)

        fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.6)))

        colors = []
        for score in df["overall_score"]:
            if score >= 70:
                colors.append("#2ecc71")
            elif score >= 50:
                colors.append("#f39c12")
            else:
                colors.append("#e74c3c")

        bars = ax.barh(
            [f"{n}\n({r})" for n, r in zip(df["name"], df["role"])],
            df["overall_score"],
            color=colors,
            edgecolor="white",
            linewidth=0.5,
        )

        # Add grade labels
        for bar, grade in zip(bars, df["overall_grade"]):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                    f" {grade}", va="center", fontsize=11, fontweight="bold")

        ax.set_xlim(0, 110)
        ax.set_xlabel("Score (0-100)")
        ax.set_title("Court Official Scorecards", fontsize=14, fontweight="bold")
        ax.axvline(x=50, color="red", linestyle="--", alpha=0.4, label="Concern Threshold")
        ax.axvline(x=70, color="orange", linestyle="--", alpha=0.4, label="Acceptable Threshold")
        ax.legend(loc="lower right")

        fig.tight_layout()
        return self._save(fig, "official_scorecards")

    def plot_connection_network(self, connections):
        """Simple network visualization of connections between officials."""
        if not connections:
            return None

        fig, ax = plt.subplots(figsize=(12, 10))

        # Collect unique nodes
        nodes = set()
        for c in connections:
            nodes.add((c["person_1"], c["role_1"]))
            nodes.add((c["person_2"], c["role_2"]))

        nodes = list(nodes)
        n = len(nodes)
        if n == 0:
            return None

        # Position nodes in a circle
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        positions = {node[0]: (np.cos(a) * 4, np.sin(a) * 4)
                     for node, a in zip(nodes, angles)}

        # Draw edges
        for c in connections:
            p1 = positions[c["person_1"]]
            p2 = positions[c["person_2"]]
            strength = c.get("strength", 1)
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
                    color="#e74c3c", alpha=min(0.8, 0.2 + strength * 0.1),
                    linewidth=max(1, strength * 0.5))

        # Draw nodes
        role_colors = {"judge": "#e74c3c", "attorney": "#3498db",
                       "gal": "#f39c12", "guardian": "#f39c12",
                       "mediator": "#2ecc71"}
        for (name, role), pos in zip(nodes, [positions[n[0]] for n in nodes]):
            color = "#999"
            for key, c in role_colors.items():
                if key in role.lower():
                    color = c
                    break
            ax.scatter(*pos, s=300, c=color, zorder=5, edgecolors="white", linewidth=2)
            ax.annotate(f"{name}\n({role})", xy=pos, xytext=(0, 15),
                        textcoords="offset points", ha="center", fontsize=8,
                        fontweight="bold",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

        ax.set_xlim(-6, 6)
        ax.set_ylim(-6, 6)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("Court Official Connections Network", fontsize=14, fontweight="bold")

        return self._save(fig, "connection_network")

    def plot_document_comparison(self, side_by_side_rows, title_a="Doc A", title_b="Doc B"):
        """Visualize document comparison match scores."""
        if not side_by_side_rows:
            return None

        df = pd.DataFrame(side_by_side_rows)
        if "match_score" not in df.columns:
            return None

        fig, ax = plt.subplots(figsize=(14, 6))
        scores = df["match_score"].values
        colors = ["#2ecc71" if s > 0.8 else "#f39c12" if s > 0.4 else "#e74c3c" for s in scores]

        ax.bar(range(len(scores)), scores, color=colors, width=1.0, edgecolor="none")
        ax.set_xlabel("Line Number")
        ax.set_ylabel("Match Score")
        ax.set_title(f"Document Comparison: {title_a} vs {title_b}",
                      fontsize=14, fontweight="bold")
        ax.axhline(y=0.8, color="green", linestyle="--", alpha=0.5, label="High Match")
        ax.axhline(y=0.4, color="orange", linestyle="--", alpha=0.5, label="Partial Match")
        ax.legend()

        return self._save(fig, "document_comparison")
