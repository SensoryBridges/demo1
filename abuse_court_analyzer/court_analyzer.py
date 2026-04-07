"""
Court Case Analysis Module.

Analyzes court filings, identifies patterns in judicial behavior,
tracks officials, calculates costs, and detects procedural violations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from .config import (
    COURT_ROLES, RIGHTS_CATEGORIES,
    SC_FAMILY_COURT_RULES, FRAUD_INDICATORS, DISMISSAL_GROUNDS,
)


# ============================================================================
# State-specific rules of procedure (extensible registry)
# ============================================================================

STATE_LAWS = {
    # Format: "STATE_CODE": { "category": [ {"law": ..., "description": ..., "citation": ...} ] }
    # Populated dynamically or via configuration file
    "_default": {
        "due_process": [
            {"law": "14th Amendment Due Process",
             "description": "Right to notice and opportunity to be heard",
             "citation": "U.S. Const. amend. XIV"},
            {"law": "Right to Timely Resolution",
             "description": "Cases must be resolved within reasonable timeframes",
             "citation": "Varies by state"},
        ],
        "equal_protection": [
            {"law": "14th Amendment Equal Protection",
             "description": "Equal treatment under the law",
             "citation": "U.S. Const. amend. XIV"},
        ],
        "parental_rights": [
            {"law": "Fundamental Right to Parent",
             "description": "Parents have a fundamental right to the care and custody of children",
             "citation": "Troxel v. Granville, 530 U.S. 57 (2000)"},
        ],
        "right_to_counsel": [
            {"law": "Right to Counsel in Custody",
             "description": "Right to legal representation in custody matters",
             "citation": "Varies by state"},
        ],
        "vexatious_litigation": [
            {"law": "Vexatious Litigation Sanctions",
             "description": "Courts may sanction parties filing frivolous motions",
             "citation": "28 U.S.C. § 1927; state equivalents"},
        ],
        "judicial_conduct": [
            {"law": "Code of Judicial Conduct",
             "description": "Judges must be impartial and avoid conflicts of interest",
             "citation": "ABA Model Code of Judicial Conduct"},
            {"law": "Judicial Disqualification",
             "description": "Judges must recuse when impartiality may be questioned",
             "citation": "28 U.S.C. § 455; state equivalents"},
        ],
    }
}


class CourtAnalyzer:
    """Analyzes court case patterns, officials, costs, and procedural violations."""

    def __init__(self, state_code=None, county=None):
        self.state_code = state_code
        self.county = county
        self.laws = STATE_LAWS.get(state_code, STATE_LAWS["_default"])
        self.officials_registry = {}
        self.filings_data = None
        self.case_timeline = []
        # SC-specific config references
        self.sc_family_court_rules = SC_FAMILY_COURT_RULES
        self.fraud_indicators = FRAUD_INDICATORS
        self.dismissal_grounds = DISMISSAL_GROUNDS
        self.sc_custody_factors = SC_FAMILY_COURT_RULES.get("best_interest", {}).get("factors", [])
        self.analysis_start_date = datetime(2022, 3, 11)

    # ------------------------------------------------------------------
    # Official tracking
    # ------------------------------------------------------------------

    def register_officials(self, officials_df=None, officials_list=None):
        """Register court officials from data or manual list."""
        if officials_df is not None:
            for _, row in officials_df.iterrows():
                name = str(row.get("name", row.get("official", "Unknown")))
                role = str(row.get("role", row.get("position", "unknown")))
                self.officials_registry[name] = {
                    "role": role,
                    "appearances": 0,
                    "actions": [],
                    "filings_involved": 0,
                    "background": {k: row.get(k, "") for k in row.index
                                   if k not in ("name", "role", "official", "position")},
                }
        if officials_list:
            for item in officials_list:
                if isinstance(item, dict):
                    name = item.get("name", "Unknown")
                    self.officials_registry[name] = {
                        "role": item.get("role", "unknown"),
                        "appearances": 0,
                        "actions": [],
                        "filings_involved": 0,
                        "background": item,
                    }

    def track_official_activity(self, filings_df, name_columns=None):
        """
        Scan filings data to count appearances and actions per official.
        """
        if name_columns is None:
            name_columns = ["judge", "attorney", "guardian_ad_litem", "gal",
                            "magistrate", "mediator", "filed_by", "assigned_to",
                            "ruling_by", "official"]

        existing_cols = [c for c in name_columns if c in filings_df.columns]
        if not existing_cols:
            return self.officials_registry

        for _, row in filings_df.iterrows():
            for col in existing_cols:
                name = str(row.get(col, "")).strip()
                if not name or name == "nan" or name == "":
                    continue

                if name not in self.officials_registry:
                    self.officials_registry[name] = {
                        "role": col,
                        "appearances": 0,
                        "actions": [],
                        "filings_involved": 0,
                        "background": {},
                    }

                self.officials_registry[name]["appearances"] += 1
                self.officials_registry[name]["filings_involved"] += 1

                action = row.get("action", row.get("type", row.get("filing_type", "")))
                date = row.get("date", row.get("filing_date", ""))
                outcome = row.get("outcome", row.get("ruling", row.get("result", "")))
                self.officials_registry[name]["actions"].append({
                    "date": str(date),
                    "action": str(action),
                    "outcome": str(outcome),
                })

        return self.officials_registry

    def get_officials_summary(self):
        """Return a summary DataFrame of all tracked officials."""
        rows = []
        for name, info in self.officials_registry.items():
            rows.append({
                "name": name,
                "role": info["role"],
                "total_appearances": info["appearances"],
                "total_filings_involved": info["filings_involved"],
                "num_actions": len(info["actions"]),
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("total_appearances", ascending=False)
        return df

    # ------------------------------------------------------------------
    # Case duration and timeline
    # ------------------------------------------------------------------

    def analyze_case_duration(self, filings_df, date_col="date"):
        """Analyze how long the case has been going on."""
        if date_col not in filings_df.columns:
            return {"error": f"No '{date_col}' column found"}

        dates = pd.to_datetime(filings_df[date_col], errors="coerce").dropna()
        if dates.empty:
            return {"error": "No valid dates found"}

        first = dates.min()
        last = dates.max()
        duration = last - first

        return {
            "case_start": str(first.date()),
            "most_recent_filing": str(last.date()),
            "duration_days": duration.days,
            "duration_months": round(duration.days / 30.44, 1),
            "duration_years": round(duration.days / 365.25, 2),
            "total_filings": len(filings_df),
            "filings_per_month": round(len(filings_df) / max(duration.days / 30.44, 1), 2),
        }

    def build_timeline(self, filings_df, date_col="date"):
        """Build a chronological case timeline."""
        if date_col not in filings_df.columns:
            return []

        df = filings_df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col)

        timeline = []
        for _, row in df.iterrows():
            entry = {
                "date": str(row[date_col].date()) if hasattr(row[date_col], "date") else str(row[date_col]),
                "type": str(row.get("type", row.get("filing_type", row.get("action", "")))),
                "description": str(row.get("description", row.get("details", row.get("notes", "")))),
                "filed_by": str(row.get("filed_by", row.get("party", ""))),
                "outcome": str(row.get("outcome", row.get("ruling", row.get("result", "")))),
            }
            timeline.append(entry)

        self.case_timeline = timeline
        return timeline

    # ------------------------------------------------------------------
    # Filing pattern analysis
    # ------------------------------------------------------------------

    def analyze_filing_patterns(self, filings_df, date_col="date"):
        """Identify patterns in court filings."""
        if filings_df.empty:
            return {}

        analysis = {}

        # Filing types frequency
        type_col = None
        for candidate in ["type", "filing_type", "action", "motion_type"]:
            if candidate in filings_df.columns:
                type_col = candidate
                break

        if type_col:
            type_counts = filings_df[type_col].value_counts().to_dict()
            analysis["filing_type_distribution"] = type_counts
            analysis["most_common_filing"] = filings_df[type_col].mode().iloc[0] if not filings_df[type_col].mode().empty else "N/A"

        # Party filing frequency
        party_col = None
        for candidate in ["filed_by", "party", "filer", "petitioner_respondent"]:
            if candidate in filings_df.columns:
                party_col = candidate
                break

        if party_col:
            party_counts = filings_df[party_col].value_counts().to_dict()
            analysis["filings_by_party"] = party_counts

        # Time-based patterns
        if date_col in filings_df.columns:
            dates = pd.to_datetime(filings_df[date_col], errors="coerce")
            dates = dates.dropna()
            if not dates.empty:
                analysis["filings_by_year"] = dates.dt.year.value_counts().sort_index().to_dict()
                analysis["filings_by_month"] = dates.dt.month_name().value_counts().to_dict()

                # Bursts — periods of high filing activity
                intervals = dates.sort_values().diff().dt.days.dropna()
                if len(intervals) > 0:
                    analysis["avg_days_between_filings"] = round(float(intervals.mean()), 1)
                    analysis["min_days_between_filings"] = int(intervals.min())
                    # Burst detection: filings less than 7 days apart
                    burst_count = (intervals < 7).sum()
                    analysis["rapid_filings_count"] = int(burst_count)
                    analysis["rapid_filing_ratio"] = round(float(burst_count / len(intervals)), 3)

        return analysis

    # ------------------------------------------------------------------
    # Procedural violation detection
    # ------------------------------------------------------------------

    def detect_procedural_violations(self, filings_df, date_col="date"):
        """
        Scan filings for potential procedural violations.
        Returns identified violations with relevant law citations.
        """
        violations = []

        # 1. Excessive case duration
        duration = self.analyze_case_duration(filings_df, date_col)
        if isinstance(duration, dict) and "duration_years" in duration:
            if duration["duration_years"] > 2:
                violations.append({
                    "type": "EXCESSIVE_DURATION",
                    "description": f"Case has been ongoing for {duration['duration_years']} years "
                                   f"({duration['duration_days']} days)",
                    "law": "Right to Timely Resolution",
                    "citation": self._get_citation("due_process"),
                    "severity": "HIGH" if duration["duration_years"] > 3 else "MODERATE",
                })

        # 2. Excessive filings (potential vexatious litigation)
        patterns = self.analyze_filing_patterns(filings_df, date_col)
        if patterns.get("rapid_filing_ratio", 0) > 0.3:
            violations.append({
                "type": "EXCESSIVE_RAPID_FILINGS",
                "description": f"{patterns.get('rapid_filings_count', 0)} filings made within "
                               f"7 days of prior filings ({patterns['rapid_filing_ratio']:.0%} of all filings)",
                "law": "Vexatious Litigation Sanctions",
                "citation": self._get_citation("vexatious_litigation"),
                "severity": "HIGH",
            })

        # 3. Detect repeated denied motions (same type filed multiple times)
        type_col = None
        outcome_col = None
        for c in ["type", "filing_type", "action", "motion_type"]:
            if c in filings_df.columns:
                type_col = c
                break
        for c in ["outcome", "ruling", "result", "decision"]:
            if c in filings_df.columns:
                outcome_col = c
                break

        if type_col and outcome_col:
            for filing_type in filings_df[type_col].dropna().unique():
                subset = filings_df[filings_df[type_col] == filing_type]
                denied = subset[subset[outcome_col].astype(str).str.lower().str.contains(
                    "denied|dismissed|overruled", na=False
                )]
                if len(denied) >= 3:
                    violations.append({
                        "type": "REPEATED_DENIED_FILINGS",
                        "description": f"'{filing_type}' has been denied/dismissed {len(denied)} times",
                        "law": "Vexatious Litigation / Abuse of Process",
                        "citation": self._get_citation("vexatious_litigation"),
                        "severity": "HIGH",
                    })

        # 4. Look for text indicators in descriptions/notes
        text_cols = [c for c in filings_df.columns
                     if c in ("description", "details", "notes", "text", "document_text")]
        violation_keywords = {
            "ex_parte": ("Ex Parte Communication", "judicial_conduct"),
            "no notice": ("Failure to Provide Notice", "due_process"),
            "denied counsel": ("Denial of Right to Counsel", "right_to_counsel"),
            "conflict of interest": ("Judicial Conflict of Interest", "judicial_conduct"),
            "bias": ("Judicial Bias Indicators", "judicial_conduct"),
            "not heard": ("Denial of Right to Be Heard", "due_process"),
            "without hearing": ("Action Without Hearing", "due_process"),
        }

        for _, row in filings_df.iterrows():
            combined_text = " ".join(
                str(row.get(c, "")).lower() for c in text_cols
            )
            for keyword, (desc, law_cat) in violation_keywords.items():
                if keyword in combined_text:
                    violations.append({
                        "type": "TEXT_INDICATOR",
                        "description": f"{desc} detected in filing on {row.get(date_col, 'unknown date')}",
                        "law": desc,
                        "citation": self._get_citation(law_cat),
                        "severity": "MODERATE",
                        "source_text_snippet": combined_text[:200],
                    })

        return violations

    # ------------------------------------------------------------------
    # Financial analysis
    # ------------------------------------------------------------------

    def analyze_costs(self, financial_df=None, filings_df=None):
        """
        Calculate estimated and actual costs per party, per official,
        and per filing outcome.
        """
        results = {
            "per_party": {},
            "per_outcome": {},
            "per_official": {},
            "total_estimated": 0,
        }

        # If we have actual financial data
        if financial_df is not None and not financial_df.empty:
            amount_col = None
            for c in ["amount", "cost", "fee", "payment", "total"]:
                if c in financial_df.columns:
                    amount_col = c
                    break

            if amount_col:
                financial_df[amount_col] = pd.to_numeric(financial_df[amount_col], errors="coerce")

                # By party
                party_col = None
                for c in ["party", "paid_by", "billed_to", "name"]:
                    if c in financial_df.columns:
                        party_col = c
                        break
                if party_col:
                    results["per_party"] = financial_df.groupby(party_col)[amount_col].sum().to_dict()

                # By official/payee
                payee_col = None
                for c in ["payee", "paid_to", "provider", "attorney", "official"]:
                    if c in financial_df.columns:
                        payee_col = c
                        break
                if payee_col:
                    results["per_official"] = financial_df.groupby(payee_col)[amount_col].sum().to_dict()

                results["total_actual"] = float(financial_df[amount_col].sum())

        # Estimate from filings if no financial data
        if filings_df is not None and not filings_df.empty:
            # Rough estimates per filing type (conservative)
            filing_cost_estimates = {
                "motion": 500, "response": 400, "hearing": 1500,
                "trial": 5000, "deposition": 2000, "mediation": 1500,
                "evaluation": 3000, "appeal": 5000, "emergency": 2000,
                "contempt": 1000, "modification": 800, "discovery": 1000,
            }

            type_col = None
            for c in ["type", "filing_type", "action"]:
                if c in filings_df.columns:
                    type_col = c
                    break

            estimated_total = 0
            if type_col:
                for _, row in filings_df.iterrows():
                    ftype = str(row.get(type_col, "")).lower()
                    for keyword, cost in filing_cost_estimates.items():
                        if keyword in ftype:
                            estimated_total += cost
                            break
                    else:
                        estimated_total += 500  # default per filing

            results["total_estimated"] = estimated_total
            results["estimated_per_filing"] = round(
                estimated_total / max(len(filings_df), 1), 2
            )

        return results

    def calculate_official_earnings(self, financial_df=None, filings_df=None):
        """
        Estimate earnings of each court official from the case.
        """
        earnings = {}

        for name, info in self.officials_registry.items():
            role = info["role"]
            appearances = info["appearances"]

            # Role-based hourly estimates
            hourly_rates = {
                "judge": 0,  # Judges are salaried — tracked separately
                "attorney": 350,
                "attorney_petitioner": 350,
                "attorney_respondent": 350,
                "guardian_ad_litem": 250,
                "gal": 250,
                "mediator": 300,
                "custody_evaluator": 275,
                "therapist_court_appointed": 200,
                "parenting_coordinator": 225,
                "special_master": 300,
            }

            rate = hourly_rates.get(role.lower(), 250)
            # Estimate 2-4 hours per appearance
            hours_per_appearance = 3
            estimated_earnings = rate * hours_per_appearance * appearances

            earnings[name] = {
                "role": role,
                "appearances": appearances,
                "estimated_hourly_rate": rate,
                "estimated_hours": hours_per_appearance * appearances,
                "estimated_earnings": estimated_earnings,
            }

        return earnings

    # ------------------------------------------------------------------
    # Appeals analysis
    # ------------------------------------------------------------------

    def analyze_appeals(self, appeals_df=None, filings_df=None):
        """Analyze appeals patterns for judges and outcomes."""
        if appeals_df is not None and not appeals_df.empty:
            df = appeals_df
        elif filings_df is not None:
            # Filter filings for appeal-related entries
            type_col = None
            for c in ["type", "filing_type", "action"]:
                if c in filings_df.columns:
                    type_col = c
                    break
            if type_col:
                mask = filings_df[type_col].astype(str).str.lower().str.contains(
                    "appeal|appellate|remand|reversal", na=False
                )
                df = filings_df[mask]
            else:
                return {"error": "No appeal data found"}
        else:
            return {"error": "No data provided"}

        if df.empty:
            return {"total_appeals": 0}

        analysis = {
            "total_appeals": len(df),
        }

        # By judge
        judge_col = None
        for c in ["judge", "ruling_by", "original_judge", "assigned_to"]:
            if c in df.columns:
                judge_col = c
                break
        if judge_col:
            analysis["appeals_by_judge"] = df[judge_col].value_counts().to_dict()

        # By outcome
        outcome_col = None
        for c in ["outcome", "result", "ruling", "appeal_result"]:
            if c in df.columns:
                outcome_col = c
                break
        if outcome_col:
            analysis["appeal_outcomes"] = df[outcome_col].value_counts().to_dict()

        # By year
        date_col = None
        for c in ["date", "filing_date", "appeal_date"]:
            if c in df.columns:
                date_col = c
                break
        if date_col:
            dates = pd.to_datetime(df[date_col], errors="coerce")
            if not dates.dropna().empty:
                analysis["appeals_by_year"] = dates.dt.year.value_counts().sort_index().to_dict()

        return analysis

    # ------------------------------------------------------------------
    # Outcome prediction
    # ------------------------------------------------------------------

    def predict_outcomes(self, filings_df, date_col="date"):
        """
        Project likely outcomes and timing based on case patterns.
        """
        duration = self.analyze_case_duration(filings_df, date_col)
        patterns = self.analyze_filing_patterns(filings_df, date_col)

        if "error" in duration:
            return {"error": "Insufficient data for prediction"}

        # Filing rate trend
        if date_col in filings_df.columns:
            dates = pd.to_datetime(filings_df[date_col], errors="coerce").dropna().sort_values()
            if len(dates) >= 5:
                # Split into halves and compare rates
                mid = len(dates) // 2
                first_half_rate = mid / max((dates.iloc[mid] - dates.iloc[0]).days, 1)
                second_half_rate = (len(dates) - mid) / max((dates.iloc[-1] - dates.iloc[mid]).days, 1)
                rate_change = second_half_rate / max(first_half_rate, 0.001)
            else:
                rate_change = 1.0
        else:
            rate_change = 1.0

        # Projected resolution
        avg_interval = patterns.get("avg_days_between_filings", 30)
        current_rate = patterns.get("filings_per_month", duration.get("filings_per_month", 1))

        if rate_change < 0.7:
            projected_months = max(3, int(6 / max(rate_change, 0.1)))
            trajectory = "DECELERATING — case may be winding down"
        elif rate_change > 1.3:
            projected_months = max(6, int(12 * rate_change))
            trajectory = "ACCELERATING — case activity increasing"
        else:
            projected_months = max(6, int(duration.get("duration_months", 12) * 0.3))
            trajectory = "STEADY — case continuing at current pace"

        # Outcome probabilities based on filing patterns
        outcome_col = None
        for c in ["outcome", "ruling", "result"]:
            if c in filings_df.columns:
                outcome_col = c
                break

        outcome_distribution = {}
        if outcome_col:
            outcomes = filings_df[outcome_col].dropna().astype(str).str.lower()
            total = len(outcomes)
            if total > 0:
                for outcome in outcomes.unique():
                    count = (outcomes == outcome).sum()
                    outcome_distribution[outcome] = round(count / total, 3)

        return {
            "case_duration": duration,
            "filing_rate_trend": round(float(rate_change), 3),
            "trajectory": trajectory,
            "projected_additional_months": projected_months,
            "projected_end_date": str(
                (datetime.now() + timedelta(days=projected_months * 30)).date()
            ),
            "current_filing_rate_per_month": round(float(current_rate), 2),
            "historical_outcome_distribution": outcome_distribution,
            "disclaimer": (
                "Predictions are statistical projections and do not constitute legal advice. "
                "Actual outcomes depend on judicial discretion, legal arguments, and evidence."
            ),
        }

    # ------------------------------------------------------------------
    # Connection analysis
    # ------------------------------------------------------------------

    def analyze_connections(self, officials_data=None):
        """
        Analyze connections between court officials based on available data.
        Looks for shared affiliations, firms, schools, repeated co-appearances.
        """
        connections = []

        # Co-appearance analysis from tracked actions
        officials = list(self.officials_registry.keys())
        for i, name1 in enumerate(officials):
            for name2 in officials[i + 1:]:
                info1 = self.officials_registry[name1]
                info2 = self.officials_registry[name2]

                # Check date overlap in actions
                dates1 = set(a["date"] for a in info1["actions"])
                dates2 = set(a["date"] for a in info2["actions"])
                shared_dates = dates1 & dates2
                if shared_dates:
                    connections.append({
                        "person_1": name1,
                        "role_1": info1["role"],
                        "person_2": name2,
                        "role_2": info2["role"],
                        "connection_type": "CO_APPEARANCE",
                        "strength": len(shared_dates),
                        "details": f"Appeared on same {len(shared_dates)} dates",
                    })

        # Background-based connections (if background data provided)
        if officials_data is not None and not officials_data.empty:
            connection_fields = ["law_firm", "firm", "school", "university",
                                 "college", "bar_association", "club",
                                 "organization", "association"]

            for field in connection_fields:
                if field not in officials_data.columns:
                    continue

                groups = defaultdict(list)
                for _, row in officials_data.iterrows():
                    val = str(row.get(field, "")).strip()
                    if val and val.lower() not in ("", "nan", "none", "n/a"):
                        groups[val.lower()].append({
                            "name": str(row.get("name", row.get("official", "Unknown"))),
                            "role": str(row.get("role", row.get("position", "")))
                        })

                for affiliation, members in groups.items():
                    if len(members) >= 2:
                        for i, m1 in enumerate(members):
                            for m2 in members[i + 1:]:
                                connections.append({
                                    "person_1": m1["name"],
                                    "role_1": m1["role"],
                                    "person_2": m2["name"],
                                    "role_2": m2["role"],
                                    "connection_type": f"SHARED_{field.upper()}",
                                    "strength": 1,
                                    "details": f"Both affiliated with: {affiliation}",
                                })

        return connections

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_citation(self, law_category):
        """Look up a citation for a law category."""
        laws = self.laws.get(law_category, [])
        if laws:
            return laws[0].get("citation", "See state statutes")
        return "See applicable state statutes and rules of procedure"

    def get_children_analysis(self, cases_df):
        """Analyze cases by number of children involved."""
        child_col = None
        for c in ["children", "num_children", "children_count", "minors"]:
            if c in cases_df.columns:
                child_col = c
                break
        if not child_col:
            return {"error": "No children count column found"}

        cases_df[child_col] = pd.to_numeric(cases_df[child_col], errors="coerce")
        return {
            "total_children": int(cases_df[child_col].sum()),
            "avg_children_per_case": round(float(cases_df[child_col].mean()), 1),
            "distribution": cases_df[child_col].value_counts().sort_index().to_dict(),
        }

    # ------------------------------------------------------------------
    # Text extraction helper
    # ------------------------------------------------------------------

    def _get_text_blob(self, row):
        """Join all text-like columns in a row into a single lowercase string."""
        text_cols = ["description", "details", "notes", "text", "document_text",
                     "type", "filing_type", "action", "outcome", "ruling",
                     "result", "violation", "category", "subcategory"]
        parts = []
        for c in text_cols:
            val = str(row.get(c, ""))
            if val and val.lower() not in ("nan", "none", ""):
                parts.append(val)
        return " ".join(parts).lower()

    # ------------------------------------------------------------------
    # Rule 11 Violation Detection
    # ------------------------------------------------------------------

    def detect_rule_11_violations(self, filings_df, detailed_hearings_df=None,
                                  violations_df=None):
        """
        Detect SCRCP Rule 11 violations in court filings.

        Rule 11 requires that every pleading, motion, and other paper be:
        1. Well grounded in fact
        2. Warranted by existing law or good faith argument for change
        3. Not interposed for any improper purpose (harassment, delay, cost)

        Returns a list of detected violations with citations and evidence.
        """
        rule_11 = self.sc_family_court_rules.get("rule_11", {})
        violations = []

        # Combine all available data sources
        all_dfs = [filings_df]
        if detailed_hearings_df is not None and not detailed_hearings_df.empty:
            all_dfs.append(detailed_hearings_df)
        if violations_df is not None and not violations_df.empty:
            all_dfs.append(violations_df)

        combined = pd.concat(all_dfs, ignore_index=True, sort=False)

        # --- 1. Improper purpose: harassment ---
        harassment_keywords = ["harass", "intimidat", "threaten", "coerce",
                               "bully", "stalk", "retali", "punish", "spite"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in harassment_keywords if kw in text]
            if matched:
                violations.append({
                    "rule": "SCRCP Rule 11",
                    "sub_rule": "Rule 11 - Improper Purpose (Harassment)",
                    "requirement_violated": "not_for_improper_purpose",
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Filing appears motivated by harassment: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "citation": rule_11.get("citation", "SCRCP Rule 11"),
                    "sanctions_available": "Attorney fees, costs, disciplinary referral",
                    "dismissal_support": True,
                })

        # --- 2. Improper purpose: delay ---
        delay_keywords = ["delay", "continu", "postpone", "extend time",
                          "stall", "drag out", "prolong", "slow down"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in delay_keywords if kw in text]
            if matched:
                violations.append({
                    "rule": "SCRCP Rule 11",
                    "sub_rule": "Rule 11 - Improper Purpose (Delay)",
                    "requirement_violated": "not_for_improper_purpose",
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Filing appears designed to cause delay: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "MODERATE",
                    "citation": rule_11.get("citation", "SCRCP Rule 11"),
                    "sanctions_available": "Attorney fees, costs",
                    "dismissal_support": True,
                })

        # --- 3. Improper purpose: needless increase in cost ---
        cost_keywords = ["frivolous", "vexatious", "needless cost",
                         "waste", "bad faith", "groundless", "meritless",
                         "no basis", "without merit", "unsupported"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in cost_keywords if kw in text]
            if matched:
                violations.append({
                    "rule": "SCRCP Rule 11",
                    "sub_rule": "Rule 11 - Improper Purpose (Needless Cost)",
                    "requirement_violated": "not_for_improper_purpose",
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Filing imposes needless costs: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "citation": rule_11.get("citation", "SCRCP Rule 11"),
                    "sanctions_available": "Attorney fees, costs, sanctions",
                    "dismissal_support": True,
                })

        # --- 4. Not well grounded in fact ---
        fact_keywords = ["false", "untrue", "fabricat", "lie", "lied",
                         "perjur", "misstat", "inaccurat", "not true",
                         "false statement", "misrepresent"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in fact_keywords if kw in text]
            if matched:
                violations.append({
                    "rule": "SCRCP Rule 11",
                    "sub_rule": "Rule 11 - Not Well Grounded in Fact",
                    "requirement_violated": "well_grounded_in_fact",
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Filing not well grounded in fact: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "CRITICAL",
                    "citation": rule_11.get("citation", "SCRCP Rule 11"),
                    "sanctions_available": "Sanctions, attorney fees, contempt, perjury referral",
                    "dismissal_support": True,
                })

        # --- 5. Repeated denied motions (pattern of frivolous filings) ---
        type_col = None
        outcome_col = None
        for c in ["type", "filing_type", "action", "motion_type"]:
            if c in filings_df.columns:
                type_col = c
                break
        for c in ["outcome", "ruling", "result", "decision"]:
            if c in filings_df.columns:
                outcome_col = c
                break

        if type_col and outcome_col:
            for filing_type in filings_df[type_col].dropna().unique():
                subset = filings_df[filings_df[type_col] == filing_type]
                denied = subset[subset[outcome_col].astype(str).str.lower().str.contains(
                    "denied|dismissed|overruled|rejected", na=False
                )]
                if len(denied) >= 2:
                    violations.append({
                        "rule": "SCRCP Rule 11",
                        "sub_rule": "Rule 11 - Pattern of Frivolous Filings",
                        "requirement_violated": "warranted_by_existing_law",
                        "date": "Multiple dates",
                        "description": (
                            f"'{filing_type}' filed {len(subset)} times, "
                            f"denied/dismissed {len(denied)} times — "
                            f"pattern suggests not warranted by law"
                        ),
                        "evidence": f"Denied dates: {', '.join(denied.get('date', denied.get('filing_date', pd.Series())).astype(str).tolist()[:5])}",
                        "severity": "HIGH",
                        "citation": rule_11.get("citation", "SCRCP Rule 11"),
                        "sanctions_available": "Sanctions under Rule 11; 28 USC 1927",
                        "dismissal_support": True,
                    })

        # --- 6. Check fraud indicators from config ---
        for indicator_name, indicator_data in self.fraud_indicators.items():
            keywords = indicator_data.get("keywords", [])
            for idx, row in combined.iterrows():
                text = self._get_text_blob(row)
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    violations.append({
                        "rule": "SCRCP Rule 11",
                        "sub_rule": f"Rule 11 / {indicator_data.get('rule_citation', '')}",
                        "requirement_violated": "well_grounded_in_fact",
                        "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                        "description": f"Fraud indicator '{indicator_name}': "
                                       f"keywords [{', '.join(matched)}] found",
                        "evidence": text[:300],
                        "severity": indicator_data.get("severity", "HIGH"),
                        "citation": indicator_data.get("rule_citation", "SCRCP Rule 11"),
                        "sanctions_available": "Rule 11 sanctions; potential criminal referral",
                        "dismissal_support": True,
                    })

        # Deduplicate by (date, sub_rule, evidence[:50])
        seen = set()
        unique_violations = []
        for v in violations:
            key = (v["date"], v["sub_rule"], v["evidence"][:50])
            if key not in seen:
                seen.add(key)
                unique_violations.append(v)

        return unique_violations

    # ------------------------------------------------------------------
    # Rule 12 Dismissal Grounds Detection
    # ------------------------------------------------------------------

    def detect_rule_12_dismissal_grounds(self, filings_df, addresses_df=None,
                                          detailed_hearings_df=None):
        """
        Detect grounds for dismissal under SCRCP Rule 12(b)(1)-(6).

        Analyzes filings for:
        - 12(b)(1): Lack of subject matter jurisdiction
        - 12(b)(2): Lack of personal jurisdiction
        - 12(b)(3): Improper venue
        - 12(b)(4): Insufficiency of process
        - 12(b)(5): Insufficiency of service of process
        - 12(b)(6): Failure to state a claim

        Returns list of identified grounds with supporting evidence.
        """
        rule_12 = self.sc_family_court_rules.get("rule_12", {})
        subsections = rule_12.get("subsections", {})
        grounds = []

        # Combine data
        all_dfs = [filings_df]
        if detailed_hearings_df is not None and not detailed_hearings_df.empty:
            all_dfs.append(detailed_hearings_df)
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)

        # --- 12(b)(1): Lack of subject matter jurisdiction ---
        jurisdiction_keywords = ["jurisdiction", "no jurisdiction", "lack jurisdiction",
                                 "subject matter", "uccjea", "home state",
                                 "not home state", "wrong court", "improper court",
                                 "no authority"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in jurisdiction_keywords if kw in text]
            if matched:
                sub = subsections.get("12b1", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(1)",
                    "ground": sub.get("ground", "Lack of subject matter jurisdiction"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Subject matter jurisdiction issue: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "CRITICAL",
                    "dismissal_type": "Dismissal with prejudice possible",
                    "legal_basis": "Court lacks power to hear this type of case",
                    "action_required": "File Motion to Dismiss under Rule 12(b)(1)",
                })

        # --- 12(b)(1) via UCCJEA (address-based analysis) ---
        if addresses_df is not None and not addresses_df.empty:
            state_col = None
            for c in ["state", "state_code", "jurisdiction"]:
                if c in addresses_df.columns:
                    state_col = c
                    break
            if state_col:
                states = addresses_df[state_col].dropna().astype(str).str.upper().unique()
                non_sc = [s for s in states if s not in ("SC", "SOUTH CAROLINA")]
                if non_sc:
                    grounds.append({
                        "rule": "SCRCP Rule 12(b)(1) / UCCJEA",
                        "ground": "Lack of subject matter jurisdiction - UCCJEA home state",
                        "date": "Case-wide",
                        "description": (
                            f"Addresses in {len(non_sc)} non-SC states found: "
                            f"{', '.join(non_sc)}. If child resided in another state "
                            f"for 6+ months, SC may lack jurisdiction under UCCJEA."
                        ),
                        "evidence": f"States found: {', '.join(states)}",
                        "severity": "CRITICAL",
                        "dismissal_type": "Dismissal for lack of jurisdiction",
                        "legal_basis": "SC Code 63-15-302 (UCCJEA Home State)",
                        "action_required": "File Motion to Dismiss; argue UCCJEA home state",
                    })

        # --- 12(b)(2): Lack of personal jurisdiction ---
        personal_j_keywords = ["personal jurisdiction", "not resident", "no contacts",
                               "minimum contacts", "long arm", "not served properly",
                               "no domicile", "not domiciled"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in personal_j_keywords if kw in text]
            if matched:
                sub = subsections.get("12b2", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(2)",
                    "ground": sub.get("ground", "Lack of personal jurisdiction"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Personal jurisdiction issue: "
                                   f"keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "dismissal_type": "Dismissal without prejudice",
                    "legal_basis": "Court lacks power over this particular party",
                    "action_required": "File Motion to Dismiss under Rule 12(b)(2)",
                })

        # --- 12(b)(3): Improper venue ---
        venue_keywords = ["improper venue", "wrong venue", "wrong county",
                          "wrong court", "transfer venue", "change venue",
                          "venue objection", "not proper venue"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in venue_keywords if kw in text]
            if matched:
                sub = subsections.get("12b3", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(3)",
                    "ground": sub.get("ground", "Improper venue"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Venue issue: keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "MODERATE",
                    "dismissal_type": "Transfer or dismissal",
                    "legal_basis": "Case filed in wrong judicial circuit",
                    "action_required": "File Motion to Dismiss or Transfer under Rule 12(b)(3)",
                })

        # --- 12(b)(4): Insufficiency of process ---
        process_keywords = ["insufficiency of process", "defective process",
                            "wrong form", "defective summons", "invalid summons",
                            "no summons", "unsigned order", "not signed",
                            "missing signature"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in process_keywords if kw in text]
            if matched:
                sub = subsections.get("12b4", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(4)",
                    "ground": sub.get("ground", "Insufficiency of process"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Process deficiency: keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "dismissal_type": "Dismissal without prejudice",
                    "legal_basis": "Process itself is defective",
                    "action_required": "File Motion to Dismiss under Rule 12(b)(4)",
                })

        # --- 12(b)(5): Insufficiency of service ---
        service_keywords = ["not served", "improper service", "no service",
                            "defective service", "service defect", "never received",
                            "not properly served", "insufficient service"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in service_keywords if kw in text]
            if matched:
                sub = subsections.get("12b5", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(5)",
                    "ground": sub.get("ground", "Insufficiency of service of process"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Service deficiency: keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "dismissal_type": "Dismissal without prejudice; may be re-served",
                    "legal_basis": "Service of process was not properly effectuated",
                    "action_required": "File Motion to Dismiss under Rule 12(b)(5)",
                })

        # --- 12(b)(6): Failure to state a claim ---
        claim_keywords = ["failure to state", "no claim", "fails to state",
                          "no cause of action", "no legal basis", "legally insufficient",
                          "no standing", "lack standing"]
        for idx, row in combined.iterrows():
            text = self._get_text_blob(row)
            matched = [kw for kw in claim_keywords if kw in text]
            if matched:
                sub = subsections.get("12b6", {})
                grounds.append({
                    "rule": "SCRCP Rule 12(b)(6)",
                    "ground": sub.get("ground", "Failure to state a claim"),
                    "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                    "description": f"Claim deficiency: keywords [{', '.join(matched)}] found",
                    "evidence": text[:300],
                    "severity": "HIGH",
                    "dismissal_type": "Dismissal with prejudice possible",
                    "legal_basis": "Pleading fails to state a claim upon which relief can be granted",
                    "action_required": "File Motion to Dismiss under Rule 12(b)(6)",
                })

        # Deduplicate
        seen = set()
        unique_grounds = []
        for g in grounds:
            key = (g["rule"], g["date"], g["evidence"][:50] if "evidence" in g else "")
            if key not in seen:
                seen.add(key)
                unique_grounds.append(g)

        return unique_grounds

    # ------------------------------------------------------------------
    # Rule 60(b)(3) Fraud Detection
    # ------------------------------------------------------------------

    def detect_rule_60_fraud(self, filings_df, detailed_hearings_df=None):
        """
        Detect fraud, misrepresentation, or misconduct warranting
        relief from judgment under SCRCP Rule 60(b)(3).
        """
        rule_60 = self.sc_family_court_rules.get("rule_60", {})
        fraud_findings = []

        all_dfs = [filings_df]
        if detailed_hearings_df is not None and not detailed_hearings_df.empty:
            all_dfs.append(detailed_hearings_df)
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)

        # Check each fraud indicator category from config
        for indicator_name, indicator_data in self.fraud_indicators.items():
            keywords = indicator_data.get("keywords", [])
            for idx, row in combined.iterrows():
                text = self._get_text_blob(row)
                matched = [kw for kw in keywords if kw in text]
                if matched:
                    fraud_findings.append({
                        "rule": rule_60.get("citation", "SCRCP Rule 60(b)(3)"),
                        "fraud_type": indicator_name,
                        "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                        "description": f"{indicator_name.replace('_', ' ').title()}: "
                                       f"keywords [{', '.join(matched)}] detected",
                        "evidence": text[:300],
                        "severity": indicator_data.get("severity", "HIGH"),
                        "rule_citation": indicator_data.get("rule_citation", ""),
                        "relief_available": "Vacate judgment; reopen case; sanctions",
                        "time_limit": "Must be filed within reasonable time, "
                                      "not more than 1 year after judgment",
                    })

        # Deduplicate
        seen = set()
        unique = []
        for f in fraud_findings:
            key = (f["fraud_type"], f["date"], f["evidence"][:50])
            if key not in seen:
                seen.add(key)
                unique.append(f)

        return unique

    # ------------------------------------------------------------------
    # 365-Day Case Resolution Analysis
    # ------------------------------------------------------------------

    def analyze_365_day_order(self, filings_df, date_col="date"):
        """
        Analyze compliance with SC Supreme Court 365-day
        case resolution administrative order.
        """
        rule = self.sc_family_court_rules.get("365_day_rule", {})
        max_days = rule.get("max_days", 365)

        if date_col not in filings_df.columns:
            return {"status": "UNKNOWN", "error": "No date column"}

        dates = pd.to_datetime(filings_df[date_col], errors="coerce").dropna()
        if dates.empty:
            return {"status": "UNKNOWN", "error": "No valid dates"}

        case_start = dates.min()
        most_recent = dates.max()
        elapsed = (most_recent - case_start).days
        today = datetime.now()
        total_elapsed = (today - case_start).days

        exceeded = total_elapsed > max_days
        overage_days = max(0, total_elapsed - max_days)

        # Calculate how many 365-day periods have passed
        periods = total_elapsed / max_days

        return {
            "status": "EXCEEDED" if exceeded else "WITHIN_LIMIT",
            "citation": rule.get("citation", "SC Family Court Administrative Order"),
            "case_start_date": str(case_start.date()),
            "most_recent_activity": str(most_recent.date()),
            "elapsed_days": total_elapsed,
            "max_allowed_days": max_days,
            "overage_days": overage_days,
            "periods_elapsed": round(periods, 2),
            "deadline_date": str((case_start + timedelta(days=max_days)).date()),
            "exceeded": exceeded,
            "dismissal_support": exceeded,
            "recommended_action": (
                f"Case has exceeded the 365-day deadline by {overage_days} days. "
                f"File motion citing SC Supreme Court Administrative Order "
                f"requiring disposition within 365 days of filing."
            ) if exceeded else "Case is within the 365-day limit.",
        }

    # ------------------------------------------------------------------
    # UCCJEA Jurisdiction Analysis
    # ------------------------------------------------------------------

    def analyze_uccjea_jurisdiction(self, addresses_data=None, filings_df=None):
        """
        Analyze UCCJEA (Uniform Child Custody Jurisdiction and
        Enforcement Act) jurisdiction issues.
        SC Code 63-15-300 et seq.
        """
        uccjea_rule = self.sc_family_court_rules.get("uccjea", {})
        issues = []
        analysis = {
            "citation": uccjea_rule.get("citation", "SC Code 63-15-300 et seq."),
            "home_state_months": uccjea_rule.get("home_state_months", 6),
            "issues": issues,
        }

        # Analyze addresses for multi-state presence
        if addresses_data is not None and not addresses_data.empty:
            state_col = None
            for c in ["state", "state_code", "jurisdiction"]:
                if c in addresses_data.columns:
                    state_col = c
                    break
            if state_col:
                states = addresses_data[state_col].dropna().astype(str).str.strip().str.upper()
                unique_states = states.unique().tolist()
                analysis["states_involved"] = unique_states

                non_sc = [s for s in unique_states if s not in ("SC", "SOUTH CAROLINA")]
                if non_sc:
                    issues.append({
                        "type": "MULTI_STATE_RESIDENCE",
                        "description": (
                            f"Addresses found in {len(unique_states)} states: "
                            f"{', '.join(unique_states)}. UCCJEA home state "
                            f"determination required."
                        ),
                        "severity": "CRITICAL",
                        "legal_basis": "SC Code 63-15-302 (Home State Jurisdiction)",
                        "action": "Determine which state is home state "
                                  "(child resided 6 consecutive months prior to filing)",
                    })

            # Check for date-based residency
            date_col = None
            for c in ["move_date", "date", "start_date", "from_date"]:
                if c in addresses_data.columns:
                    date_col = c
                    break
            if date_col and state_col:
                addr_df = addresses_data.copy()
                addr_df[date_col] = pd.to_datetime(addr_df[date_col], errors="coerce")
                addr_df = addr_df.dropna(subset=[date_col]).sort_values(date_col)
                if not addr_df.empty:
                    analysis["address_timeline"] = []
                    for _, row in addr_df.iterrows():
                        analysis["address_timeline"].append({
                            "date": str(row[date_col].date()),
                            "state": str(row[state_col]),
                            "address": str(row.get("address", row.get("city", ""))),
                        })

        # Scan filings for UCCJEA-related text
        if filings_df is not None and not filings_df.empty:
            uccjea_keywords = ["uccjea", "home state", "jurisdiction", "interstate",
                               "uniform child custody", "emergency jurisdiction",
                               "inconvenient forum", "declining jurisdiction",
                               "continuing jurisdiction", "temporary emergency"]
            for idx, row in filings_df.iterrows():
                text = self._get_text_blob(row)
                matched = [kw for kw in uccjea_keywords if kw in text]
                if matched:
                    issues.append({
                        "type": "UCCJEA_REFERENCE",
                        "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                        "description": f"UCCJEA issue referenced: [{', '.join(matched)}]",
                        "evidence": text[:300],
                        "severity": "HIGH",
                    })

        analysis["total_issues"] = len(issues)
        analysis["dismissal_support"] = any(
            i.get("severity") == "CRITICAL" for i in issues
        )
        return analysis

    # ------------------------------------------------------------------
    # Best Interest of the Child Factors (SC Code 63-15-240)
    # ------------------------------------------------------------------

    def analyze_best_interest_factors(self, classified_abuse_df=None,
                                      filings_df=None, officials_df=None):
        """
        Analyze the 17 best interest of the child factors
        under SC Code 63-15-240.
        """
        factors_list = self.sc_custody_factors
        result = {
            "citation": "SC Code 63-15-240",
            "total_factors": len(factors_list),
            "factors": [],
        }

        # Map abuse data to relevant factors
        abuse_factor_map = {
            "domestic_violence": ["PHYSICAL_ABUSE", "COERCIVE_CONTROL", "STALKING"],
            "effect_of_abuse_on_child": ["CHILD_ABUSE_ENABLEMENT", "PSYCHOLOGICAL_ABUSE"],
            "substance_abuse": ["SUBSTANCE_RELATED"],
            "mental_and_physical_health_of_all_involved": ["PSYCHOLOGICAL_ABUSE"],
            "actions_of_each_parent_to_encourage_relationship": [
                "COERCIVE_CONTROL", "CHILD_ABUSE_ENABLEMENT"
            ],
        }

        for factor in factors_list:
            factor_data = {
                "factor": factor,
                "label": factor.replace("_", " ").title(),
                "evidence_count": 0,
                "evidence": [],
                "severity": "LOW",
            }

            # Check if abuse data maps to this factor
            if classified_abuse_df is not None and not classified_abuse_df.empty:
                mapped_types = abuse_factor_map.get(factor, [])
                cat_col = None
                for c in ["category", "abuse_type", "type", "classification"]:
                    if c in classified_abuse_df.columns:
                        cat_col = c
                        break
                if cat_col and mapped_types:
                    for abuse_type in mapped_types:
                        matches = classified_abuse_df[
                            classified_abuse_df[cat_col].astype(str).str.upper().str.contains(
                                abuse_type, na=False
                            )
                        ]
                        if not matches.empty:
                            factor_data["evidence_count"] += len(matches)
                            factor_data["severity"] = "HIGH"
                            for _, m in matches.head(3).iterrows():
                                factor_data["evidence"].append({
                                    "date": str(m.get("date", "")),
                                    "type": str(m.get(cat_col, "")),
                                    "description": str(m.get("description", m.get("details", "")))[:200],
                                })

            # Scan filings for factor keywords
            if filings_df is not None and not filings_df.empty:
                factor_words = factor.replace("_", " ").lower().split()
                for idx, row in filings_df.iterrows():
                    text = self._get_text_blob(row)
                    if any(w in text for w in factor_words if len(w) > 3):
                        factor_data["evidence_count"] += 1
                        if factor_data["severity"] == "LOW":
                            factor_data["severity"] = "MODERATE"

            result["factors"].append(factor_data)

        # Summary
        high_factors = [f for f in result["factors"] if f["severity"] == "HIGH"]
        result["high_severity_factors"] = len(high_factors)
        result["factors_with_evidence"] = sum(
            1 for f in result["factors"] if f["evidence_count"] > 0
        )

        return result

    # ------------------------------------------------------------------
    # Judicial Code of Conduct Compliance
    # ------------------------------------------------------------------

    def analyze_judicial_code_compliance(self, filings_df,
                                         detailed_hearings_df=None):
        """
        Analyze judicial conduct against SC Code of Judicial Conduct.
        """
        canons = self.sc_family_court_rules.get("judicial_code", {}).get("canons", {})
        violations = []

        all_dfs = [filings_df]
        if detailed_hearings_df is not None and not detailed_hearings_df.empty:
            all_dfs.append(detailed_hearings_df)
        combined = pd.concat(all_dfs, ignore_index=True, sort=False)

        # Canon violation keyword mapping
        canon_keywords = {
            "canon_1": {
                "label": "Independence and Integrity",
                "keywords": ["corrupt", "brib", "dishonest", "lack integrity",
                              "unethical", "improper influence"],
            },
            "canon_2": {
                "label": "Impropriety / Appearance of Impropriety",
                "keywords": ["ex parte", "bias", "prejudic", "partial",
                              "conflict of interest", "appearance of impropriety",
                              "social relationship", "political"],
            },
            "canon_3": {
                "label": "Impartiality and Diligence",
                "keywords": ["not impartial", "one-sided", "favor", "unfair",
                              "denied hearing", "refused to hear", "not heard",
                              "without hearing", "delayed ruling", "no ruling"],
            },
            "canon_4": {
                "label": "Conflicts with Judicial Obligations",
                "keywords": ["outside activity", "business dealing",
                              "financial interest", "fiduciary"],
            },
        }

        for canon_key, canon_data in canon_keywords.items():
            for idx, row in combined.iterrows():
                text = self._get_text_blob(row)
                matched = [kw for kw in canon_data["keywords"] if kw in text]
                if matched:
                    violations.append({
                        "canon": canon_key,
                        "canon_description": canons.get(canon_key, canon_data["label"]),
                        "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                        "description": f"Potential {canon_data['label']} violation: "
                                       f"keywords [{', '.join(matched)}] found",
                        "evidence": text[:300],
                        "severity": "HIGH",
                        "citation": "SC Code of Judicial Conduct, " + canon_key.replace("_", " ").title(),
                        "remedy": "Judicial complaint; motion for recusal; appeal",
                    })

        # Check for judge rotation issues (same judge too long)
        judge_col = None
        date_col = None
        for c in ["judge", "ruling_by", "assigned_to"]:
            if c in filings_df.columns:
                judge_col = c
                break
        for c in ["date", "filing_date"]:
            if c in filings_df.columns:
                date_col = c
                break

        if judge_col and date_col:
            judge_counts = filings_df[judge_col].dropna().value_counts()
            for judge, count in judge_counts.items():
                if count > 10:
                    violations.append({
                        "canon": "canon_3",
                        "canon_description": "Impartiality and Diligence",
                        "date": "Case-wide",
                        "description": (
                            f"Judge '{judge}' appeared in {count} filings. "
                            f"Extended involvement may warrant scrutiny for bias."
                        ),
                        "evidence": f"Total appearances: {count}",
                        "severity": "MODERATE",
                        "citation": "SC Code of Judicial Conduct, Canon 3",
                        "remedy": "Motion for recusal; judicial performance review",
                    })

        # Deduplicate
        seen = set()
        unique = []
        for v in violations:
            key = (v["canon"], v["date"], v.get("evidence", "")[:50])
            if key not in seen:
                seen.add(key)
                unique.append(v)

        return {"violations": unique, "total_violations": len(unique)}

    # ------------------------------------------------------------------
    # Per-Person Abuse Scoring
    # ------------------------------------------------------------------

    def analyze_per_person_abuse_scoring(self, classified_df):
        """
        Score each person mentioned in abuse data by total
        abuse involvement and severity.
        """
        scoring = {}

        # Find name columns
        name_cols = []
        for c in ["perpetrator", "abuser", "respondent", "filed_by", "party",
                   "name", "person", "subject"]:
            if c in classified_df.columns:
                name_cols.append(c)

        if not name_cols:
            return scoring

        severity_col = None
        for c in ["severity_score", "casi_score", "severity", "score"]:
            if c in classified_df.columns:
                severity_col = c
                break

        cat_col = None
        for c in ["category", "abuse_type", "type", "classification"]:
            if c in classified_df.columns:
                cat_col = c
                break

        for col in name_cols:
            for name in classified_df[col].dropna().unique():
                name_str = str(name).strip()
                if not name_str or name_str.lower() in ("nan", "none", "unknown", ""):
                    continue

                person_rows = classified_df[classified_df[col] == name]

                if name_str not in scoring:
                    scoring[name_str] = {
                        "total_incidents": 0,
                        "total_severity": 0.0,
                        "avg_severity": 0.0,
                        "max_severity": 0.0,
                        "abuse_types": {},
                        "role": col,
                        "date_range": "",
                    }

                scoring[name_str]["total_incidents"] += len(person_rows)

                if severity_col:
                    scores = pd.to_numeric(person_rows[severity_col], errors="coerce").dropna()
                    if not scores.empty:
                        scoring[name_str]["total_severity"] += float(scores.sum())
                        scoring[name_str]["max_severity"] = max(
                            scoring[name_str]["max_severity"], float(scores.max())
                        )

                if cat_col:
                    type_counts = person_rows[cat_col].value_counts().to_dict()
                    for t, c_count in type_counts.items():
                        scoring[name_str]["abuse_types"][str(t)] = (
                            scoring[name_str]["abuse_types"].get(str(t), 0) + c_count
                        )

                # Date range
                date_col = None
                for dc in ["date", "incident_date", "filing_date"]:
                    if dc in person_rows.columns:
                        date_col = dc
                        break
                if date_col:
                    dates = pd.to_datetime(person_rows[date_col], errors="coerce").dropna()
                    if not dates.empty:
                        scoring[name_str]["date_range"] = (
                            f"{dates.min().date()} to {dates.max().date()}"
                        )

        # Calculate averages
        for name_str in scoring:
            total = scoring[name_str]["total_incidents"]
            if total > 0:
                scoring[name_str]["avg_severity"] = round(
                    scoring[name_str]["total_severity"] / total, 2
                )

        return scoring

    # ------------------------------------------------------------------
    # Dismissal Opportunities (Combines Rule 11, 12, 60, 365, UCCJEA)
    # ------------------------------------------------------------------

    def identify_dismissal_opportunities(self, filings_df, addresses_data=None):
        """
        Comprehensive analysis of all available grounds for dismissal.
        Combines Rule 11, Rule 12, Rule 60, 365-day, and UCCJEA analysis.
        """
        opportunities = []

        # 1. Rule 11 violations
        rule_11 = self.detect_rule_11_violations(filings_df)
        for v in rule_11:
            if v.get("dismissal_support"):
                opportunities.append({
                    "ground": "SCRCP Rule 11 Violation",
                    "rule": v["rule"],
                    "sub_rule": v.get("sub_rule", ""),
                    "date": v["date"],
                    "description": v["description"],
                    "evidence": v.get("evidence", "")[:200],
                    "severity": v["severity"],
                    "action": "File Motion for Sanctions under Rule 11; "
                              "seek dismissal for pattern of frivolous filings",
                    "strength": "STRONG" if v["severity"] in ("CRITICAL", "HIGH") else "MODERATE",
                })

        # 2. Rule 12 dismissal grounds
        rule_12 = self.detect_rule_12_dismissal_grounds(filings_df, addresses_df=addresses_data)
        for g in rule_12:
            opportunities.append({
                "ground": g["rule"],
                "rule": g["rule"],
                "sub_rule": g.get("ground", ""),
                "date": g["date"],
                "description": g["description"],
                "evidence": g.get("evidence", "")[:200],
                "severity": g["severity"],
                "action": g.get("action_required", "File Motion to Dismiss"),
                "strength": "STRONG" if g["severity"] == "CRITICAL" else "MODERATE",
            })

        # 3. Rule 60 fraud
        rule_60 = self.detect_rule_60_fraud(filings_df)
        for f in rule_60:
            opportunities.append({
                "ground": "SCRCP Rule 60(b)(3) - Fraud on Court",
                "rule": f["rule"],
                "sub_rule": f["fraud_type"],
                "date": f["date"],
                "description": f["description"],
                "evidence": f.get("evidence", "")[:200],
                "severity": f["severity"],
                "action": "File Motion for Relief from Judgment under Rule 60(b)(3)",
                "strength": "STRONG" if f["severity"] in ("CRITICAL", "HIGH") else "MODERATE",
            })

        # 4. 365-day order
        analysis_365 = self.analyze_365_day_order(filings_df)
        if analysis_365.get("exceeded"):
            opportunities.append({
                "ground": "365-Day Administrative Order Exceeded",
                "rule": analysis_365.get("citation", "SC Supreme Court Administrative Order"),
                "sub_rule": "Case Resolution Deadline",
                "date": analysis_365.get("deadline_date", ""),
                "description": (
                    f"Case has exceeded 365-day limit by "
                    f"{analysis_365.get('overage_days', 0)} days "
                    f"(total: {analysis_365.get('elapsed_days', 0)} days)"
                ),
                "evidence": f"Case started: {analysis_365.get('case_start_date', '')}",
                "severity": "HIGH",
                "action": analysis_365.get("recommended_action", ""),
                "strength": "STRONG",
            })

        # 5. UCCJEA jurisdiction
        if addresses_data is not None:
            uccjea = self.analyze_uccjea_jurisdiction(
                addresses_data=addresses_data, filings_df=filings_df
            )
            for issue in uccjea.get("issues", []):
                if issue.get("severity") == "CRITICAL":
                    opportunities.append({
                        "ground": "UCCJEA Jurisdiction Defect",
                        "rule": "SC Code 63-15-300 et seq.",
                        "sub_rule": issue.get("type", ""),
                        "date": issue.get("date", "Case-wide"),
                        "description": issue["description"],
                        "evidence": issue.get("evidence", "")[:200] if "evidence" in issue else "",
                        "severity": "CRITICAL",
                        "action": "File Motion to Dismiss for lack of jurisdiction under UCCJEA",
                        "strength": "STRONG",
                    })

        # 6. Check dismissal grounds from config
        for ground_name, ground_data in self.dismissal_grounds.items():
            keywords = ground_name.replace("_", " ").split()
            for idx, row in filings_df.iterrows():
                text = self._get_text_blob(row)
                if any(kw in text for kw in keywords if len(kw) > 3):
                    opportunities.append({
                        "ground": ground_data.get("description", ground_name),
                        "rule": ground_data.get("rule", ""),
                        "sub_rule": ground_name,
                        "date": str(row.get("date", row.get("filing_date", "Unknown"))),
                        "description": ground_data.get("description", ""),
                        "evidence": text[:200],
                        "severity": "HIGH",
                        "action": f"File Motion to Dismiss under {ground_data.get('rule', '')}",
                        "strength": "MODERATE",
                    })
                    break  # One per ground is enough

        # Deduplicate and sort by strength
        seen = set()
        unique = []
        for o in opportunities:
            key = (o["ground"], o["date"])
            if key not in seen:
                seen.add(key)
                unique.append(o)

        strength_order = {"STRONG": 0, "MODERATE": 1, "WEAK": 2}
        unique.sort(key=lambda x: strength_order.get(x.get("strength", "WEAK"), 2))

        return unique

    # ------------------------------------------------------------------
    # Judge Rotation Analysis
    # ------------------------------------------------------------------

    def analyze_judge_rotation(self, filings_df):
        """Analyze judge assignments and rotations across the case."""
        judge_col = None
        date_col = None
        for c in ["judge", "ruling_by", "assigned_to"]:
            if c in filings_df.columns:
                judge_col = c
                break
        for c in ["date", "filing_date"]:
            if c in filings_df.columns:
                date_col = c
                break

        if not judge_col:
            return {"error": "No judge column found"}

        judges = filings_df[judge_col].dropna()
        if judges.empty:
            return {"error": "No judge data"}

        rotation = {
            "total_judges": int(judges.nunique()),
            "judge_counts": judges.value_counts().to_dict(),
            "primary_judge": str(judges.mode().iloc[0]) if not judges.mode().empty else "Unknown",
            "changes": [],
        }

        # Track judge changes over time
        if date_col:
            df = filings_df[[date_col, judge_col]].dropna()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna().sort_values(date_col)

            prev_judge = None
            for _, row in df.iterrows():
                current = str(row[judge_col])
                if prev_judge and current != prev_judge:
                    rotation["changes"].append({
                        "date": str(row[date_col].date()),
                        "from": prev_judge,
                        "to": current,
                    })
                prev_judge = current

        rotation["total_changes"] = len(rotation["changes"])
        rotation["excessive_rotation"] = rotation["total_changes"] > 3

        return rotation

    # ------------------------------------------------------------------
    # Conflict of Interest Detection
    # ------------------------------------------------------------------

    def detect_conflict_of_interest(self, officials_data=None):
        """Detect potential conflicts of interest among court officials."""
        conflicts = []

        # Check official backgrounds for shared affiliations
        if officials_data is not None and not officials_data.empty:
            affiliation_cols = ["law_firm", "firm", "organization", "association",
                                "school", "university", "bar_number", "notary",
                                "connection", "relationship"]

            existing_cols = [c for c in affiliation_cols if c in officials_data.columns]

            # Find shared affiliations
            for col in existing_cols:
                groups = defaultdict(list)
                for _, row in officials_data.iterrows():
                    val = str(row.get(col, "")).strip()
                    if val and val.lower() not in ("", "nan", "none", "n/a"):
                        groups[val.lower()].append(
                            str(row.get("name", row.get("official", "Unknown")))
                        )

                for affil, members in groups.items():
                    if len(members) >= 2:
                        conflicts.append({
                            "type": f"SHARED_{col.upper()}",
                            "persons": members,
                            "affiliation": affil,
                            "description": (
                                f"{', '.join(members)} share {col}: '{affil}'"
                            ),
                            "severity": "HIGH" if col in ("law_firm", "firm") else "MODERATE",
                            "citation": "SC Code of Judicial Conduct, Canon 2 & 3",
                            "action": "Motion for recusal; request disclosure",
                        })

            # Check for dual roles
            role_col = None
            for c in ["role", "position", "title"]:
                if c in officials_data.columns:
                    role_col = c
                    break
            if role_col:
                name_col = "name" if "name" in officials_data.columns else "official"
                if name_col in officials_data.columns:
                    name_roles = defaultdict(list)
                    for _, row in officials_data.iterrows():
                        name = str(row.get(name_col, "")).strip()
                        role = str(row.get(role_col, "")).strip()
                        if name and role:
                            name_roles[name].append(role)

                    for name, roles in name_roles.items():
                        if len(roles) > 1:
                            conflicts.append({
                                "type": "DUAL_ROLE",
                                "persons": [name],
                                "affiliation": ", ".join(roles),
                                "description": f"{name} has multiple roles: {', '.join(roles)}",
                                "severity": "HIGH",
                                "citation": "SC Code of Judicial Conduct",
                                "action": "Investigate potential conflict",
                            })

        # Cross-reference with officials registry
        for name, info in self.officials_registry.items():
            bg = info.get("background", {})
            for key, val in bg.items():
                val_str = str(val).lower()
                if any(kw in val_str for kw in ["conflict", "relationship",
                                                 "married to", "related to",
                                                 "partner", "spouse"]):
                    conflicts.append({
                        "type": "PERSONAL_RELATIONSHIP",
                        "persons": [name],
                        "affiliation": str(val),
                        "description": f"{name} has potential personal conflict: {val}",
                        "severity": "HIGH",
                        "citation": "SC Code of Judicial Conduct, Canon 2",
                        "action": "Motion for recusal; file judicial complaint",
                    })

        return conflicts

    # ------------------------------------------------------------------
    # Detailed Event Timeline
    # ------------------------------------------------------------------

    def generate_detailed_event_timeline(self, filings_df, classified_df=None,
                                          violations_df=None):
        """
        Generate a comprehensive, merged timeline from all data sources.
        Each event is labeled with type, severity, and rule violations.
        """
        events = []

        # Add filings
        date_col = None
        for c in ["date", "filing_date"]:
            if c in filings_df.columns:
                date_col = c
                break

        if date_col:
            for _, row in filings_df.iterrows():
                dt = pd.to_datetime(row.get(date_col), errors="coerce")
                if pd.isna(dt):
                    continue
                events.append({
                    "date": str(dt.date()),
                    "source": "court_filing",
                    "type": str(row.get("type", row.get("filing_type", row.get("action", "")))),
                    "description": str(row.get("description", row.get("details", row.get("notes", "")))),
                    "party": str(row.get("filed_by", row.get("party", ""))),
                    "outcome": str(row.get("outcome", row.get("ruling", ""))),
                    "judge": str(row.get("judge", row.get("ruling_by", ""))),
                    "severity": "MODERATE",
                    "rule_violations": [],
                    "labels": [],
                })

        # Add abuse incidents
        if classified_df is not None and not classified_df.empty:
            abuse_date_col = None
            for c in ["date", "incident_date", "filing_date"]:
                if c in classified_df.columns:
                    abuse_date_col = c
                    break
            if abuse_date_col:
                for _, row in classified_df.iterrows():
                    dt = pd.to_datetime(row.get(abuse_date_col), errors="coerce")
                    if pd.isna(dt):
                        continue
                    cat = str(row.get("category", row.get("abuse_type", row.get("type", ""))))
                    sev = row.get("severity_score", row.get("severity", ""))
                    events.append({
                        "date": str(dt.date()),
                        "source": "abuse_incident",
                        "type": cat,
                        "description": str(row.get("description", row.get("details", "")))[:300],
                        "party": str(row.get("perpetrator", row.get("abuser", ""))),
                        "outcome": "",
                        "judge": "",
                        "severity": "HIGH" if str(sev) not in ("", "nan") and float(str(sev) if str(sev).replace(".", "").isdigit() else "0") > 5 else "MODERATE",
                        "rule_violations": [],
                        "labels": [cat],
                    })

        # Add violations
        if violations_df is not None and not violations_df.empty:
            viol_date_col = None
            for c in ["date", "violation_date", "filing_date"]:
                if c in violations_df.columns:
                    viol_date_col = c
                    break
            if viol_date_col:
                for _, row in violations_df.iterrows():
                    dt = pd.to_datetime(row.get(viol_date_col), errors="coerce")
                    if pd.isna(dt):
                        continue
                    events.append({
                        "date": str(dt.date()),
                        "source": "violation",
                        "type": str(row.get("type", row.get("violation_type", ""))),
                        "description": str(row.get("description", row.get("details", "")))[:300],
                        "party": str(row.get("party", row.get("violator", ""))),
                        "outcome": "",
                        "judge": "",
                        "severity": str(row.get("severity", "HIGH")),
                        "rule_violations": [str(row.get("rule", row.get("citation", "")))],
                        "labels": ["VIOLATION"],
                    })

        # Sort by date
        events.sort(key=lambda e: e.get("date", "0000-00-00"))

        # Filter to post-analysis start date events
        filtered = []
        for e in events:
            try:
                edt = datetime.strptime(e["date"], "%Y-%m-%d")
                if edt >= self.analysis_start_date:
                    filtered.append(e)
                else:
                    filtered.append(e)  # Keep all events but mark pre-analysis
            except (ValueError, TypeError):
                filtered.append(e)

        return filtered
