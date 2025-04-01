import os

# --- Constants ---
DEFAULT_EXCEL_PATH = "Pathfinder Data.xlsx"
DEFAULT_PDF_DIR = "annual_reports"
DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_OUTPUT_CSV = os.path.join(DEFAULT_OUTPUT_DIR, "enhanced_dataset.csv")
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Extraction prompt template
EXTRACTION_PROMPT_TEMPLATE = """
Analyze the following annual report text for "{company_name}" and extract the explicitly stated information below.
Structure the output EXACTLY as follows, using the headers provided.
If a specific piece of information is not explicitly mentioned in the text provided, state "Not Mentioned".

1.  Executive Summary: [Provide a concise summary of the company's business model and overall strategy as stated.]
2.  Strategic Priorities (Energy Transition): [List ONLY explicitly mentioned priorities related to: Renewables, Energy Efficiency, Electrification, Bioenergy, Carbon Capture Utilisation and Storage (CCUS), Hydrogen Fuel, Behavioral Changes. If none mentioned, state "Not Mentioned".]
3.  Financial Commitments (Energy Transition): [State the specific % of CapEx explicitly dedicated to energy transition, or other explicitly stated financial commitment figures related to transition. If none mentioned, state "Not Mentioned".]
4.  Identified Risks (Physical and Transition): [List explicitly mentioned physical risks (e.g., climate impacts) and transition risks (e.g., policy changes, market shifts) related to energy/climate. If none mentioned, state "Not Mentioned".]
5.  Sustainability Milestones: [List explicitly stated quantitative milestones, targets, years, and scope coverage (Scope 1, 2, 3) related to emissions or other sustainability goals. If none mentioned, state "Not Mentioned".]

--- START OF ANNUAL REPORT TEXT ---
{report_text}
--- END OF ANNUAL REPORT TEXT ---

Structured Output:
"""

# Enhanced extraction prompt
ENHANCED_EXTRACTION_PROMPT = """
Analyze the following annual report text for "{company_name}" and extract the explicitly stated information below.
Structure the output EXACTLY as follows, using the headers provided.
If a specific piece of information is not explicitly mentioned in the text provided, state "Not Mentioned".

1.  Executive Summary: [Provide a concise summary of the company's business model and overall strategy as stated.]
2.  Strategic Priorities (Energy Transition): [List ONLY explicitly mentioned priorities related to: Renewables, Energy Efficiency, Electrification, Bioenergy, Carbon Capture Utilisation and Storage (CCUS), Hydrogen Fuel, Behavioral Changes. If none mentioned, state "Not Mentioned".]
3.  Financial Commitments (Energy Transition): [State the specific % of CapEx explicitly dedicated to energy transition, or other explicitly stated financial commitment figures related to transition. If none mentioned, state "Not Mentioned".]
4.  Identified Risks (Physical and Transition): [List explicitly mentioned physical risks (e.g., climate impacts) and transition risks (e.g., policy changes, market shifts) related to energy/climate. If none mentioned, state "Not Mentioned".]
5.  Sustainability Milestones: [List explicitly stated quantitative milestones, targets, years, and scope coverage (Scope 1, 2, 3) related to emissions or other sustainability goals. If none mentioned, state "Not Mentioned".]
6.  Action Classifications: For each action category below, explicitly state TRUE or FALSE if the company is engaged in this action based on the report. For each TRUE classification, provide a brief, one-sentence justification with evidence from the text:
   a) Renewables: [TRUE/FALSE] [If TRUE, provide justification]
   b) Energy Efficiency: [TRUE/FALSE] [If TRUE, provide justification]
   c) Electrification: [TRUE/FALSE] [If TRUE, provide justification]
   d) Bioenergy: [TRUE/FALSE] [If TRUE, provide justification]
   e) CCUS: [TRUE/FALSE] [If TRUE, provide justification]
   f) Hydrogen Fuel: [TRUE/FALSE] [If TRUE, provide justification]
   g) Behavioral Changes: [TRUE/FALSE] [If TRUE, provide justification]

--- START OF ANNUAL REPORT TEXT ---
{text}
--- END OF ANNUAL REPORT TEXT ---

Structured Output:
"""

