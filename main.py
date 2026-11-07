"""
main.py
-------
Command-line entry point supporting Gemini LLM or Normal Rubric execution modes:
--mode gemini  => Google Gemini LLM evaluation -> output_gemini.json
--mode rubric  => Local deterministic rubric -> output_normal.json
"""

import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime

from rubric import evaluate_lead_rubric
from llm_evaluator import evaluate_leads_batch_llm

def process_pipeline(csv_path, output_path, mode):
    if not os.path.exists(csv_path):
        print(f"Error: Input CSV file '{csv_path}' not found.")
        sys.exit(1)

    print(f"[Ingest] Loading leads from: {csv_path}")
    df = pd.read_csv(csv_path)
    df['parsed_date'] = pd.to_datetime(df['last_interaction_date'], errors='coerce')
    ref_date = df['parsed_date'].max() if pd.notna(df['parsed_date'].max()) else datetime.now()

    results = []
    evaluation_mode_used = "Deterministic Rubric"

    if mode == "gemini":
        print("[GEMINI] Attempting batch evaluation via Google Gemini...")
        records = df.to_dict(orient='records')
        batch_size = 20
        success = True
        
        for i in range(0, len(records), batch_size):
            chunk = records[i:i+batch_size]
            clean_chunk = [{k: (v if pd.notna(v) else None) for k, v in r.items() if k != 'parsed_date'} for r in chunk]
            
            try:
                gemini_res = evaluate_leads_batch_llm(clean_chunk, ref_date.date() if hasattr(ref_date, 'date') else ref_date, provider="gemini")
                if gemini_res:
                    results.extend(gemini_res)
                else:
                    success = False
                    break
            except Exception as e:
                print(f"[Error] Gemini batch failed: {e}")
                success = False
                break

        if success and len(results) == len(df):
            evaluation_mode_used = "LLM (GEMINI)"
        else:
            print("[Fallback] Gemini evaluation failed or incomplete. Falling back to deterministic rubric scoring...")
            results = []
            mode = "rubric"

    if mode == "rubric":
        print("[Rubric] Running local deterministic rubric evaluation...")
        for _, row in df.iterrows():
            results.append(evaluate_lead_rubric(row, ref_date))
        evaluation_mode_used = "Deterministic Rubric"

    # Calculate summary statistics
    qualified_count = sum(1 for r in results if str(r.get('decision')).upper() == 'QUALIFIED')
    review_count = sum(1 for r in results if str(r.get('decision')).upper() == 'REVIEW')
    rejected_count = sum(1 for r in results if str(r.get('decision')).upper() == 'REJECTED')

    report = {
        "metadata": {
            "processed_timestamp": datetime.now().isoformat(),
            "source_csv": csv_path,
            "total_records": len(df),
            "evaluation_mode": evaluation_mode_used
        },
        "summary": {
            "total_leads": len(df),
            "qualified": qualified_count,
            "review": review_count,
            "rejected": rejected_count,
            "qualified_percentage": round((qualified_count / len(df)) * 100, 1) if len(df) > 0 else 0.0
        },
        "sample_outreach_messages": [r.get('outreach_message', '') for r in results if r.get('outreach_message')][:5],
        "leads": results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[Export] Pipeline execution complete ({evaluation_mode_used}).")
    print(f"[Export] Report successfully saved to: {output_path}")
    print(f"Summary: Total={len(df)} | Qualified={qualified_count} | Review={review_count} | Rejected={rejected_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Lead Intelligence System CLI")
    parser.add_argument("--csv", default="leads_training.csv", help="Path to input CSV file")
    parser.add_argument("--output", default="output_report.json", help="Path to output JSON report")
    parser.add_argument("--mode", default="rubric", choices=["rubric", "gemini"], help="Execution mode")
    args = parser.parse_args()

    process_pipeline(args.csv, args.output, args.mode)