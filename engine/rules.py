import re
from typing import List, Dict, Any

RISK_RULES: List[Dict[str, Any]] = [
    {
        "id": "UNILATERAL_RATE_HIKE",
        "title": "Unilateral Interest Rate / Fee Revision",
        "severity": "HIGH",
        "weight": 30,
        "pattern": r"(?i)(lender|company|bank)\s+(reserves\s+the\s+right\s+to|may|shall\s+have\s+the\s+sole\s+discretion\s+to)\s+(modify|revise|increase|alter|change)\s+[\w\s,]{0,40}?(interest\s+rate|rate\s+of\s+interest|fees|charges)\s+(at\s+any\s+time|without\s+prior\s+notice)",
        "explanation": "Allows the lender to raise your interest rate or fees unilaterally without prior notice or consent.",
        "recommendation": "Demand a 30-day advance written notice clause and tie rate changes strictly to an external benchmark (e.g., RBI Repo Rate)."
    },
    {
        "id": "AUTO_DEBIT_WAIVER",
        "title": "Irrevocable Auto-Debit / NACH Mandate",
        "severity": "HIGH",
        "weight": 25,
        "pattern": r"(?i)(irrevocable|unconditional)\s+(authorization|consent|mandate|right)\s+to\s+(debit|deduct|withdraw)\s+[\w\s,]{0,35}?from\s+(any|all)\s+(bank\s+)?account",
        "explanation": "Grants blanket, irrevocable permission to pull funds from any of your accounts, making it hard to stop disputed deductions.",
        "recommendation": "Restrict auto-debit strictly to your designated loan EMI account and preserve your statutory right to revoke the mandate."
    },
    {
        "id": "FORECLOSURE_PENALTY",
        "title": "Heavy Prepayment / Foreclosure Penalty",
        "severity": "MEDIUM",
        "weight": 20,
        "pattern": r"(?i)(prepayment|foreclosure|early\s+settlement)\s+(penalty|charge|fee)\s+of\s+(\d+(\.\d+)?%|\w+\s+percent)",
        "explanation": "Penalizes you for paying off your loan early. Note: RBI guidelines prohibit foreclosure penalties on floating-rate individual loans.",
        "recommendation": "Request zero foreclosure charges after 6–12 months, or verify exemption if this is a floating-rate personal/home loan."
    },
    {
        "id": "HIDDEN_DATA_SHARING",
        "title": "Broad Third-Party Data & Contact Sharing",
        "severity": "HIGH",
        "weight": 25,
        "pattern": r"(?i)(share|disclose|transfer)\s+[\w\s,]{0,35}?(borrower|user|personal|contact\s+list|phone)\s+(data|information|details)\s+with\s+(third\s+parties|affiliates|marketing\s+partners|recovery\s+agents|collection\s+agencies)",
        "explanation": "Permits sharing your personal data or phone contacts with third-party marketers or aggressive recovery agencies.",
        "recommendation": "Limit data sharing strictly to credit bureaus (CIBIL/Experian) and statutory regulators as required by law."
    },
    {
        "id": "CROSS_DEFAULT_CLAUSE",
        "title": "Cross-Default Trigger",
        "severity": "MEDIUM",
        "weight": 15,
        "pattern": r"(?i)(default\s+under\s+any\s+other\s+(agreement|loan|facility)|cross[\s-]default)",
        "explanation": "A minor delay on an unrelated account can automatically put this entire loan into default and trigger immediate full repayment.",
        "recommendation": "Narrow this clause so default only applies to material payment failures on this specific agreement."
    },
    {
        "id": "UNILATERAL_ARBITRATION",
        "title": "Lender-Appointed Sole Arbitrator / Distant Venue",
        "severity": "MEDIUM",
        "weight": 15,
        "pattern": r"(?i)(sole\s+arbitrator\s+(appointed|nominated)\s+by\s+the\s+(lender|company|bank)|jurisdiction\s+exclusively\s+at\s+\w+)",
        "explanation": "Forces disputes into arbitration where the lender picks the arbitrator or sets a distant city as the sole legal venue.",
        "recommendation": "Insist on mutual appointment of an independent arbitrator and local court jurisdiction in your city of residence."
    }
]


def analyze_contract(text: str) -> Dict[str, Any]:
    """Scans contract text against deterministic regex rules and computes a risk score."""
    findings = []
    total_penalty = 0

    paragraphs = [p.strip() for p in re.split(r"\n+", text) if p.strip()]

    for rule in RISK_RULES:
        regex = re.compile(rule["pattern"])
        for idx, para in enumerate(paragraphs, start=1):
            match = regex.search(para)
            if match:
                total_penalty += rule["weight"]
                findings.append({
                    "rule_id": rule["id"],
                    "title": rule["title"],
                    "severity": rule["severity"],
                    "weight": rule["weight"],
                    "clause_number": idx,
                    "matched_phrase": match.group(0),
                    "clause_text": para,
                    "explanation": rule["explanation"],
                    "recommendation": rule["recommendation"]
                })
                break

    risk_score = min(100, total_penalty)
    if risk_score >= 60:
        risk_level = "CRITICAL"
    elif risk_score >= 30:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "total_clauses_scanned": len(paragraphs),
        "flags_count": len(findings),
        "findings": findings
    }