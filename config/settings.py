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

# --- UPDATED Extraction Prompt ---
ENHANCED_EXTRACTION_PROMPT = """
Analyze the following annual report text for "{company_name}" and extract the explicitly stated information below.
Use the existing company information provided to inform your analysis, but focus on extracting new information from the report text.

EXISTING COMPANY DATA:
{company_context}

Structure the output EXACTLY as follows, using the headers provided, and ensure your entire response is valid JSON.
If a specific piece of information is not explicitly mentioned in the text provided, state "Not Mentioned". For the TRUE/FALSE classifications, format it as "TRUE" or "FALSE" ONLY.

{{
  "Executive Summary": "[Provide a concise summary of the company's business model and overall strategy as stated.]",
  "Strategic Priorities (Energy Transition)": "[List ONLY explicitly mentioned priorities related to: {action_categories_list}. If none mentioned, state 'Not Mentioned'.]",
  "Financial Commitments (Energy Transition)": "[State SPECIFICALLY: a) % of CapEx dedicated to energy transition, b) Absolute CapEx amount in local currency, c) Any planned increase over time, d) Any specific project allocations. Provide exact figures and timeframes if mentioned. If none found, state 'Not Mentioned'.]",
  "Identified Risks (Physical and Transition)": "[List explicitly mentioned physical risks (e.g., climate impacts) and transition risks (e.g., policy changes, market shifts) related to energy/climate. If none mentioned, state 'Not Mentioned'.]",

  // --- START: Modified Target Section ---
  "Emission targets": "[List specific quantitative emission reduction targets mentioned, e.g., '50% reduction in Scope 1 & 2 by 2030', 'Net Zero Scope 1 & 2 by 2050'. If none explicitly stated, state 'Not Mentioned'.]",
  "Target Year": "[State the primary target year mentioned for the main emission goals (e.g., 2030, 2040, 2050). If multiple distinct years or none explicitly stated, state 'Not Mentioned' or list key years.]",
  "Scope coverage": "[List the scopes (Scope 1, 2, 3) explicitly covered by the main emission targets mentioned. Format as 'Scope 1, 2' or 'Scope 1, 2, 3'. If not explicitly mentioned, state 'Not Mentioned'.]",
  "Base Year": "[State the base year used for emission reduction targets, if mentioned (e.g., 2019). If not mentioned, state 'Not Mentioned'.]",
  "Interim Targets": "[List any specific interim targets mentioned (e.g., '25% reduction by 2025'). If none mentioned, state 'Not Mentioned'.]",
  // --- END: Modified Target Section ---

  "Countries of Operation": "[List all countries where the company explicitly states it has operations, assets, production facilities, or significant business activities. Provide as a comma-separated list. If none mentioned, state 'Not Mentioned'.]",
  "Action Classifications": {{
      "Renewables": "TRUE/FALSE",
      "Energy Efficiency": "TRUE/FALSE",
      "Electrification": "TRUE/FALSE",
      "Bioenergy": "TRUE/FALSE",
      "CCUS": "TRUE/FALSE",
      "Hydrogen Fuel": "TRUE/FALSE",
      "Behavioral Changes": "TRUE/FALSE"
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
The following RISK SCORES come from our in-house risk evaluation models in the 'risk_eval' module:
- Climate Risk: calculated by analyzing temperature rise forecasts
- Carbon Price Risk: calculated by evaluating carbon tax/subsidy forecasting
- Technology Risk: calculated by forecasting low-carbon technology adoption rates

Use these scores when filling in the score field for each factor

{risk_assessment}


{actions_summary}

TASK: Create a detailed energy transition roadmap for {company_name} with the following specifications:
- Organize your analysis into External Factors, Internal Factors, Factor Rankings, and Time-based Recommendations.
- Your recommendations MUST take into account the risk assessment results. Use these results to fill the score for each factor.
- For high climate risk regions, prioritize adaptation measures and faster timelines.
- For high carbon price risk regions, focus on emissions reduction and cost mitigation.
- For high technology risk regions, recommend incremental technology adoption strategies.

CRITICAL: YOU MUST OUTPUT YOUR ENTIRE RESPONSE IN VALID JSON FORMAT USING THIS EXACT STRUCTURE:

{{
  "company": "{company_name}",
  "external_factors": {{
    "climate_risk": {{
      "score": "High/Medium/Low",
      "interpretation": "Detailed interpretation of climate risk for this company",
      "impact": "How this impacts the company's operations and strategy"
    }},
    "carbon_price_risk": {{
      "score": "High/Medium/Low",
      "interpretation": "Detailed interpretation of carbon price risk for this company",
      "impact": "How this impacts the company's financial outlook"
    }},
    "technology_risk": {{
      "score": "High/Medium/Low",
      "interpretation": "Detailed interpretation of technology risk for this company",
      "impact": "How this impacts the company's competitive position"
    }},
    "policy_environment": "Analysis of the regulatory environment in the company's operating regions"
  }},
  "internal_factors": {{
    "operational_feasibility": {{
      "assessment": "High/Medium/Low",
      "details": "Analysis of the company's operational capacity to implement changes"
    }},
    "financial_viability": {{
      "assessment": "High/Medium/Low",
      "details": "Analysis of the company's financial capacity to fund the transition"
    }},
    "existing_capabilities": {{
      "assessment": "Strong/Moderate/Weak",
      "details": "Assessment of the company's existing technological and operational capabilities"
    }},
    "organizational_readiness": {{
      "assessment": "High/Medium/Low",
      "details": "Assessment of the company's cultural and organizational readiness for change"
    }}
  }},
  "factor_rankings": [
    {{
      "factor": "Name of factor (e.g., Climate Risk)",
      "rank": 1,
      "importance": "Critical/High/Medium/Low",
      "justification": "Why this factor ranks highest in importance for this company"
    }},
    {{
      "factor": "Name of factor",
      "rank": 2,
      "importance": "Critical/High/Medium/Low",
      "justification": "Why this factor ranks second in importance"
    }}
    // Include all remaining factors in ranked order
  ],
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