# Recommendation prompt template
RECOMMENDATION_PROMPT_TEMPLATE = """
Context: You are an expert energy transition consultant analyzing company data to provide actionable recommendations.

Peer Group Context ({num_peers} companies):
{peer_summary}

Company Under Review: {company_name}
Company Details:
{company_summary}

Task: Generate a practical, step-by-step energy transition roadmap for {company_name}. The roadmap should be ambitious yet achievable, considering the company's profile, current actions, and peer context. Structure it clearly into milestones aligned with typical climate goals:

- Immediate actions (Now - 2030): Focus on foundational steps, quick wins, and compliance.
- Medium-term actions (2030 - 2040): Focus on scaling proven technologies and deeper integration.
- Long-term goals (2040 - 2050): Focus on achieving deep decarbonization and potentially net-zero targets.

Be specific and suggest concrete actions within each timeframe (e.g., "Invest X% CapEx in solar PV by 2028", "Pilot green hydrogen project by 2035", "Achieve 50% reduction in Scope 1 & 2 emissions by 2040"). Align recommendations with IEA milestones or similar frameworks where applicable.

Roadmap for {company_name}:
"""

# Structured recommendation prompt template
DETAILED_RECOMMENDATION_PROMPT = """
You are an expert energy transition consultant creating a detailed, time-based roadmap of recommendations for {company_name}.

COMPANY PROFILE FROM ANNUAL REPORT:
- Executive Summary: {executive_summary}
- Strategic Priorities: {strategic_priorities}
- Financial Commitments: {financial_commitments}
- Sustainability Targets: {sustainability_info}
- Identified Risks: {risks_info}

{actions_summary}

TASK: Create a detailed energy transition roadmap for {company_name} with the following specifications.

CRITICAL: YOU MUST OUTPUT YOUR ENTIRE RESPONSE IN VALID JSON FORMAT USING THIS EXACT STRUCTURE:

```json
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
              "reference": "Annual Report reference or New Recommendation rationale"
            }}
          ]
        }}
      ]
    }}
  ]
}}
```

Your response must include the following three timeframes:
1. "Immediate actions (Now - 2030)"
2. "Medium-term actions (2030 - 2040)"
3. "Long-term goals (2040 - 2050)"

For each timeframe, include action categories relevant to the company from this list:
- Renewables
- Energy Efficiency
- Electrification
- Bioenergy
- Carbon Capture Utilization and Storage (CCUS)
- Hydrogen Fuel
- Behavioral Changes
- Other relevant actions

Requirements:
- Base recommendations PRIMARILY on actions already identified in the company's annual report
- For each identified action, provide specific steps that link to the company's actual targets
- Only suggest NEW actions if they are feasible based on the company's operations and industry
- For each recommendation, explain HOW it helps achieve specific targets mentioned in their sustainability milestones
- Be specific with measurable targets and timelines (e.g., "Increase renewable capacity by X% by 2030")
- Include feasibility considerations and potential implementation challenges

For references:
- For EACH recommendation, explicitly cite where in the annual report the supporting information was found
- Use this format: [Annual Report, Section/Page Reference: "Direct quote or paraphrased content"]
- If recommending something not explicitly mentioned in the report, clearly state: [New Recommendation: Rationale based on industry standards/peer practices]

IMPORTANT: RESPOND ONLY WITH VALID JSON. Do not include any explanatory text, markdown formatting, or code blocks outside the JSON structure. The JSON must be parseable by standard JSON parsers.
"""
# Action categories
ACTION_CATEGORIES = [
    "Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
    "CCUS", "Hydrogen Fuel", "Behavioral Changes"
]
