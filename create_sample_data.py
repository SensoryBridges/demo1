#!/usr/bin/env python3
"""
Generate sample input data to demonstrate the analysis tool.
Creates sample Excel workbook with realistic sheet structures.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

def create_sample_data(output_dir="input"):
    os.makedirs(output_dir, exist_ok=True)

    # --- Sheet 1: Post-Separation Abuse Incidents ---
    n_incidents = 60
    base_date = datetime(2021, 3, 15)
    dates = sorted([base_date + timedelta(days=int(x)) for x in
                    np.cumsum(np.random.exponential(18, n_incidents))])

    behaviors = [
        "Filed emergency motion without emergency basis, threatening custody loss",
        "Monitored movements via GPS tracker on vehicle",
        "Refused to return children at scheduled custody exchange time",
        "Sent 47 harassing text messages in one day, verbal degradation",
        "Filed contempt motion - third time for same alleged violation, denied twice before",
        "Showed up unannounced at workplace, contacting employer",
        "Hid financial documents, refused discovery compliance",
        "Made false allegations to CPS, using children as leverage",
        "Social media monitoring, cyberstalking, contacted friends",
        "Filed motion to reduce parenting time with no changed circumstances",
        "Drove by residence 3 times in one evening, physical following",
        "Depleted joint savings account without authorization",
        "Interrogated children about other parent's activities after each visit",
        "Gaslighting - denied documented events, blame shifting",
        "Threatened to file bankruptcy to avoid support obligations",
        "Demanded excessive compliance with unreasonable parenting schedule",
        "Filed frivolous discovery requests to increase legal costs",
        "Public humiliation at school event in front of children",
        "Used third parties to monitor and relay information",
        "Emergency motion filed day before holiday visitation",
        "Alcohol abuse present during custody time, erratic behavior",
        "Blocked exits during custody exchange, physical intimidation",
        "Refused to negotiate parenting plan, weaponizing court system",
        "Filed vexatious motion, misrepresentation to court about income",
        "Isolated from support network, controlling communications",
    ]

    severity = np.clip(np.random.normal(5, 2.5, n_incidents) + np.linspace(0, 2, n_incidents), 0, 10)

    abuse_df = pd.DataFrame({
        "date": dates[:n_incidents],
        "behavior_description": [behaviors[i % len(behaviors)] for i in range(n_incidents)],
        "severity_score": np.round(severity, 1),
        "evidence_type": np.random.choice(
            ["text_message", "email", "witness", "police_report", "court_record",
             "photo", "video", "voicemail", "social_media", "bank_record"],
            n_incidents
        ),
        "evidence_strength": np.round(np.random.uniform(0.3, 1.0, n_incidents), 2),
        "children_present": np.random.choice(["yes", "no"], n_incidents, p=[0.4, 0.6]),
        "substance_use_noted": np.random.choice(["none", "alcohol", "suspected"], n_incidents, p=[0.6, 0.25, 0.15]),
        "police_called": np.random.choice(["yes", "no"], n_incidents, p=[0.15, 0.85]),
        "court_date_proximity": np.random.randint(0, 60, n_incidents),
        "link": "",  # Placeholder for Google Drive links
    })

    # --- Sheet 2: Court Filings / Docket ---
    n_filings = 85
    filing_dates = sorted([base_date + timedelta(days=int(x)) for x in
                          np.cumsum(np.random.exponential(14, n_filings))])

    filing_types = [
        "Petition for Dissolution", "Response to Petition", "Motion for Temporary Orders",
        "Emergency Motion - Custody", "Motion for Contempt", "Response to Contempt",
        "Motion to Compel Discovery", "Motion for Continuance", "GAL Appointment",
        "Motion to Modify Custody", "Motion for Psychological Evaluation",
        "Motion for Attorney Fees", "Pre-Trial Conference", "Hearing - Contempt",
        "Hearing - Custody", "Mediation Session", "Trial Date - Day 1",
        "Motion for Reconsideration", "Notice of Appeal", "Emergency Motion - Support",
        "Motion to Restrict Parenting Time", "Motion for Supervised Visitation",
        "Response to Motion to Modify", "Hearing - Support", "Status Conference",
    ]

    judges = ["Hon. Robert Mitchell", "Hon. Robert Mitchell", "Hon. Robert Mitchell",
              "Hon. Sarah Patterson", "Hon. Robert Mitchell"]
    attorneys_pet = ["James Hartwell, Esq.", "James Hartwell, Esq."]
    attorneys_resp = ["Patricia Knowles, Esq.", "Patricia Knowles, Esq.", "Diana Reeves, Esq."]
    gals = ["Dr. Karen Whitfield", "Dr. Karen Whitfield"]

    filings_df = pd.DataFrame({
        "date": filing_dates[:n_filings],
        "type": [filing_types[i % len(filing_types)] for i in range(n_filings)],
        "filed_by": np.random.choice(["Petitioner", "Respondent", "Court", "GAL"], n_filings,
                                      p=[0.35, 0.35, 0.2, 0.1]),
        "judge": [np.random.choice(judges) for _ in range(n_filings)],
        "attorney_petitioner": [np.random.choice(attorneys_pet) for _ in range(n_filings)],
        "attorney_respondent": [np.random.choice(attorneys_resp) for _ in range(n_filings)],
        "guardian_ad_litem": [np.random.choice(gals) if np.random.random() > 0.3 else "" for _ in range(n_filings)],
        "outcome": np.random.choice(
            ["Granted", "Denied", "Continued", "Settled", "Pending", "Partially Granted",
             "Dismissed", "Sustained", "Overruled", "No Ruling"],
            n_filings
        ),
        "description": [f"Filing #{i+1} — {filing_types[i % len(filing_types)]}" for i in range(n_filings)],
        "link": "",
    })

    # --- Sheet 3: Court Officials ---
    officials_df = pd.DataFrame({
        "name": ["Hon. Robert Mitchell", "Hon. Sarah Patterson", "James Hartwell, Esq.",
                 "Patricia Knowles, Esq.", "Diana Reeves, Esq.", "Dr. Karen Whitfield",
                 "Mark Sullivan", "Janet Crawford"],
        "role": ["Judge", "Judge", "Attorney (Petitioner)", "Attorney (Respondent)",
                 "Attorney (Respondent)", "Guardian ad Litem", "Mediator",
                 "Custody Evaluator"],
        "law_firm": ["", "", "Hartwell & Associates", "Knowles Family Law",
                     "Reeves Legal Group", "Whitfield Consulting", "Sullivan Mediation",
                     "Crawford Psychology"],
        "university": ["State University Law", "State University Law", "State University Law",
                       "Metro Law School", "State University Law", "State University",
                       "Metro University", "State University"],
        "bar_association": ["County Bar", "County Bar", "County Bar",
                           "County Bar", "State Bar", "N/A", "N/A", "N/A"],
        "years_experience": [22, 15, 18, 12, 8, 14, 10, 16],
    })

    # --- Sheet 4: Financial Records ---
    n_financial = 40
    financial_df = pd.DataFrame({
        "date": sorted(np.random.choice(filing_dates[:n_filings], n_financial)),
        "amount": np.round(np.random.lognormal(7, 1, n_financial), 2),
        "paid_by": np.random.choice(["Petitioner", "Respondent", "Joint"], n_financial,
                                     p=[0.45, 0.45, 0.1]),
        "paid_to": np.random.choice(
            ["James Hartwell, Esq.", "Patricia Knowles, Esq.", "Diana Reeves, Esq.",
             "Dr. Karen Whitfield", "Mark Sullivan", "Janet Crawford",
             "Court Filing Fees", "Process Server"],
            n_financial
        ),
        "description": np.random.choice(
            ["Attorney fees", "GAL fees", "Mediation fees", "Evaluation fees",
             "Court costs", "Filing fees", "Deposition costs", "Expert witness"],
            n_financial
        ),
    })

    # --- Write to Excel ---
    filepath = os.path.join(output_dir, "case_data_sample.xlsx")
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        abuse_df.to_excel(writer, sheet_name="Post Separation Abuse", index=False)
        filings_df.to_excel(writer, sheet_name="Court Filings", index=False)
        officials_df.to_excel(writer, sheet_name="Court Officials", index=False)
        financial_df.to_excel(writer, sheet_name="Financial Records", index=False)

    print(f"Sample data created: {filepath}")
    print(f"  - Post Separation Abuse: {len(abuse_df)} rows")
    print(f"  - Court Filings: {len(filings_df)} rows")
    print(f"  - Court Officials: {len(officials_df)} rows")
    print(f"  - Financial Records: {len(financial_df)} rows")

    return filepath


if __name__ == "__main__":
    create_sample_data()
