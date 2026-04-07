"""
Post-Separation Abuse Classification Engine.

Classifies incidents by type, calculates severity scores, and identifies
abuse patterns using configurable trait matching and weighted scoring.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .config import ABUSE_CATEGORIES


class AbuseClassifier:
    """Classifies and scores post-separation abuse incidents."""

    def __init__(self):
        self.categories = ABUSE_CATEGORIES
        self.classification_log = []

    def classify_incident(self, incident_row):
        """
        Classify a single incident into abuse categories.

        Args:
            incident_row: dict or Series with incident details

        Returns:
            dict with classification results
        """
        matched_categories = []
        total_score = 0
        evidence = []

        text_fields = []
        for key, val in incident_row.items():
            if isinstance(val, str):
                text_fields.append(val.lower())
        combined_text = " ".join(text_fields)

        for cat_id, cat_info in self.categories.items():
            matched_traits = []
            for trait in cat_info["traits"]:
                # Check trait keywords against all text fields
                trait_words = trait.replace("_", " ")
                if trait_words in combined_text or trait in combined_text:
                    matched_traits.append(trait)

                # Also check individual words for broader matching
                for word in trait.split("_"):
                    if len(word) > 3 and word in combined_text:
                        if trait not in matched_traits:
                            matched_traits.append(trait)
                            break

            if matched_traits:
                trait_ratio = len(matched_traits) / len(cat_info["traits"])
                category_score = trait_ratio * cat_info["severity_weight"] * 10
                matched_categories.append({
                    "category_id": cat_id,
                    "category_label": cat_info["label"],
                    "matched_traits": matched_traits,
                    "trait_match_ratio": round(trait_ratio, 3),
                    "category_score": round(category_score, 2),
                    "severity_weight": cat_info["severity_weight"]
                })
                total_score += category_score

        # Sort by score descending
        matched_categories.sort(key=lambda x: x["category_score"], reverse=True)

        primary_type = matched_categories[0]["category_label"] if matched_categories else "Unclassified"
        severity_level = self._score_to_severity(total_score)

        result = {
            "primary_abuse_type": primary_type,
            "all_categories": matched_categories,
            "total_severity_score": round(total_score, 2),
            "severity_level": severity_level,
            "num_categories_matched": len(matched_categories),
        }

        self.classification_log.append(result)
        return result

    def classify_dataframe(self, df):
        """Classify all rows in a dataframe."""
        results = []
        for _, row in df.iterrows():
            result = self.classify_incident(row.to_dict())
            results.append({
                "primary_abuse_type": result["primary_abuse_type"],
                "severity_score": result["total_severity_score"],
                "severity_level": result["severity_level"],
                "categories_matched": result["num_categories_matched"],
                "all_types": "; ".join(c["category_label"] for c in result["all_categories"]),
                "matched_traits": "; ".join(
                    t for c in result["all_categories"] for t in c["matched_traits"]
                )
            })

        result_df = pd.DataFrame(results)
        # Avoid duplicate column names — drop originals that conflict
        df_reset = df.reset_index(drop=True)
        for col in result_df.columns:
            if col in df_reset.columns:
                df_reset = df_reset.drop(columns=[col])
        return pd.concat([df_reset, result_df], axis=1)

    def _score_to_severity(self, score):
        """Convert numeric score to severity level."""
        if score >= 8:
            return "CRITICAL"
        elif score >= 6:
            return "SEVERE"
        elif score >= 4:
            return "HIGH"
        elif score >= 2:
            return "MODERATE"
        elif score > 0:
            return "LOW"
        return "NONE"

    def generate_abuse_formula(self):
        """
        Generate and return the composite abuse severity formula.

        The Composite Abuse Severity Index (CASI) formula:

        CASI = Σ(Wi × Ti × Fi × Ei) × Rm × Cp

        Where:
            Wi = Category severity weight (0-1)
            Ti = Trait match ratio for category i (0-1)
            Fi = Frequency multiplier (incidents/month normalized)
            Ei = Evidence strength factor (0-1)
            Rm = Recency multiplier (exponential decay from most recent)
            Cp = Cumulative pattern factor (escalation trend)
        """
        formula_doc = {
            "name": "Composite Abuse Severity Index (CASI)",
            "formula": "CASI = Σ(Wi × Ti × Fi × Ei) × Rm × Cp",
            "components": {
                "Wi": {
                    "name": "Category Severity Weight",
                    "range": "0.0 - 1.0",
                    "description": "Pre-assigned weight based on abuse category severity",
                    "values": {cat_id: cat["severity_weight"]
                               for cat_id, cat in self.categories.items()}
                },
                "Ti": {
                    "name": "Trait Match Ratio",
                    "range": "0.0 - 1.0",
                    "description": "Proportion of category traits matched in incident"
                },
                "Fi": {
                    "name": "Frequency Multiplier",
                    "range": "0.1 - 5.0",
                    "description": "Normalized frequency of incidents per month. "
                                   "Fi = (incidents_this_month / avg_monthly_incidents)"
                },
                "Ei": {
                    "name": "Evidence Strength Factor",
                    "range": "0.0 - 1.0",
                    "description": "Strength of supporting evidence: "
                                   "0.2=self-report only, 0.4=witness corroboration, "
                                   "0.6=documented communication, 0.8=official record, "
                                   "1.0=court-verified evidence"
                },
                "Rm": {
                    "name": "Recency Multiplier",
                    "range": "0.1 - 2.0",
                    "description": "Exponential decay based on time since incident. "
                                   "Rm = e^(-λ × days_since), λ=0.01"
                },
                "Cp": {
                    "name": "Cumulative Pattern Factor",
                    "range": "0.5 - 3.0",
                    "description": "Measures escalation trend. >1.0 indicates escalation, "
                                   "<1.0 indicates de-escalation. Calculated via linear "
                                   "regression slope of severity over time."
                }
            },
            "interpretation": {
                "0-2": "Low risk - monitoring recommended",
                "2-4": "Moderate risk - safety planning advised",
                "4-6": "High risk - immediate safety measures needed",
                "6-8": "Severe risk - professional intervention required",
                "8+": "Critical risk - emergency protective measures"
            }
        }
        return formula_doc

    def calculate_casi(self, classified_df, date_col="date"):
        """
        Calculate the Composite Abuse Severity Index for the dataset.
        """
        if classified_df.empty:
            return classified_df

        df = classified_df.copy()

        # Ensure date column exists and is datetime
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col])
            df = df.sort_values(date_col)
        else:
            df["casi_score"] = df.get("severity_score", 0)
            return df

        if df.empty:
            return df

        # Fi: Frequency multiplier
        df["month"] = df[date_col].dt.to_period("M")
        monthly_counts = df.groupby("month").size()
        avg_monthly = monthly_counts.mean() if len(monthly_counts) > 0 else 1
        month_freq = monthly_counts.to_dict()
        df["frequency_multiplier"] = df["month"].map(
            lambda m: min(5.0, max(0.1, month_freq.get(m, 1) / max(avg_monthly, 1)))
        )

        # Rm: Recency multiplier
        most_recent = df[date_col].max()
        decay_lambda = 0.01
        df["days_since"] = (most_recent - df[date_col]).dt.days
        df["recency_multiplier"] = np.exp(-decay_lambda * df["days_since"])

        # Cp: Cumulative pattern factor (escalation)
        if len(df) >= 3 and "severity_score" in df.columns:
            scores = df["severity_score"].astype(float).values
            x = np.arange(len(scores), dtype=float)
            if np.std(scores) > 0:
                coeffs = np.polyfit(x, scores, 1)
                slope = float(coeffs[0])
                # Normalize slope to a multiplier
                cp = max(0.5, min(3.0, 1.0 + slope))
            else:
                cp = 1.0
        else:
            cp = 1.0
        df["pattern_factor"] = cp

        # Ei: Evidence strength (default 0.5 if not provided)
        if "evidence_strength" not in df.columns:
            df["evidence_strength"] = 0.5

        # Final CASI calculation
        base_score = df.get("severity_score", pd.Series([0] * len(df)))
        df["casi_score"] = (
            base_score
            * df["frequency_multiplier"]
            * df["evidence_strength"]
            * df["recency_multiplier"]
            * df["pattern_factor"]
        )
        df["casi_score"] = df["casi_score"].round(3)

        # Clean up temp columns
        df = df.drop(columns=["month"], errors="ignore")

        return df
