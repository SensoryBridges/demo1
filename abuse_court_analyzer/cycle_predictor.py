"""
Abuse Cycle Prediction Engine.

Uses statistical analysis and time-series modeling to predict
future abuse cycles based on historical patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from scipy.signal import find_peaks


class CyclePredictor:
    """Predicts abuse cycle timing and intensity."""

    def __init__(self):
        self.cycle_data = None
        self.predictions = []
        self.pattern_analysis = {}

    def analyze_cycles(self, df, date_col="date", score_col="severity_score"):
        """
        Analyze temporal patterns in abuse incidents.

        Returns cycle analysis including:
        - Average cycle length
        - Escalation patterns
        - Trigger correlations
        - Seasonal/calendar patterns
        """
        if df.empty or date_col not in df.columns:
            return {"error": "Insufficient data for cycle analysis"}

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        if len(df) < 3:
            return {"error": "Need at least 3 incidents for cycle analysis"}

        self.cycle_data = df
        analysis = {}

        # 1. Inter-incident intervals
        dates = df[date_col].values
        intervals = np.diff(dates).astype("timedelta64[D]").astype(float)
        analysis["interval_stats"] = {
            "mean_days": round(float(np.mean(intervals)), 1),
            "median_days": round(float(np.median(intervals)), 1),
            "std_days": round(float(np.std(intervals)), 1),
            "min_days": round(float(np.min(intervals)), 1),
            "max_days": round(float(np.max(intervals)), 1),
        }

        # 2. Peak detection for cycle identification
        if score_col in df.columns and len(df) >= 5:
            scores = df[score_col].fillna(0).values.astype(float)
            if np.std(scores) > 0:
                peaks, properties = find_peaks(scores, distance=2, prominence=0.5)
                if len(peaks) >= 2:
                    peak_intervals = np.diff(peaks)
                    analysis["cycle_length"] = {
                        "estimated_cycle_days": round(
                            float(np.mean(intervals[peaks[:-1]]) if len(peaks) > 1 else np.mean(intervals)), 1
                        ),
                        "num_cycles_detected": len(peaks),
                        "cycle_regularity": round(1 - (np.std(peak_intervals) / max(np.mean(peak_intervals), 1)), 3)
                    }
                else:
                    analysis["cycle_length"] = {
                        "estimated_cycle_days": analysis["interval_stats"]["mean_days"],
                        "num_cycles_detected": max(len(peaks), 1),
                        "cycle_regularity": 0.0
                    }
            else:
                analysis["cycle_length"] = {
                    "estimated_cycle_days": analysis["interval_stats"]["mean_days"],
                    "num_cycles_detected": 0,
                    "cycle_regularity": 0.0
                }
        else:
            analysis["cycle_length"] = {
                "estimated_cycle_days": analysis["interval_stats"]["mean_days"],
                "num_cycles_detected": 0,
                "cycle_regularity": 0.0
            }

        # 3. Escalation trend
        if score_col in df.columns and len(df) >= 3:
            scores = df[score_col].fillna(0).values.astype(float)
            x = np.arange(len(scores))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, scores)
            analysis["escalation"] = {
                "trend": "ESCALATING" if slope > 0.05 else ("DE-ESCALATING" if slope < -0.05 else "STABLE"),
                "slope": round(float(slope), 4),
                "r_squared": round(float(r_value ** 2), 4),
                "p_value": round(float(p_value), 4),
                "statistically_significant": p_value < 0.05
            }
        else:
            analysis["escalation"] = {"trend": "INSUFFICIENT_DATA"}

        # 4. Day-of-week patterns
        df["dow"] = df[date_col].dt.day_name()
        dow_counts = df["dow"].value_counts().to_dict()
        analysis["day_of_week_pattern"] = dow_counts

        # 5. Monthly patterns
        df["month_name"] = df[date_col].dt.month_name()
        month_counts = df["month_name"].value_counts().to_dict()
        analysis["monthly_pattern"] = month_counts

        # 6. Court date correlation
        if "court_date_proximity" in df.columns:
            prox = df["court_date_proximity"].fillna(0).astype(float)
            if score_col in df.columns:
                scores = df[score_col].fillna(0).astype(float)
                if len(prox) > 2 and prox.std() > 0 and scores.std() > 0:
                    corr, p = stats.pearsonr(prox, scores)
                    analysis["court_date_correlation"] = {
                        "correlation": round(float(corr), 4),
                        "p_value": round(float(p), 4),
                        "significant": p < 0.05
                    }

        # 7. Holiday/special date proximity
        if score_col in df.columns:
            holidays_us = self._get_holiday_proximity(df[date_col])
            if holidays_us is not None:
                df["holiday_proximity"] = holidays_us
                scores = df[score_col].fillna(0).astype(float)
                near_holiday = scores[holidays_us <= 7]
                far_holiday = scores[holidays_us > 7]
                if len(near_holiday) > 0 and len(far_holiday) > 0:
                    analysis["holiday_effect"] = {
                        "avg_severity_near_holiday": round(float(near_holiday.mean()), 2),
                        "avg_severity_far_holiday": round(float(far_holiday.mean()), 2),
                        "holiday_amplification": round(
                            float(near_holiday.mean() / max(far_holiday.mean(), 0.01)), 2
                        )
                    }

        self.pattern_analysis = analysis
        return analysis

    def predict_next_cycle(self, df, date_col="date", score_col="severity_score",
                           forecast_days=90):
        """
        Predict timing and intensity of the next abuse cycle.

        Returns predictions with confidence intervals.
        """
        analysis = self.analyze_cycles(df, date_col, score_col)
        if "error" in analysis:
            return analysis

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        last_date = df[date_col].max()
        cycle_days = analysis["cycle_length"]["estimated_cycle_days"]
        regularity = analysis["cycle_length"].get("cycle_regularity", 0)

        predictions = []
        current_date = last_date

        # Project forward
        num_predictions = max(1, int(forecast_days / max(cycle_days, 1)))
        for i in range(num_predictions):
            next_date = current_date + timedelta(days=cycle_days)

            # Predicted intensity based on trend
            if "escalation" in analysis and "slope" in analysis["escalation"]:
                base_severity = df[score_col].mean() if score_col in df.columns else 5
                slope = analysis["escalation"]["slope"]
                predicted_severity = base_severity + slope * (len(df) + i)
                predicted_severity = max(0, min(10, predicted_severity))
            else:
                predicted_severity = df[score_col].mean() if score_col in df.columns else 5

            # Confidence based on regularity and data volume
            base_confidence = min(0.9, 0.3 + regularity * 0.4 + min(len(df), 20) * 0.015)
            confidence = max(0.1, base_confidence - i * 0.1)

            # Uncertainty window
            interval_std = analysis["interval_stats"].get("std_days", cycle_days * 0.3)
            window_days = max(1, interval_std * (1 + i * 0.2))

            prediction = {
                "predicted_date": next_date.strftime("%Y-%m-%d") if hasattr(next_date, "strftime")
                                  else str(next_date)[:10],
                "earliest_date": (next_date - timedelta(days=window_days)).strftime("%Y-%m-%d")
                                 if hasattr(next_date, "strftime")
                                 else str(next_date - timedelta(days=window_days))[:10],
                "latest_date": (next_date + timedelta(days=window_days)).strftime("%Y-%m-%d")
                               if hasattr(next_date, "strftime")
                               else str(next_date + timedelta(days=window_days))[:10],
                "predicted_severity": round(float(predicted_severity), 2),
                "severity_level": self._severity_label(predicted_severity),
                "confidence": round(float(confidence), 3),
                "window_days": round(float(window_days), 1),
                "cycle_number": i + 1
            }
            predictions.append(prediction)
            current_date = next_date

        self.predictions = predictions
        return {
            "analysis_summary": analysis,
            "predictions": predictions,
            "model_info": {
                "data_points": len(df),
                "date_range": f"{df[date_col].min()} to {df[date_col].max()}",
                "method": "Cycle peak detection with linear trend extrapolation",
                "disclaimer": (
                    "These predictions are statistical projections based on historical "
                    "patterns and should not be used as the sole basis for legal decisions. "
                    "They are intended to supplement professional assessment and safety planning."
                )
            }
        }

    def identify_triggers(self, df, date_col="date", score_col="severity_score"):
        """Identify variables correlated with high-severity incidents."""
        if df.empty or score_col not in df.columns:
            return {}

        df = df.copy()
        scores = df[score_col].fillna(0).astype(float)
        triggers = {}

        # Test correlation of each numeric column with severity
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col == score_col:
                continue
            col_data = df[col].fillna(0).astype(float)
            if col_data.std() > 0 and scores.std() > 0:
                corr, p_value = stats.pearsonr(col_data, scores)
                if abs(corr) > 0.2:
                    triggers[col] = {
                        "correlation": round(float(corr), 4),
                        "p_value": round(float(p_value), 4),
                        "direction": "positive" if corr > 0 else "negative",
                        "strength": "strong" if abs(corr) > 0.6 else
                                    ("moderate" if abs(corr) > 0.4 else "weak")
                    }

        # Test categorical columns
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in categorical_cols:
            if col == score_col or df[col].nunique() > 20:
                continue
            groups = df.groupby(col)[score_col].mean()
            if len(groups) >= 2:
                group_values = [df[df[col] == g][score_col].values for g in groups.index]
                group_values = [g for g in group_values if len(g) > 0]
                if len(group_values) >= 2:
                    try:
                        f_stat, p_value = stats.f_oneway(*group_values)
                        if p_value < 0.1:
                            triggers[col] = {
                                "type": "categorical",
                                "group_means": groups.round(2).to_dict(),
                                "f_statistic": round(float(f_stat), 4),
                                "p_value": round(float(p_value), 4),
                                "highest_risk_value": groups.idxmax()
                            }
                    except Exception:
                        pass

        return dict(sorted(triggers.items(), key=lambda x: abs(
            x[1].get("correlation", 0) if "correlation" in x[1] else x[1].get("f_statistic", 0)
        ), reverse=True))

    def _get_holiday_proximity(self, date_series):
        """Calculate days to nearest major US holiday for each date."""
        try:
            holidays = []
            years = date_series.dt.year.unique()
            for year in years:
                if pd.isna(year):
                    continue
                y = int(year)
                holidays.extend([
                    datetime(y, 1, 1), datetime(y, 2, 14), datetime(y, 5, 12),
                    datetime(y, 6, 16), datetime(y, 7, 4), datetime(y, 9, 1),
                    datetime(y, 10, 31), datetime(y, 11, 28), datetime(y, 12, 25),
                    datetime(y, 12, 31)
                ])

            if not holidays:
                return None

            result = []
            for d in date_series:
                if pd.isna(d):
                    result.append(np.nan)
                else:
                    min_dist = min(abs((d - pd.Timestamp(h)).days) for h in holidays)
                    result.append(min_dist)
            return pd.Series(result, index=date_series.index)
        except Exception:
            return None

    def _severity_label(self, score):
        if score >= 8:
            return "CRITICAL"
        elif score >= 6:
            return "SEVERE"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MODERATE"
        return "LOW"
