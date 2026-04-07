"""
Configuration and classification definitions for the analysis tool.
"""

# ============================================================================
# POST-SEPARATION ABUSE CLASSIFICATION TAXONOMY
# ============================================================================

ABUSE_CATEGORIES = {
    "COERCIVE_CONTROL": {
        "label": "Coercive Control",
        "traits": [
            "monitoring_movements", "isolating_from_support", "controlling_finances",
            "dictating_daily_activities", "restricting_communication",
            "using_children_as_leverage", "threatening_custody_loss",
            "weaponizing_court_system", "filing_frivolous_motions",
            "demanding_excessive_compliance"
        ],
        "severity_weight": 0.9,
        "legal_references": {
            "federal": ["18 USC 2261A - Stalking", "Violence Against Women Act (VAWA)"],
        }
    },
    "LEGAL_ABUSE": {
        "label": "Legal/Litigation Abuse",
        "traits": [
            "frivolous_filings", "repeated_motions", "discovery_abuse",
            "contempt_threats", "emergency_motions_without_emergency",
            "delaying_tactics", "refusing_to_negotiate", "court_shopping",
            "misrepresentation_to_court", "vexatious_litigation",
            "weaponizing_gal", "parental_alienation_claims"
        ],
        "severity_weight": 0.85,
        "legal_references": {
            "federal": ["28 USC 1927 - Vexatious Litigation"],
        }
    },
    "FINANCIAL_ABUSE": {
        "label": "Financial Abuse",
        "traits": [
            "hiding_assets", "refusing_support_payments", "running_up_legal_fees",
            "destroying_credit", "unauthorized_account_access",
            "forcing_unnecessary_litigation_costs", "depleting_marital_assets",
            "income_manipulation", "tax_fraud", "coerced_debt"
        ],
        "severity_weight": 0.8,
        "legal_references": {
            "federal": ["IRS Tax Fraud Statutes"],
        }
    },
    "PSYCHOLOGICAL_ABUSE": {
        "label": "Psychological/Emotional Abuse",
        "traits": [
            "gaslighting", "verbal_degradation", "intimidation",
            "threatening_behavior", "public_humiliation", "blame_shifting",
            "minimizing_abuse", "denying_abuse", "emotional_manipulation",
            "false_allegations", "smear_campaigns", "triangulation"
        ],
        "severity_weight": 0.85,
        "legal_references": {
            "federal": [],
        }
    },
    "STALKING": {
        "label": "Stalking/Surveillance",
        "traits": [
            "physical_following", "electronic_surveillance", "gps_tracking",
            "social_media_monitoring", "contacting_employer",
            "contacting_friends_family", "drive_bys", "unwanted_contact",
            "using_third_parties_to_monitor", "cyberstalking"
        ],
        "severity_weight": 0.95,
        "legal_references": {
            "federal": ["18 USC 2261A - Interstate Stalking"],
        }
    },
    "PHYSICAL_ABUSE": {
        "label": "Physical Violence/Threats",
        "traits": [
            "hitting", "pushing", "restraining", "throwing_objects",
            "blocking_exits", "destroying_property", "weapon_threats",
            "physical_intimidation", "assault", "battery"
        ],
        "severity_weight": 1.0,
        "legal_references": {
            "federal": ["18 USC 2261 - Domestic Violence"],
        }
    },
    "CHILD_ABUSE_ENABLEMENT": {
        "label": "Child-Related Abuse",
        "traits": [
            "parental_alienation", "withholding_children", "exposing_to_conflict",
            "using_children_as_messengers", "interrogating_children",
            "making_false_cps_reports", "undermining_parental_authority",
            "scheduling_conflicts_deliberately", "refusing_coparenting"
        ],
        "severity_weight": 0.9,
        "legal_references": {
            "federal": ["Parental Kidnapping Prevention Act"],
        }
    },
    "SUBSTANCE_RELATED": {
        "label": "Substance Abuse Related",
        "traits": [
            "alcohol_abuse_present", "drug_use_present", "substance_during_custody",
            "driving_impaired_with_children", "erratic_behavior_substance",
            "denial_of_substance_issues"
        ],
        "severity_weight": 0.7,
        "legal_references": {
            "federal": [],
        }
    }
}

