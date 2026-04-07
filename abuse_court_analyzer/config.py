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
# SOUTH CAROLINA-SPECIFIC LEGAL FRAMEWORK
# ============================================================================

SC_FAMILY_COURT_RULES = {
    "Rule 1": {
        "title": "Scope of Rules",
        "text": "These rules govern procedure in all family court actions.",
        "citation": "SC Rules of Family Court, Rule 1",
    },
    "Rule 2": {
        "title": "One Action Rule",
        "text": "There shall be one form of action known as a civil action.",
        "citation": "SC Rules of Family Court, Rule 2",
    },
    "Rule 6": {
        "title": "Time",
        "text": "Computing and enlarging time; motions and affidavits.",
        "citation": "SC Rules of Family Court, Rule 6",
    },
    "Rule 11": {
        "title": "Signing and Verification of Pleadings",
        "text": ("Every pleading, motion, or other paper shall be signed by an attorney "
                 "or party. The signature constitutes a certificate that the signer has "
                 "read the document, that it is well grounded in fact, warranted by law, "
                 "and not interposed for improper purpose such as delay, harassment, "
                 "or needless increase in litigation cost."),
        "citation": "SC Rules of Civil Procedure, Rule 11",
        "sanctions": "Appropriate sanction including reasonable attorney fees.",
    },
    "Rule 12": {
        "title": "Defenses and Objections",
        "text": "Timing and manner of presenting defenses.",
        "citation": "SC Rules of Family Court, Rule 12",
    },
    "Rule 17": {
        "title": "Parties Plaintiff and Defendant; GAL",
        "text": "Guardian ad Litem appointment and duties.",
        "citation": "SC Rules of Family Court, Rule 17",
    },
    "Rule 26": {
        "title": "General Provisions Governing Discovery",
        "text": "Scope and limits of discovery.",
        "citation": "SC Rules of Family Court, Rule 26",
    },
    "Rule 37": {
        "title": "Failure to Make or Cooperate in Discovery",
        "text": "Sanctions for discovery abuse.",
        "citation": "SC Rules of Family Court, Rule 37",
    },
    "Rule 52": {
        "title": "Findings by the Court",
        "text": "Court must make findings of fact and conclusions of law.",
        "citation": "SC Rules of Family Court, Rule 52",
    },
    "Rule 59": {
        "title": "New Trial; Amendment of Judgments",
        "text": "Grounds for new trial or amendment.",
        "citation": "SC Rules of Family Court, Rule 59",
    },
    "Rule 60": {
        "title": "Relief from Judgment or Order",
        "text": ("On motion and just terms, court may relieve a party from final "
                 "judgment for: (1) mistake, inadvertence, surprise, excusable neglect; "
                 "(2) newly discovered evidence; (3) fraud, misrepresentation, or other "
                 "misconduct of adverse party; (4) void judgment; (5) satisfied, released, "
                 "or discharged judgment; (6) any other reason justifying relief."),
        "citation": "SC Rules of Civil Procedure, Rule 60(b)",
        "subsections": {
            "60(b)(1)": "Mistake, inadvertence, surprise, excusable neglect",
            "60(b)(2)": "Newly discovered evidence",
            "60(b)(3)": "Fraud, misrepresentation, or misconduct",
            "60(b)(4)": "Void judgment",
            "60(b)(5)": "Satisfied, released, or discharged judgment",
            "60(b)(6)": "Any other reason justifying relief",
        },
    },
}

SC_RULES_CIVIL_PROCEDURE = {
    "Rule 11": SC_FAMILY_COURT_RULES["Rule 11"],
    "Rule 60": SC_FAMILY_COURT_RULES["Rule 60"],
    "Rule 26": SC_FAMILY_COURT_RULES["Rule 26"],
    "Rule 37": SC_FAMILY_COURT_RULES["Rule 37"],
}

