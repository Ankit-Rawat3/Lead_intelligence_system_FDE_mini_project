"""
llm_evaluator.py
----------------
Handles batched lead evaluation using Google Gemini SDK.
"""

import os
import json
import pandas as pd

try:
    from google import genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

def evaluate_leads_batch_llm(batch_records, reference_date, provider="gemini"):
    """
    Evaluates a batch of leads using Google Gemini.
    """
    if not GOOGLE_GENAI_AVAILABLE or not os.environ.get("GEMINI_API_KEY"):
        print("[LLM Warning] Google GenAI SDK or GEMINI_API_KEY is missing.")
        return None

    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        prompt = (
            "You are a B2B sales operations expert. Evaluate this batch of leads against our rubric: "
            "1. Company size 11-5000 is ideal. 2. Tier-1 industries (SaaS, FinTech, Healthcare, Cybersecurity) score highest. "
            "3. Inbound demo requests and referrals are high intent. 4. Recent interactions score higher (Ref date: " + str(reference_date) + "). "
            "Return valid JSON with key 'leads' containing an array of objects with: 'name', 'company', 'company_size', 'industry', 'source', "
            "'score' (float 1-10), 'decision' (QUALIFIED, REVIEW, REJECTED), 'priority' (HIGH, MEDIUM, LOW), 'reasoning', and 'outreach_message'. "
            "Leads Data: " + json.dumps(batch_records)
        )
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'},
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        data = json.loads(text)
        results = data.get("leads", data.get("results", data if isinstance(data, list) else []))
        return results if results else None
    except Exception as e:
        print(f"[LLM Warning] Gemini evaluation failed: {e}")
        return None