"""
Scorecard and Rating System Module.

Generates scorecards for judges, court officials, and case outcomes.
Provides predictive scoring based on case setup and participants.
"""

import pandas as pd
import numpy as np
from collections import defaultdict


class OutcomeRatingSystem:
    """
    Predictive rating system for case outcomes based on
    case configuration, participants, and historical patterns.
    """

    # Weights for outcome prediction factors
    FACTOR_WEIGHTS = {
        "case_duration": 0.10,
        "filing_volume": 0.10,
        "judge_history": 0.20,
        "attorney_experience": 0.10,
        "gal_involvement": 0.10,
        "abuse_severity": 0.15,
        "financial_disparity": 0.10,
        "children_involved": 0.05,
        "violation_count": 0.10,
    }

    def __init__(self):
        self.case_scores = {}
        self.official_scorecards = {}

    def score_case_outcome(self, case_data):
        """
        Calculate a predictive outcome score for a case.

        Args:
            case_data: dict with keys matching FACTOR_WEIGHTS

        Returns:
            dict with overall score (0-100), factor breakdown, and interpretation
        """
        scores = {}
        total = 0

        for factor, weight in self.FACTOR_WEIGHTS.items():
            raw = case_data.get(factor, 50)  # default neutral
            if isinstance(raw, (int, float)):
                normalized = max(0, min(100, float(raw)))
            else:
                normalized = 50  # neutral if non-numeric

            weighted = normalized * weight
            scores[factor] = {
                "raw_score": round(normalized, 1),
                "weight": weight,
                "weighted_score": round(weighted, 2),
            }
            total += weighted

        overall = round(total, 1)

        interpretation = self._interpret_outcome_score(overall)

        result = {
            "overall_score": overall,
            "max_possible": 100,
            "interpretation": interpretation,
            "risk_level": self._risk_level(overall),
            "factor_breakdown": scores,
            "recommendations": self._generate_recommendations(scores),
        }

        self.case_scores = result
        return result

    def _interpret_outcome_score(self, score):
        """Interpret the outcome prediction score."""
        if score >= 75:
            return ("HIGH FAVORABILITY — Case factors strongly favor a positive outcome. "
                    "Historical patterns suggest favorable resolution within typical timeframes.")
        elif score >= 60:
            return ("MODERATE-HIGH FAVORABILITY — Most factors are favorable. "
                    "Some areas of concern should be addressed proactively.")
        elif score >= 40:
            return ("NEUTRAL — Case could go either way. Multiple factors pulling "
                    "in different directions. Strategic adjustments recommended.")
        elif score >= 25:
            return ("MODERATE-LOW FAVORABILITY — Several concerning factors present. "
                    "Significant strategic changes may be needed.")
        else:
            return ("LOW FAVORABILITY — Multiple high-risk factors detected. "
                    "Case requires urgent strategic review and possible change of approach.")

    def _risk_level(self, score):
        if score >= 70:
            return "LOW"
        elif score >= 50:
            return "MODERATE"
        elif score >= 30:
            return "HIGH"
        return "CRITICAL"

    def _generate_recommendations(self, scores):
        """Generate actionable recommendations based on factor scores."""
        recs = []
        for factor, data in scores.items():
            if data["raw_score"] < 40:
                rec_map = {
                    "case_duration": "Case is excessively long. File motion for expedited resolution or raise with presiding judge.",
                    "filing_volume": "Excessive filing volume detected. Consider motion for vexatious litigant designation or filing restrictions.",
                    "judge_history": "Judge's historical pattern unfavorable. Consider recusal motion if grounds exist, or appeal strategy.",
                    "attorney_experience": "Attorney effectiveness is a concern. Consider second opinion or change of counsel.",
                    "gal_involvement": "GAL involvement raising concerns. Document issues and consider objection to GAL recommendations.",
                    "abuse_severity": "High abuse severity documented. Ensure all incidents are formally reported and seek protective orders.",
                    "financial_disparity": "Financial disparity disadvantaging case. Seek fee-shifting motions or pro bono assistance.",
                    "children_involved": "Children's welfare at risk. Prioritize child-focused interventions and ensure proper representation.",
                    "violation_count": "Multiple procedural violations found. File formal complaints with judicial conduct commission.",
                }
                recs.append(rec_map.get(factor, f"Address low score in {factor}"))
        return recs