SC_JUDICIAL_CODE = {
    "Canon 1": {
        "title": "Independence and Integrity of the Judiciary",
        "text": "A judge shall uphold and promote the independence, integrity, and impartiality of the judiciary.",
        "citation": "SC Code of Judicial Conduct, Canon 1",
    },
    "Canon 2": {
        "title": "Impropriety and Appearance of Impropriety",
        "text": ("A judge shall avoid impropriety and the appearance of impropriety. "
                 "A judge shall not allow family, social, political, financial, or other "
                 "relationships to influence judicial conduct or judgment."),
        "citation": "SC Code of Judicial Conduct, Canon 2",
        "rules": {
            "2.2": "Impartiality and Fairness",
            "2.3": "Bias, Prejudice, and Harassment",
            "2.4": "External Influences on Judicial Conduct",
            "2.6": "Ensuring Right to Be Heard",
            "2.9": "Ex Parte Communications",
            "2.11": "Disqualification",
            "2.15": "Responding to Judicial and Lawyer Misconduct",
        },
    },
    "Canon 3": {
        "title": "Personal and Extrajudicial Activities",
        "text": "A judge shall conduct personal and extrajudicial activities to minimize conflicts.",
        "citation": "SC Code of Judicial Conduct, Canon 3",
        "rules": {
            "3.1": "Extrajudicial Activities in General",
            "3.5": "Use of Nonpublic Information",
            "3.10": "Practice of Law",
            "3.11": "Financial, Business, or Remunerative Activities",
            "3.13": "Acceptance and Reporting of Gifts",
        },
    },
    "Canon 4": {
        "title": "Political and Campaign Activities",
        "text": "A judge or candidate for judicial office shall not engage in political or campaign activity inconsistent with independence, integrity, or impartiality.",
        "citation": "SC Code of Judicial Conduct, Canon 4",
    },
}

SC_CUSTODY_FACTORS = {
    "citation": "SC Code Ann. 63-15-240",
    "title": "Best Interest of the Child Factors (SC Code 63-15-240)",
    "factors": {
        1: "The temperament and developmental needs of the child",
        2: "The capacity and disposition of each parent to understand and meet the child's needs",
        3: "The preferences of each child (if age-appropriate)",
        4: "The wishes of the parents as to custody",
        5: "The past and current interaction and relationship of the child with each parent, siblings, and others who may significantly affect the child's best interest",
        6: "The actions of each parent to encourage the ongoing relationship of the child with the other parent (friendly parent provision)",
        7: "The manipulation by or coercive behavior of a parent in an effort to involve the child in the parents' dispute",
        8: "Any effort by one parent to disparage the other parent in the presence of the child",
        9: "The ability of each parent to be actively involved in the life of the child",
        10: "The child's adjustment to home, school, and community environments",
        11: "The mental and physical health of all individuals involved, except disability alone shall not be a basis to deny custody",
        12: "The child's cultural and spiritual background",
        13: "Whether the child or a sibling has been abused or neglected",
        14: "Whether one parent has perpetrated domestic violence or child abuse",
        15: "The nature and extent of each parent's involvement in the child's life before separation",
        16: "Which parent is more likely to encourage frequent, meaningful, and continuing contact with the other parent",
        17: "Whether a parent has relocated or plans to relocate more than 100 miles from the current primary residence of the child",
    },
}

SC_SUPREME_COURT_365 = {
    "title": "SC Supreme Court Administrative Order: 365-Day Rule",
    "citation": "SC Supreme Court Administrative Order (Rule 365)",
    "text": ("Family court cases should be resolved within 365 days from the date of filing. "
             "Extensions may be granted for good cause shown. Cases exceeding 365 days "
             "without resolution or extension are in non-compliance."),
    "filing_to_resolution_limit_days": 365,
    "extension_grounds": [
        "Complexity of issues",
        "Number of parties",
        "Pending related proceedings",
        "Good cause shown by motion",
        "Continuance granted by court",
    ],
    "non_compliance_consequences": [
        "Case reported to Chief Justice",
        "Required status conference",
        "Mandatory case management order",
        "Potential judicial reassignment",
    ],
}

