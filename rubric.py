"""
rubric.py
---------
Defines the explicit 4-factor scoring rubric, deterministic fallback evaluation, 
and personalized outreach message generator.
"""

import pandas as pd
import random
from datetime import datetime

def evaluate_lead_rubric(row, reference_date):
    """
    Evaluates a single lead row against our 4-factor business rubric:
    1. Company Size Fit (3 pts max)
    2. Industry Alignment (3 pts max)
    3. Lead Source / Intent (2 pts max)
    4. Interaction Recency (2 pts max)
    """
    score = 0.0
    reasoning = []
    
    # 1. Company Size Fit (3 points max) - Target: 11 - 5000 employees
    size = row.get('company_size')
    if pd.isna(size) or str(size).strip().upper() in ['NA', '', 'NONE']:
        reasoning.append("Missing company size (0 pts)")
    else:
        try:
            s_val = float(size)
            if 11 <= s_val <= 5000:
                score += 3.0
                reasoning.append(f"Company size {int(s_val)} is in target SMB/Mid-market range (3 pts)")
            else:
                score += 1.0
                reasoning.append(f"Company size {int(s_val)} is outside target range (1 pt)")
        except ValueError:
            reasoning.append("Invalid company size format (0 pts)")

    # 2. Industry Alignment (3 points max)
    industry = str(row.get('industry', '')).strip().title()
    tier1_industries = ['Saas', 'Software', 'Finance', 'Fintech', 'Healthcare', 'Cybersecurity', 'Analytics']
    tier2_industries = ['Retail', 'Logistics', 'Manufacturing', 'Edtech', 'Consulting', 'Insurance', 'Supply Chain', 'Energy']
    
    if not industry or industry == 'Nan':
        reasoning.append("Missing industry (0 pts)")
    elif industry in tier1_industries:
        score += 3.0
        reasoning.append(f"Industry '{industry}' is Tier-1 high fit (3 pts)")
    elif industry in tier2_industries:
        score += 2.0
        reasoning.append(f"Industry '{industry}' is Tier-2 moderate fit (2 pts)")
    else:
        score += 1.0
        reasoning.append(f"Industry '{industry}' is Tier-3 niche/other (1 pt)")

    # 3. Lead Source / Intent (2 points max)
    source = str(row.get('source', '')).strip().title()
    high_intent = ['Inbound Demo Request', 'Referral', 'Sales Call']
    med_intent = ['Content Download', 'Webinar Attendee']
    
    if any(hi in source for hi in high_intent):
        score += 2.0
        reasoning.append(f"Source '{source}' is high intent (2 pts)")
    elif any(mi in source for mi in med_intent):
        score += 1.0
        reasoning.append(f"Source '{source}' is medium intent (1 pt)")
    else:
        score += 0.5
        reasoning.append(f"Source '{source}' is low intent/cold (0.5 pts)")

    # 4. Interaction Recency (2 points max)
    date_str = str(row.get('last_interaction_date', '')).strip()
    try:
        dt = pd.to_datetime(date_str)
        days_ago = (reference_date - dt).days
        if days_ago <= 60:
            score += 2.0
            reasoning.append(f"Interaction {days_ago} days ago is very recent (2 pts)")
        elif days_ago <= 180:
            score += 1.0
            reasoning.append(f"Interaction {days_ago} days ago is moderately aged (1 pt)")
        else:
            score += 0.0
            reasoning.append(f"Interaction {days_ago} days ago is stale (>6 months) (0 pts)")
    except Exception:
        reasoning.append("Invalid or missing interaction date (0 pts)")

    # Final Decision & Routing
    has_missing = pd.isna(row.get('company_size')) or pd.isna(row.get('industry')) or pd.isna(row.get('source')) or pd.isna(row.get('last_interaction_date'))
    
    if score >= 7.0 and not has_missing:
        decision, priority = "QUALIFIED", "HIGH"
    elif score >= 4.0:
        decision, priority = "REVIEW", "MEDIUM"
    else:
        decision, priority = "REJECTED", "LOW"

    # Generate outreach message if qualified
    name = str(row.get('name', 'there')) if pd.notna(row.get('name')) else 'there'
    company = str(row.get('company', 'your company')) if pd.notna(row.get('company')) else 'your company'
    ind = industry if industry and industry != 'Nan' else 'technology'
    source_lower = source.lower()
    
    hook = "Following up on your recent demo request," if 'demo' in source_lower else "I came across your profile and"
    outreach = f"Hi {name}, {hook} I noticed {company} is making strong moves in {ind}. We help growing teams automate workflows and boost output. Open to a 10-minute intro call?" if decision == "QUALIFIED" else ""

    return {
        "name": name,
        "company": company,
        "company_size": row.get('company_size') if pd.notna(row.get('company_size')) else "N/A",
        "industry": ind,
        "source": source,
        "score": round(score, 1),
        "decision": decision,
        "priority": priority,
        "reasoning": "; ".join(reasoning),
        "outreach_message": outreach
    }