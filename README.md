# Lead Intelligence System

A lightweight, standalone CLI system designed to auto-qualify inbound B2B sales leads, sequence personalized outreach messages, and generate actionable summary reports. It supports both a local, deterministic rule-based scoring engine and AI-driven batched evaluation powered by Google Gemini (`gemini-3.8-flash`).

---

## 📌 Architecture Overview

The system follows a clean 3-file modular architecture:

```
Lead_intelligence_system/
├── main.py           # CLI entry point, dataset ingestion, orchestration, output generation
├── rubric.py         # Deterministic 4-factor scoring rubric & fallback message generator
└── llm_evaluator.py  # Google Gemini LLM batch processing integration (batch size = 25)
```

### Module Responsibilities
* **`main.py`**: Handles command-line argument parsing (`--csv`, `--output`, `--mode`), reads incoming datasets via `pandas`, routes records to either the LLM batch engine or local rubric, and outputs formatted JSON reports.
* **`rubric.py`**: Contains deterministic business logic evaluating 4 core qualification factors (Company Size, Industry Alignment, Source Intent, Interaction Recency). Serves as a standalone evaluation mode and a zero-downtime fallback mechanism if API calls fail.
* **`llm_evaluator.py`**: Manages batched API requests to Google Gemini using the `google-genai` SDK, passing leads in chunks of 25 to optimize rate limits and response speed.

---

## 🎯 Qualification Rubric (4-Factor Model)

Leads are scored on a scale of **0.0 to 10.0** based on the following criteria:

1. **Company Size Fit (Max 3.0 pts):**
   * Target SMB/Mid-market (11–5,000 employees): `+3.0 pts`
   * Enterprise (>5,000 employees) or Solopreneur/Startup (<11 employees): `+1.0 pt`
   * Missing / Invalid size: `0.0 pts`

2. **Industry Alignment (Max 3.0 pts):**
   * **Tier-1 Fit** (SaaS, FinTech, Healthcare, Cybersecurity, Analytics, Software, Finance): `+3.0 pts`
   * **Tier-2 Fit** (Retail, Logistics, Manufacturing, EdTech, Consulting, Insurance, Supply Chain, Energy): `+2.0 pts`
   * **Tier-3 / Other** (Niche or non-core verticals): `+1.0 pt`

3. **Source Intent (Max 2.0 pts):**
   * High Intent (Inbound Demo Request, Referral, Direct Sales Call): `+2.0 pts`
   * Medium Intent (Content Download, Webinar Attendee): `+1.0 pt`
   * Low Intent (Outbound LinkedIn / Cold Outreach): `+0.5 pts`

4. **Interaction Recency (Max 2.0 pts):**
   * $\le 60$ days old: `+2.0 pts`
   * $61–180$ days old: `+1.0 pt`
   * $> 180$ days old: `0.0 pts`

### Decision Routing Thresholds
* **QUALIFIED (High Priority):** Score $\ge 7.0$ with no missing critical data fields. Triggers personalized outreach generation.
* **REVIEW (Medium Priority):** Score between $4.0$ and $6.9$, or leads missing secondary attributes. Flagged for manual SDR inspection.
* **REJECTED (Low Priority):** Score $< 4.0$. Excluded from active sales cadence.

---

## ⚙️ Environment Setup & Prerequisites

### 1. Prerequisites
* **Python 3.10+**
* `pandas`
* `google-genai`

### 2. Dependencies Installation
Run the following command in your terminal:
```bash
pip install google-genai pandas
```

---

## 🔑 Setting Up Google Gemini LLM API

To enable AI-driven evaluation mode using Google Gemini (`gemini-3.8-flash`):

1. Obtain a free API key from **[Google AI Studio](https://aistudio.google.com/)**.
2. Export your API key in your terminal session before execution.

### PowerShell (Windows):
```powershell
$env:GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

### Command Prompt (Windows):
```cmd
set GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

### Bash / Zsh (Linux / macOS):
```bash
export GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

> **Note:** If no API key is detected or if an API error occurs during LLM execution, the system gracefully falls back to the deterministic rubric engine without crashing.

---

## 🚀 How to Execute the Pipeline

You can run the pipeline in either **Rubric Mode** (Deterministic) or **Gemini Mode** (LLM Batched).

### 1. Run via Local Deterministic Rubric (`--mode rubric`)
No API keys required. Evaluates dataset instantly via local programmatic rules.
```bash
python main.py --csv leads_training.csv --output output_lead_training_normal.json --mode rubric
```

### 2. Run via Google Gemini LLM (`--mode gemini`)
Requires `GEMINI_API_KEY` set in the active terminal session.
```bash
python main.py --csv leads_training.csv --output output_Lead_training_gemini.json --mode gemini
```

### 3. Run at Production Scale (100+ Leads)
```bash
python main.py --csv leads_full_scale_100.csv --output output_full_scale_gemini.json --mode gemini
```

---

## 📊 What to Expect (Output Structure)

Upon execution, the CLI prints real-time logs to standard output and generates a structured JSON report at the specified output path.

### Terminal Output Preview:
```text
[Ingest] Loading leads from: leads_training.csv
[GEMINI] Attempting batch evaluation via Google Gemini...

[Export] Pipeline execution complete (LLM (GEMINI)).
[Export] Report successfully saved to: output_Lead_training_gemini.json
Summary: Total=29 | Qualified=17 | Review=8 | Rejected=4
```

### Output JSON Report Schema:
```json
{
  "metadata": {
    "processed_timestamp": "2026-11-07T12:15:50.589245",
    "source_csv": "leads_training.csv",
    "total_records": 29,
    "evaluation_mode": "LLM (GEMINI)"
  },
  "summary": {
    "total_leads": 29,
    "qualified": 17,
    "review": 8,
    "rejected": 4,
    "qualified_percentage": 58.6
  },
  "sample_outreach_messages": [
    "Hi Alice, thanks for requesting a demo of our platform. Given CloudScale AI's rapid growth in SaaS..."
  ],
  "leads": [
    {
      "name": "Alice Chen",
      "company": "CloudScale AI",
      "company_size": 50,
      "industry": "SaaS",
      "source": "Inbound demo request",
      "score": 9.8,
      "decision": "QUALIFIED",
      "priority": "HIGH",
      "reasoning": "Fits target size (50), Tier-1 industry (SaaS), highest intent source (Inbound demo request), and highly recent interaction.",
      "outreach_message": "Hi Alice, thanks for requesting a demo of our platform..."
    }
  ]
}
```

---

## ⚠️ Known Limitations & Edge Cases

1. **Session-Scoped Environment Variables:** In PowerShell, `$env:GEMINI_API_KEY` is tied to the current shell tab. Opening a new terminal tab clears the key, triggering a temporary fallback to rubric mode.
2. **Missing Dates / Fields:** Leads missing required values default to `0.0 pts` for that specific factor and are flagged for human `REVIEW`.
3. **Model Versioning:** Configured specifically for `gemini-3.8-flash`. Deprecated endpoints (e.g., `gemini-2.5-flash`) are bypassed via internal fallbacks.