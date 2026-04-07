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