UCCJEA = {
    "title": "Uniform Child Custody Jurisdiction and Enforcement Act",
    "sc_citation": "SC Code Ann. 63-15-300 et seq.",
    "federal_citation": "Pub. L. 105-310 (UCCJEA); 28 USC 1738A (PKPA)",
    "sections": {
        "201": {
            "title": "Initial Child Custody Jurisdiction",
            "text": ("A court has jurisdiction to make an initial custody determination "
                     "only if: (1) this state is the home state of the child on the date of "
                     "commencement, or was the home state within 6 months before and the child "
                     "is absent but a parent continues to reside; (2) no other state has home "
                     "state jurisdiction; (3) all states having jurisdiction have declined; "
                     "(4) no state has jurisdiction."),
            "citation": "SC Code Ann. 63-15-332 / UCCJEA Section 201",
        },
        "202": {
            "title": "Exclusive Continuing Jurisdiction",
            "text": ("A court that made initial custody determination retains exclusive "
                     "continuing jurisdiction until: (1) the court determines neither the "
                     "child nor a parent has significant connection with the state AND "
                     "substantial evidence is no longer available; or (2) the court or a "
                     "court of another state determines neither the child nor parent resides "
                     "in this state."),
            "citation": "SC Code Ann. 63-15-334 / UCCJEA Section 202",
        },
        "203": {
            "title": "Jurisdiction to Modify Determination",
            "text": ("A court may not modify another state's custody determination unless "
                     "it has jurisdiction under 201 AND the original court determines it no "
                     "longer has exclusive continuing jurisdiction OR a court of this state "
                     "would be a more convenient forum."),
            "citation": "SC Code Ann. 63-15-336 / UCCJEA Section 203",
        },
        "204": {
            "title": "Temporary Emergency Jurisdiction",
            "text": ("A court has temporary emergency jurisdiction if the child is present "
                     "in this state and has been subjected to or threatened with mistreatment "
                     "or abuse, or the child's parent is subjected to domestic violence."),
            "citation": "SC Code Ann. 63-15-338 / UCCJEA Section 204",
        },
        "207": {
            "title": "Inconvenient Forum",
            "text": ("A court may decline jurisdiction if it determines it is an inconvenient "
                     "forum and a court of another state is a more appropriate forum."),
            "citation": "SC Code Ann. 63-15-344 / UCCJEA Section 207",
        },
        "208": {
            "title": "Jurisdiction Declined by Reason of Conduct",
            "text": ("If a court determines a party has engaged in unjustifiable conduct "
                     "to create jurisdiction, the court may decline to exercise jurisdiction."),
            "citation": "SC Code Ann. 63-15-346 / UCCJEA Section 208",
        },
    },
    "home_state_definition": (
        "The state in which a child lived with a parent for at least 6 consecutive "
        "months immediately before commencement of the custody proceeding. "
        "A period of temporary absence is counted as part of the period."
    ),
}