# Variables tracked for cycle prediction
CYCLE_VARIABLES = [
    "date", "abuse_type", "severity_score", "perpetrator_behavior",
    "victim_impact", "children_involved", "substance_use_noted",
    "work_performance_change", "financial_action", "legal_filing",
    "stalking_behavior", "mental_health_indicator", "biometric_data",
    "witness_present", "documented_evidence", "police_report_filed",
    "court_date_proximity", "holiday_proximity", "custody_exchange_date",
    "communication_frequency", "threat_level"
]

# Court official roles
COURT_ROLES = [
    "judge", "attorney_petitioner", "attorney_respondent",
    "guardian_ad_litem", "mediator", "custody_evaluator",
    "therapist_court_appointed", "clerk", "magistrate",
    "special_master", "parenting_coordinator"
]

# Legal rights categories (to be populated per state)
RIGHTS_CATEGORIES = [
    "due_process", "equal_protection", "right_to_counsel",
    "right_to_fair_hearing", "right_to_timely_resolution",
    "right_to_appeal", "right_to_discovery", "right_to_present_evidence",
    "right_to_cross_examine", "parental_rights",
    "right_to_be_free_from_abuse", "right_to_privacy"
]

# ============================================================================
# SC FAMILY COURT RULES AND FRAUD DETECTION
# ============================================================================

SC_FAMILY_COURT_RULES = {
    "rule_11": {
        "citation": "SCRCP Rule 11",
        "title": "Signing of Pleadings, Motions, and Other Papers; Sanctions",
        "requirements": [
            "well_grounded_in_fact",
            "warranted_by_existing_law",
            "not_for_improper_purpose",
        ],
        "improper_purposes": [
            "harassment", "delay", "needless_increase_in_cost",
        ],
    },
    "rule_12": {
        "citation": "SCRCP Rule 12",
        "title": "Defenses and Objections",
        "subsections": {
            "12b1": {"citation": "SCRCP Rule 12(b)(1)", "ground": "Lack of subject matter jurisdiction"},
            "12b2": {"citation": "SCRCP Rule 12(b)(2)", "ground": "Lack of personal jurisdiction"},
            "12b3": {"citation": "SCRCP Rule 12(b)(3)", "ground": "Improper venue"},
            "12b4": {"citation": "SCRCP Rule 12(b)(4)", "ground": "Insufficiency of process"},
            "12b5": {"citation": "SCRCP Rule 12(b)(5)", "ground": "Insufficiency of service of process"},
            "12b6": {"citation": "SCRCP Rule 12(b)(6)", "ground": "Failure to state a claim"},
        },
    },
    "rule_60": {
        "citation": "SCRCP Rule 60(b)(3)",
        "title": "Relief from Judgment - Fraud, Misrepresentation, or Misconduct",
        "grounds": [
            "fraud", "misrepresentation", "other_misconduct",
        ],
    },
    "365_day_rule": {
        "citation": "SC Family Court Benchbook / Administrative Order",
        "title": "365-Day Case Resolution Deadline",
        "max_days": 365,
    },
    "uccjea": {
        "citation": "SC Code 63-15-300 et seq.",
        "title": "Uniform Child Custody Jurisdiction and Enforcement Act",
        "home_state_months": 6,
    },
    "best_interest": {
        "citation": "SC Code 63-15-240",
        "title": "Best Interest of the Child Factors",
        "factors": [
            "temperament_and_developmental_needs",
            "parental_wishes",
            "childs_preference",
            "interaction_with_parents_siblings",
            "childs_adjustment_to_home_school_community",
            "mental_and_physical_health_of_all_involved",
            "childs_cultural_background",
            "actions_of_each_parent_to_encourage_relationship",
            "effect_of_abuse_on_child",
            "whether_parent_has_been_primary_caretaker",
            "whether_custody_award_will_encourage_contact",
            "domestic_violence",
            "substance_abuse",
            "other_factors_court_finds_relevant",
            "encumbrances_on_title",
            "parenting_plan",
            "availability_of_parent",
        ],
    },
    "judicial_code": {
        "citation": "SC Code of Judicial Conduct",
        "canons": {
            "canon_1": "Uphold independence and integrity of judiciary",
            "canon_2": "Avoid impropriety and appearance of impropriety",
            "canon_3": "Perform duties impartially and diligently",
            "canon_4": "Minimize risk of conflicts with judicial obligations",
            "canon_5": "Refrain from inappropriate political activity",
        },
    },
}