class OfficialScorecard:
    """
    Generates performance and accountability scorecards
    for judges and court officials.
    """

    JUDGE_METRICS = [
        "case_disposition_time",
        "appeal_reversal_rate",
        "recusal_compliance",
        "hearing_timeliness",
        "order_clarity",
        "procedural_compliance",
        "equal_treatment",
        "conflict_of_interest_flags",
        "complaint_history",
        "case_load_management",
    ]

    ATTORNEY_METRICS = [
        "filing_quality",
        "deadline_compliance",
        "motion_success_rate",
        "client_outcome_history",
        "ethical_complaints",
        "billing_transparency",
        "case_duration_impact",
        "opposing_counsel_cooperation",
    ]

    GAL_METRICS = [
        "investigation_thoroughness",
        "recommendation_accuracy",
        "bias_indicators",
        "report_timeliness",
        "child_interview_quality",
        "fee_reasonableness",
        "outcome_correlation",
        "complaint_history",
    ]

    def __init__(self):
        self.scorecards = {}

    def generate_judge_scorecard(self, name, data):
        """
        Generate a scorecard for a judge.

        Args:
            name: Judge's name
            data: dict with available metrics and case history

        Returns:
            Scorecard dict
        """
        scorecard = {
            "name": name,
            "role": "Judge",
            "metrics": {},
            "overall_grade": "",
            "flags": [],
            "summary": "",
        }

        total_score = 0
        scored_metrics = 0

        for metric in self.JUDGE_METRICS:
            value = data.get(metric)
            if value is not None:
                normalized = self._normalize_metric(metric, value)
                scorecard["metrics"][metric] = {
                    "raw_value": value,
                    "score": normalized,
                    "rating": self._letter_grade(normalized),
                }
                total_score += normalized
                scored_metrics += 1

                # Flag concerning values
                if normalized < 40:
                    scorecard["flags"].append(
                        f"LOW SCORE: {metric.replace('_', ' ').title()} = {normalized}/100"
                    )

        # Calculate from case data if raw metrics not available
        if scored_metrics == 0:
            scorecard = self._score_from_case_data(name, "judge", data, scorecard)
            total_score = scorecard.get("_total", 0)
            scored_metrics = scorecard.get("_count", 1)

        avg_score = round(total_score / max(scored_metrics, 1), 1)
        scorecard["overall_score"] = avg_score
        scorecard["overall_grade"] = self._letter_grade(avg_score)
        scorecard["summary"] = self._generate_judge_summary(name, scorecard)

        self.scorecards[name] = scorecard
        return scorecard

    def generate_attorney_scorecard(self, name, data):
        """Generate a scorecard for an attorney."""
        scorecard = {
            "name": name,
            "role": "Attorney",
            "metrics": {},
            "overall_grade": "",
            "flags": [],
            "summary": "",
        }

        total_score = 0
        scored_metrics = 0

        for metric in self.ATTORNEY_METRICS:
            value = data.get(metric)
            if value is not None:
                normalized = self._normalize_metric(metric, value)
                scorecard["metrics"][metric] = {
                    "raw_value": value,
                    "score": normalized,
                    "rating": self._letter_grade(normalized),
                }
                total_score += normalized
                scored_metrics += 1
                if normalized < 40:
                    scorecard["flags"].append(
                        f"LOW SCORE: {metric.replace('_', ' ').title()} = {normalized}/100"
                    )

        if scored_metrics == 0:
            scorecard = self._score_from_case_data(name, "attorney", data, scorecard)
            total_score = scorecard.get("_total", 0)
            scored_metrics = scorecard.get("_count", 1)

        avg_score = round(total_score / max(scored_metrics, 1), 1)
        scorecard["overall_score"] = avg_score
        scorecard["overall_grade"] = self._letter_grade(avg_score)
        scorecard["summary"] = self._generate_official_summary(name, "Attorney", scorecard)

        self.scorecards[name] = scorecard
        return scorecard

    def generate_gal_scorecard(self, name, data):
        """Generate a scorecard for a Guardian ad Litem."""
        scorecard = {
            "name": name,
            "role": "Guardian ad Litem",
            "metrics": {},
            "overall_grade": "",
            "flags": [],
            "summary": "",
        }

        total_score = 0
        scored_metrics = 0

        for metric in self.GAL_METRICS:
            value = data.get(metric)
            if value is not None:
                normalized = self._normalize_metric(metric, value)
                scorecard["metrics"][metric] = {
                    "raw_value": value,
                    "score": normalized,
                    "rating": self._letter_grade(normalized),
                }
                total_score += normalized
                scored_metrics += 1
                if normalized < 40:
                    scorecard["flags"].append(
                        f"LOW SCORE: {metric.replace('_', ' ').title()} = {normalized}/100"
                    )

        if scored_metrics == 0:
            scorecard = self._score_from_case_data(name, "gal", data, scorecard)
            total_score = scorecard.get("_total", 0)
            scored_metrics = scorecard.get("_count", 1)

        avg_score = round(total_score / max(scored_metrics, 1), 1)
        scorecard["overall_score"] = avg_score
        scorecard["overall_grade"] = self._letter_grade(avg_score)
        scorecard["summary"] = self._generate_official_summary(name, "GAL", scorecard)

        self.scorecards[name] = scorecard
        return scorecard

    def _score_from_case_data(self, name, role, data, scorecard):
        """Derive scores from case-level data when raw metrics unavailable."""
        total = 0
        count = 0

        # Total appearances — very high may indicate case dragging
        appearances = data.get("appearances", data.get("total_appearances", 0))
        if appearances:
            # Penalize very high appearance counts (indicates prolonged case)
            app_score = max(10, 100 - appearances * 3)
            scorecard["metrics"]["case_involvement_volume"] = {
                "raw_value": appearances,
                "score": app_score,
                "rating": self._letter_grade(app_score),
            }
            total += app_score
            count += 1

        # Outcomes favorability
        actions = data.get("actions", [])
        if actions:
            denied_count = sum(1 for a in actions
                               if "denied" in str(a.get("outcome", "")).lower() or
                               "dismissed" in str(a.get("outcome", "")).lower())
            granted_count = sum(1 for a in actions
                                if "granted" in str(a.get("outcome", "")).lower() or
                                "approved" in str(a.get("outcome", "")).lower())
            total_outcomes = denied_count + granted_count
            if total_outcomes > 0:
                balance = granted_count / total_outcomes * 100
                scorecard["metrics"]["outcome_balance"] = {
                    "raw_value": f"{granted_count}/{total_outcomes} favorable",
                    "score": round(balance, 1),
                    "rating": self._letter_grade(balance),
                }
                total += balance
                count += 1

        # Estimated earnings — flag excessive
        earnings = data.get("estimated_earnings", 0)
        if earnings:
            earn_score = max(10, 100 - (earnings / 1000) * 2)
            scorecard["metrics"]["cost_to_parties"] = {
                "raw_value": f"${earnings:,.0f}",
                "score": round(earn_score, 1),
                "rating": self._letter_grade(earn_score),
            }
            total += earn_score
            count += 1
            if earnings > 20000:
                scorecard["flags"].append(
                    f"HIGH COST: Estimated ${earnings:,.0f} earned from this case"
                )

        scorecard["_total"] = total
        scorecard["_count"] = count
        return scorecard

    def generate_all_scorecards(self, officials_registry, earnings_data=None):
        """Generate scorecards for all registered officials."""
        results = {}
        for name, info in officials_registry.items():
            role = info.get("role", "").lower()
            data = {**info}
            if earnings_data and name in earnings_data:
                data.update(earnings_data[name])

            if "judge" in role or "magistrate" in role:
                results[name] = self.generate_judge_scorecard(name, data)
            elif "attorney" in role:
                results[name] = self.generate_attorney_scorecard(name, data)
            elif "gal" in role or "guardian" in role:
                results[name] = self.generate_gal_scorecard(name, data)
            else:
                results[name] = self.generate_attorney_scorecard(name, data)

        return results

    def get_scorecards_dataframe(self):
        """Return all scorecards as a DataFrame for reporting."""
        rows = []
        for name, card in self.scorecards.items():
            row = {
                "name": name,
                "role": card.get("role", ""),
                "overall_score": card.get("overall_score", 0),
                "overall_grade": card.get("overall_grade", ""),
                "flags_count": len(card.get("flags", [])),
                "flags": "; ".join(card.get("flags", [])),
                "summary": card.get("summary", ""),
            }
            # Add individual metrics
            for metric, values in card.get("metrics", {}).items():
                row[f"metric_{metric}"] = values.get("score", "")
            rows.append(row)

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("overall_score", ascending=True)
        return df

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _normalize_metric(self, metric, value):
        """Normalize a metric value to 0-100 scale."""
        if isinstance(value, (int, float)):
            return max(0, min(100, float(value)))
        if isinstance(value, str):
            # Boolean-like
            if value.lower() in ("yes", "true", "good", "compliant"):
                return 80
            if value.lower() in ("no", "false", "bad", "non-compliant"):
                return 20
            if value.lower() in ("partial", "some", "moderate"):
                return 50
        return 50

    def _letter_grade(self, score):
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"

    def _generate_judge_summary(self, name, scorecard):
        score = scorecard.get("overall_score", 0)
        grade = scorecard.get("overall_grade", "N/A")
        flags = scorecard.get("flags", [])

        summary = f"Judge {name} — Overall Grade: {grade} ({score}/100). "
        if flags:
            summary += f"{len(flags)} concern(s) flagged: {'; '.join(flags[:3])}. "
        if score < 50:
            summary += ("Performance indicators suggest potential issues with judicial conduct "
                        "that may warrant formal review or complaint filing.")
        elif score < 70:
            summary += "Mixed performance indicators. Some areas require monitoring."
        else:
            summary += "Performance indicators are within acceptable ranges."
        return summary

    def _generate_official_summary(self, name, role, scorecard):
        score = scorecard.get("overall_score", 0)
        grade = scorecard.get("overall_grade", "N/A")
        flags = scorecard.get("flags", [])

        summary = f"{role} {name} — Overall Grade: {grade} ({score}/100). "
        if flags:
            summary += f"{len(flags)} concern(s) flagged. "
        if score < 50:
            summary += f"Performance indicators suggest {role.lower()} involvement may be adversely affecting case outcomes."
        return summary