CONSTITUTIONAL_RIGHTS = {
    "1st_Amendment": {
        "right": "Freedom of Speech and Petition",
        "text": "Right to petition the government for redress of grievances.",
        "citation": "U.S. Const. amend. I",
        "family_court_application": "Right to file motions and present arguments without retaliation.",
    },
    "4th_Amendment": {
        "right": "Freedom from Unreasonable Search",
        "text": "Right to be secure against unreasonable searches and seizures.",
        "citation": "U.S. Const. amend. IV",
        "family_court_application": "Protection against invasive discovery or surveillance orders.",
    },
    "5th_Amendment": {
        "right": "Due Process (Federal)",
        "text": "No person shall be deprived of life, liberty, or property without due process of law.",
        "citation": "U.S. Const. amend. V",
        "family_court_application": "Fundamental parental rights are liberty interests requiring due process.",
    },
    "6th_Amendment": {
        "right": "Right to Confront Witnesses",
        "text": "Right to be confronted with witnesses and to compulsory process.",
        "citation": "U.S. Const. amend. VI",
        "family_court_application": "Right to cross-examine GAL, evaluators, and adverse witnesses.",
    },
    "14th_Amendment_Due_Process": {
        "right": "Due Process (State Action)",
        "text": "No state shall deprive any person of life, liberty, or property without due process.",
        "citation": "U.S. Const. amend. XIV, Sec. 1",
        "family_court_application": (
            "Parental rights are fundamental liberty interests. "
            "Troxel v. Granville, 530 U.S. 57 (2000); Santosky v. Kramer, 455 U.S. 745 (1982)."
        ),
    },
    "14th_Amendment_Equal_Protection": {
        "right": "Equal Protection",
        "text": "No state shall deny any person equal protection of the laws.",
        "citation": "U.S. Const. amend. XIV, Sec. 1",
        "family_court_application": "Gender-based custody presumptions violate equal protection.",
    },
    "SC_Const_Art_I_Sec_3": {
        "right": "SC Due Process",
        "text": "No person shall be deprived of life, liberty, or property without due process of law.",
        "citation": "SC Const. Art. I, Sec. 3",
        "family_court_application": "State-level due process protections in family court.",
    },
    "SC_Const_Art_I_Sec_14": {
        "right": "SC Open Courts",
        "text": "Every person shall have remedy by due course of law for injury to lands, goods, person, or reputation.",
        "citation": "SC Const. Art. I, Sec. 14",
        "family_court_application": "Right of access to courts and meaningful hearing.",
    },
}

FRAUD_INDICATORS = {
    "false_statements": {
        "label": "False Statements to Court",
        "keywords": [
            "false", "fabricated", "lied", "perjury", "misrepresent",
            "not true", "falsely", "made up", "untrue", "fraudulent",
            "sworn falsely", "false affidavit", "false testimony",
        ],
        "severity": "CRITICAL",
        "legal_basis": "SC Rules of Civil Procedure, Rule 60(b)(3); SC Code 16-9-10 (Perjury)",
    },
    "concealed_facts": {
        "label": "Concealment of Material Facts",
        "keywords": [
            "concealed", "hidden", "withheld", "failed to disclose",
            "omitted", "did not reveal", "suppressed", "undisclosed",
            "not disclosed", "hid", "covered up",
        ],
        "severity": "HIGH",
        "legal_basis": "SC Rules of Civil Procedure, Rule 60(b)(3); Rule 26 Discovery Obligations",
    },
    "fabricated_evidence": {
        "label": "Fabricated or Altered Evidence",
        "keywords": [
            "fabricated", "altered", "forged", "tampered",
            "manufactured", "doctored", "fake", "falsified document",
            "altered evidence", "planted", "staged",
        ],
        "severity": "CRITICAL",
        "legal_basis": "SC Code 16-9-410 (Forgery); Rule 60(b)(3)",
    },
    "witness_tampering": {
        "label": "Witness Tampering or Intimidation",
        "keywords": [
            "witness tampering", "intimidated witness", "coerced testimony",
            "threatened witness", "bribed witness", "coached witness",
            "suborned perjury", "pressured to testify",
        ],
        "severity": "CRITICAL",
        "legal_basis": "SC Code 16-9-340 (Obstruction of Justice)",
    },
    "income_hiding": {
        "label": "Income or Asset Concealment",
        "keywords": [
            "hidden income", "unreported income", "hidden assets",
            "undisclosed account", "offshore", "shell company",
            "cash payments", "under the table", "cryptocurrency hidden",
        ],
        "severity": "HIGH",
        "legal_basis": "SC Code 20-3-130 (Financial Declarations); Rule 26",
    },
    "false_abuse_allegations": {
        "label": "False Allegations of Abuse",
        "keywords": [
            "false allegation", "fabricated abuse", "false report",
            "unfounded allegation", "made up abuse", "false accusation",
            "malicious prosecution", "weaponized cps",
        ],
        "severity": "CRITICAL",
        "legal_basis": "SC Code 63-7-440 (False Reports); SC Code 16-17-720",
    },
    "procedural_fraud": {
        "label": "Procedural Fraud on the Court",
        "keywords": [
            "fraud on the court", "fraud upon the court",
            "deceived the court", "misled the court", "improper service",
            "fake service", "sham filing", "collusion",
        ],
        "severity": "CRITICAL",
        "legal_basis": "Rule 60(b)(3); Inherent court authority to address fraud",
    },
}