FRAUD_INDICATORS = {
    "false_statement": {
        "keywords": ["false", "untrue", "fabricat", "lie", "lied", "perjur", "misstat"],
        "severity": "HIGH",
        "rule_citation": "SCRCP Rule 11; SC Code 16-9-10 (Perjury)",
    },
    "misrepresentation": {
        "keywords": ["misrepresent", "mislead", "deceiv", "decepti", "conceal", "omit"],
        "severity": "HIGH",
        "rule_citation": "SCRCP Rule 11; SCRCP Rule 60(b)(3)",
    },
    "harassment": {
        "keywords": ["harass", "intimidat", "threaten", "coerce", "bully", "stalk"],
        "severity": "HIGH",
        "rule_citation": "SCRCP Rule 11(b); SC Code 16-3-1700",
    },
    "improper_purpose": {
        "keywords": ["delay", "frivolous", "vexatious", "bad faith", "improper purpose",
                      "needless cost", "waste"],
        "severity": "MODERATE",
        "rule_citation": "SCRCP Rule 11(b)",
    },
    "ex_parte": {
        "keywords": ["ex parte", "ex-parte", "without notice", "no notice given",
                      "one-sided", "unreported contact"],
        "severity": "HIGH",
        "rule_citation": "SC Judicial Code Canon 3(B)(7)",
    },
    "docket_manipulation": {
        "keywords": ["false docket", "incorrect docket", "wrong case number",
                      "docket number mismatch", "altered docket"],
        "severity": "CRITICAL",
        "rule_citation": "SCRCP Rule 60(b)(3); SC Code 16-9-410",
    },
    "procedural_fraud": {
        "keywords": ["unsigned", "not signed", "missing signature", "forged",
                      "backdated", "altered order", "modified without"],
        "severity": "CRITICAL",
        "rule_citation": "SCRCP Rule 60(b)(3); SC Code 16-13-10",
    },
    "incorrect_parties": {
        "keywords": ["incorrect party", "wrong party", "missing party", "extra party",
                      "incorrect attorney", "wrong attorney", "not attorney of record"],
        "severity": "HIGH",
        "rule_citation": "SCRCP Rule 11; SCRCP Rule 17",
    },
}

DISMISSAL_GROUNDS = {
    "lack_subject_matter_jurisdiction": {
        "rule": "SCRCP Rule 12(b)(1)",
        "description": "Court lacks subject matter jurisdiction over the case",
        "uccjea_related": True,
    },
    "lack_personal_jurisdiction": {
        "rule": "SCRCP Rule 12(b)(2)",
        "description": "Court lacks personal jurisdiction over a party",
    },
    "improper_venue": {
        "rule": "SCRCP Rule 12(b)(3)",
        "description": "Case filed in improper venue",
    },
    "insufficiency_of_process": {
        "rule": "SCRCP Rule 12(b)(4)",
        "description": "Defective process (e.g., wrong form of summons)",
    },
    "insufficiency_of_service": {
        "rule": "SCRCP Rule 12(b)(5)",
        "description": "Service of process was not properly made",
    },
    "failure_to_state_claim": {
        "rule": "SCRCP Rule 12(b)(6)",
        "description": "Pleading fails to state a claim upon which relief can be granted",
    },
    "uccjea_home_state": {
        "rule": "SC Code 63-15-302",
        "description": "SC is not the home state under UCCJEA (child not resided here 6+ months)",
    },
    "365_day_exceeded": {
        "rule": "SC Family Court Administrative Order",
        "description": "Case has exceeded 365-day resolution deadline",
    },
    "fraud_on_court": {
        "rule": "SCRCP Rule 60(b)(3)",
        "description": "Fraud, misrepresentation, or misconduct by opposing party",
    },
}
