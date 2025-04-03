import os

# --- Constants ---
DEFAULT_EXCEL_PATH = "Pathfinder Data.xlsx"
DEFAULT_PDF_DIR = "annual_reports"
DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_OUTPUT_CSV = os.path.join(DEFAULT_OUTPUT_DIR, "enhanced_dataset.csv")
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Define the action categories for classification
ACTION_CATEGORIES = [
    "Renewables",
    "Energy Efficiency",
    "Electrification",
    "Bioenergy",
    "CCUS",
    "Hydrogen Fuel",
    "Behavioral Changes"
]

# Updated Extraction prompt template (now requesting countries of operation and justifications for actions)
ENHANCED_EXTRACTION_PROMPT = """
Analyze the following annual report text for "{company_name}" and extract the explicitly stated information below.
Structure the output EXACTLY as follows, using the headers provided, and ensure your entire response is valid JSON.
If a specific piece of information is not explicitly mentioned in the text provided, state "Not Mentioned".

{{
  "Executive Summary": "[Provide a concise summary of the company's business model and overall strategy as stated.]",
  "Strategic Priorities (Energy Transition)": "[List ONLY explicitly mentioned priorities related to: Renewables, Energy Efficiency, Electrification, Bioenergy, CCUS, Hydrogen Fuel, Behavioral Changes. If none mentioned, state 'Not Mentioned'.]",
  "Financial Commitments (Energy Transition)": "[State SPECIFICALLY: a) % of CapEx dedicated to energy transition, b) Absolute CapEx amount in local currency, c) Any planned increase over time, d) Any specific project allocations. Provide exact figures and timeframes if mentioned. If none found, state 'Not Mentioned'.]",
  "Identified Risks (Physical and Transition)": "[List explicitly mentioned physical risks (e.g., climate impacts) and transition risks (e.g., policy changes, market shifts) related to energy/climate. If none mentioned, state 'Not Mentioned'.]",
  "Sustainability Milestones": "[List explicitly stated quantitative milestones, targets, years, and scope coverage (Scope 1, 2, 3) related to emissions or other sustainability goals. If none mentioned, state 'Not Mentioned'.]",
  "Countries of Operation": "[List all countries where the company explicitly states it has operations, assets, production facilities, or significant business activities. Provide as a comma-separated list. If none mentioned, state 'Not Mentioned'.]",
  "Action Classifications": {{
      "Renewables": "[TRUE/FALSE]",
      "Energy Efficiency": "[TRUE/FALSE]",
      "Electrification": "[TRUE/FALSE]",
      "Bioenergy": "[TRUE/FALSE]",
      "CCUS": "[TRUE/FALSE]",
      "Hydrogen Fuel": "[TRUE/FALSE]",
      "Behavioral Changes": "[TRUE/FALSE]"
  }},
  "Action Justifications": {{
      "Renewables_Justification": "[If Renewables is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "Energy Efficiency_Justification": "[If Energy Efficiency is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "Electrification_Justification": "[If Electrification is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "Bioenergy_Justification": "[If Bioenergy is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "CCUS_Justification": "[If CCUS is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "Hydrogen Fuel_Justification": "[If Hydrogen Fuel is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]",
      "Behavioral Changes_Justification": "[If Behavioral Changes is TRUE, provide a brief justification based on the text. Otherwise, leave blank.]"
  }}
}}
--- START OF ANNUAL REPORT TEXT ---
{text}
--- END OF ANNUAL REPORT TEXT ---
"""

# Updated Structured recommendation prompt template (requires valid JSON output)
DETAILED_RECOMMENDATION_PROMPT = """
You are an expert energy transition consultant creating a detailed, time-based roadmap of recommendations for {company_name}.

COMPANY PROFILE FROM ANNUAL REPORT:
- Executive Summary: {executive_summary}
- Strategic Priorities: {strategic_priorities}
- Financial Commitments: {financial_commitments}
- Sustainability Targets: {sustainability_info}
- Identified Risks: {risks_info}

FINANCIAL VIABILITY ASSESSMENT:
- CapEx for Sustainability: {transition_capex}
- Current Investment Areas: {project_allocations}

RISK EVALUATION:
{risk_assessment}

{actions_summary}

TASK: Create a detailed energy transition roadmap for {company_name} with the following specifications.
- Your recommendations MUST take into account the risk assessment results.
- For high climate risk regions, prioritize adaptation measures and faster timelines.
- For high carbon price risk regions, focus on emissions reduction and cost mitigation.
- For high technology risk regions, recommend incremental technology adoption strategies.

CRITICAL: YOU MUST OUTPUT YOUR ENTIRE RESPONSE IN VALID JSON FORMAT USING THIS EXACT STRUCTURE:

{{
  "company": "{company_name}",
  "timeframes": [
    {{
      "name": "Immediate actions (Now - 2030)",
      "actions": [
        {{
          "category": "Renewables",
          "recommendations": [
            {{
              "title": "Brief recommendation title",
              "details": "Detailed explanation of the recommendation",
              "reference": "Annual Report reference or New Recommendation rationale",
              "justification": {{
                "peer_alignment": "How this aligns with industry standards or peer practices",
                "financial_viability": "Analysis of financial feasibility based on company CapEx",
                "operational_feasibility": "Assessment of implementation feasibility",
                "target_alignment": "How this helps meet company's stated targets",
                "risk_mitigation": "How this addresses identified risks in the risk assessment"
              }}
            }}
          ]
        }}
      ]
    }},
    {{
      "name": "Medium-term actions (2030 - 2040)",
      "actions": [ /* same structure as above */ ]
    }},
    {{
      "name": "Long-term goals (2040 - 2050)",
      "actions": [ /* same structure as above */ ]
    }}
  ]
}}
"""