DISMISSAL_GROUNDS = {
    "lack_of_jurisdiction": {
        "label": "Lack of Subject Matter Jurisdiction",
        "description": "Court lacks jurisdiction under UCCJEA or other basis.",
        "citation": "SC Code Ann. 63-15-332; UCCJEA Sec. 201",
        "applicable_when": [
            "Child's home state is another state",
            "No significant connection to South Carolina",
            "Another state has exclusive continuing jurisdiction",
            "Neither child nor parent resides in SC",
        ],
    },
    "lack_of_personal_jurisdiction": {
        "label": "Lack of Personal Jurisdiction",
        "description": "Court lacks jurisdiction over a party.",
        "citation": "SC Code 36-2-803 (Long-Arm Statute); Due Process",
        "applicable_when": [
            "Non-resident party with insufficient SC contacts",
            "Improper service of process",
        ],
    },
    "improper_venue": {
        "label": "Improper Venue",
        "description": "Case filed in wrong county.",
        "citation": "SC Code 63-3-530",
        "applicable_when": [
            "Neither party resides in filing county",
            "Child does not reside in filing county",
        ],
    },
    "failure_to_prosecute": {
        "label": "Failure to Prosecute / 365-Day Rule",
        "description": "Case not prosecuted within required timeframe.",
        "citation": "SC Supreme Court Administrative Order; Rule 41(b)",
        "applicable_when": [
            "Case exceeds 365 days without resolution",
            "No activity for extended period",
            "Failure to comply with case management orders",
        ],
    },
    "res_judicata": {
        "label": "Res Judicata / Claim Preclusion",
        "description": "Same claim already adjudicated between same parties.",
        "citation": "Common law; Plum Creek Dev. Co. v. City of Conway, 334 SC 30 (1999)",
        "applicable_when": [
            "Prior final judgment on same issues",
            "Same parties or privies",
            "Relitigation of settled matters",
        ],
    },
    "mootness": {
        "label": "Mootness",
        "description": "No live controversy remains.",
        "citation": "SC Const. Art. V; Curtis v. State, 345 SC 557 (2001)",
        "applicable_when": [
            "Child has aged out",
            "Parties have resolved issues",
            "Relief sought is no longer possible",
        ],
    },
    "standing": {
        "label": "Lack of Standing",
        "description": "Filing party lacks standing to bring action.",
        "citation": "SC Code 63-15-10 et seq.",
        "applicable_when": [
            "Non-parent filing without statutory authority",
            "GAL exceeding scope of authority",
        ],
    },
    "fraud_on_court": {
        "label": "Fraud on the Court",
        "description": "Opposing party obtained orders through fraud.",
        "citation": "Rule 60(b)(3); Inherent authority",
        "applicable_when": [
            "False statements in pleadings",
            "Concealed material facts",
            "Fabricated evidence",
            "Perjured testimony",
        ],
    },
    "uccjea_home_state": {
        "label": "UCCJEA Home State Jurisdiction Failure",
        "description": "SC is not the home state under UCCJEA.",
        "citation": "SC Code Ann. 63-15-332; UCCJEA Sec. 201",
        "applicable_when": [
            "Child lived in another state for 6+ months before filing",
            "Child relocated and established home state elsewhere",
            "No parent remains in SC with significant connection",
        ],
    },
}
