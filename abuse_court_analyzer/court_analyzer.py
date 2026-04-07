"""
Court Case Analysis Module.

Analyzes court filings, identifies patterns in judicial behavior,
tracks officials, calculates costs, and detects procedural violations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from .config import COURT_ROLES, RIGHTS_CATEGORIES

try:
    from .config import (SC_FAMILY_COURT_RULES, SC_RULES_CIVIL_PROCEDURE,
                         SC_JUDICIAL_CODE, SC_CUSTODY_FACTORS,
                         SC_SUPREME_COURT_365, UCCJEA, CONSTITUTIONAL_RIGHTS,
                         FRAUD_INDICATORS, DISMISSAL_GROUNDS)
except ImportError:
    SC_FAMILY_COURT_RULES = {}
    SC_RULES_CIVIL_PROCEDURE = {}
    SC_JUDICIAL_CODE = {}
    SC_CUSTODY_FACTORS = {}
    SC_SUPREME_COURT_365 = {}
    UCCJEA = {}
    CONSTITUTIONAL_RIGHTS = {}
    FRAUD_INDICATORS = {}
    DISMISSAL_GROUNDS = {}

# Case analysis start date -- all SC-specific analysis uses this cutoff
SC_ANALYSIS_START_DATE = pd.Timestamp("2022-03-11")


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

        # SC-specific config references (loaded from config module)
        self.sc_family_court_rules = SC_FAMILY_COURT_RULES
        self.sc_rules_civil_procedure = SC_RULES_CIVIL_PROCEDURE
        self.sc_judicial_code = SC_JUDICIAL_CODE
        self.sc_custody_factors = SC_CUSTODY_FACTORS
        self.sc_supreme_court_365 = SC_SUPREME_COURT_365
        self.uccjea = UCCJEA
        self.constitutional_rights = CONSTITUTIONAL_RIGHTS
        self.fraud_indicators = FRAUD_INDICATORS
        self.dismissal_grounds = DISMISSAL_GROUNDS
        self.analysis_start_date = SC_ANALYSIS_START_DATE

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
