# analysis/integrator.py
import logging
# from numpy import imag # <-- This import seems unused, consider removing
import pandas as pd
from services.gemini_service import get_gemini_response
# import numpy as np # <-- This import seems unused, consider removing
import json
from datetime import date, datetime # Import datetime types

# --- Helper function to handle non-serializable types ---
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        # Convert Timestamp/datetime objects to ISO 8601 string format
        return obj.isoformat()
    # For other types, let the default encoder raise the error
    raise TypeError (f"Type {type(obj)} not serializable")
# --------------------------------------------------------


def get_industry_peers(company_name, df, limit=5):
    """Get the most relevant peers based on industry and size."""
    # Ensure the company exists before trying to access it
    company_rows = df[df['Name'] == company_name]
    if company_rows.empty:
        logging.warning(f"Company '{company_name}' not found in DataFrame for peer comparison.")
        # Return an empty DataFrame or handle as appropriate
        return pd.DataFrame() # Return empty DF

    company = company_rows.iloc[0]
    industry = company['Industry']

    # Filter by same industry, exclude the target company
    peers = df[(df['Industry'] == industry) & (df['Name'] != company_name)]

    return peers.head(limit)


def generate_llm_peer_summary(company_name, peers_df, client, model):
    """Generate a comprehensive peer comparison using Gemini."""

    # Check if peers_df is empty or doesn't contain the company
    if peers_df is None or peers_df.empty:
        logging.error("Peers DataFrame is empty in generate_llm_peer_summary.")
        return "Error: Cannot generate peer summary with empty data."
    company_rows = peers_df[peers_df['Name'] == company_name]
    if company_rows.empty:
         logging.error(f"Target company '{company_name}' not found within the provided peers_df.")
         return f"Error: Target company '{company_name}' not found for peer summary."

    # Convert DataFrame rows to dictionaries
    # Using .iloc[0] is safe here because we checked company_rows is not empty
    company_data = company_rows.iloc[0].to_dict()
    peers_data = peers_df[peers_df['Name'] != company_name].to_dict('records')

    # --- Use the helper function in json.dumps ---
    try:
        company_data_json = json.dumps(company_data, indent=2, default=json_serial)
        peers_data_json = json.dumps(peers_data, indent=2, default=json_serial)
    except TypeError as e:
        logging.error(f"JSON serialization failed even with handler: {e}")
        logging.error(f"Problematic company_data keys: {list(company_data.keys())}")
        # Consider logging problematic values if possible, but be careful with large data
        return f"Error: Failed to serialize data for prompt generation. Check logs. ({e})"
    # ----------------------------------------------


    # Create prompt for the LLM
    prompt = f"""
    Analyze the following company and its industry peers to generate a comprehensive peer comparison:

    TARGET COMPANY:
    {company_data_json}

    INDUSTRY PEERS:
    {peers_data_json}

    Please provide:
    1. How the company compares to industry averages on emissions reduction targets
    2. Where the company stands relative to peers on key sustainability metrics
    3. Which strategies are common among industry leaders that this company may be missing
    4. Specific competitive advantages or disadvantages in sustainability this company has
    5. Recommendations for how this company can better align with or exceed industry standards

    Format your analysis as a concise, insightful executive summary with clear sections and bullet points where appropriate.
    """

    # Get LLM response
    return get_gemini_response(prompt, client, model)


def generate_llm_executive_summary(company_row, client, model):
    """Generate a strategic executive summary using Gemini."""
    # company_row is expected to be a Pandas Series here
    if not isinstance(company_row, pd.Series):
        logging.error("generate_llm_executive_summary expected a Pandas Series, got %s", type(company_row))
        # Attempt conversion or raise error
        if isinstance(company_row, pd.DataFrame) and len(company_row) == 1:
             company_data = company_row.iloc[0].to_dict()
        else:
            return "Error: Invalid data format for executive summary generation."
    else:
        company_data = company_row.to_dict()


    # --- Use the helper function in json.dumps ---
    try:
        company_data_json = json.dumps(company_data, indent=2, default=json_serial)
    except TypeError as e:
        logging.error(f"JSON serialization failed even with handler: {e}")
        logging.error(f"Problematic company_data keys: {list(company_data.keys())}")
        return f"Error: Failed to serialize data for prompt generation. Check logs. ({e})"
    # ----------------------------------------------

    # Create prompt for the LLM
    prompt = f"""
    Based on the following company data, generate a strategic executive summary:

    COMPANY DATA:
    {company_data_json}

    Your executive summary should:
    1. Highlight the most important aspects of the company's current sustainability position
    2. Identify key strengths and weaknesses in their energy transition strategy
    3. Summarize their stated commitments and how robust they appear
    4. Analyze the alignment between their actions and their stated goals
    5. Flag any critical gaps or opportunities

    Focus on synthesizing insights rather than repeating facts. Limit to 3-4 paragraphs.
    """

    # Get LLM response
    return get_gemini_response(prompt, client, model)


def integrate_data(original_df, extracted_data_list):
    """Integrate the original data with the extracted data from reports."""
    if not extracted_data_list:
        logging.warning("No data extracted from reports. Returning original dataframe.")
        return original_df

    extracted_df = pd.DataFrame(extracted_data_list)

    # Ensure 'Company Name' is string type for merging in both dataframes
    if 'Name' not in original_df.columns:
         logging.error("Original DataFrame missing 'Name' column for integration.")
         return original_df # Or raise error
    if 'Name' not in extracted_df.columns:
         logging.error("Extracted DataFrame missing 'Name' column for integration.")
         # Try to recover or return original
         return original_df

    original_df['Name'] = original_df['Name'].astype(str).str.strip()
    extracted_df['Name'] = extracted_df['Name'].astype(str).str.strip()

    # Merge the dataframes
    enhanced_df = pd.merge(original_df, extracted_df, on="Name", how="left")
    logging.info(f"Data integrated. Enhanced DataFrame shape: {enhanced_df.shape}")
    logging.info(f"Columns after integration: {enhanced_df.columns.tolist()}")  # Log columns

    # Optional: Convert known date columns back to datetime after merge if needed elsewhere
    # Example: enhanced_df['DateColumn'] = pd.to_datetime(enhanced_df['DateColumn'], errors='coerce')

    return enhanced_df


def generate_peer_summary(company_name, df):
    """Generate a summary of peer companies for comparison."""
    # Ensure df is not empty
    if df is None or df.empty:
         logging.warning("DataFrame is empty in generate_peer_summary.")
         return "No data available for peer summary."

    peer_df = df[df['Name'] != company_name]
    num_peers = len(peer_df)
    if num_peers == 0:
        return "No peer data available."

    summary_points = []
    # Example summary points - customize as needed
    reduction_col = 'Interim_target_percentage_reduction' # Check if this column exists and is appropriate
    if reduction_col in peer_df.columns:
        # Convert to numeric, coercing errors to NaN, then calculate mean ignoring NaNs
        avg_reduction = pd.to_numeric(peer_df[reduction_col], errors='coerce').mean(skipna=True) # Explicitly skip NaNs
    else:
        logging.warning(f"Column '{reduction_col}' not found for peer summary. Setting avg_reduction to NaN.")
        avg_reduction = pd.NA # Use pd.NA for missing value

    if not pd.isna(avg_reduction):
        summary_points.append(f"- Average interim emissions reduction target by peers: {avg_reduction:.1f}%")
    else:
        summary_points.append(f"- Average interim emissions reduction target by peers: Not Available")


    # Common Strategic Priorities
    action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
                   "CCUS", "Hydrogen Fuel", "Behavioral Changes"]
    # Check which action columns actually exist in the DataFrame
    existing_action_cols = [col for col in action_cols if col in peer_df.columns]

    if existing_action_cols:
         # Ensure boolean or numeric conversion before summing
         numeric_peer_actions = peer_df[existing_action_cols].fillna(0).astype(int) # Fill NA with 0 and convert to int
         common_actions = numeric_peer_actions.sum().sort_values(ascending=False)
         top_actions = common_actions[common_actions > 0].index.tolist()
         if top_actions:
             summary_points.append(f"- Common transition actions among peers: {', '.join(top_actions[:3])}...") # Show top 3
         else:
              summary_points.append(f"- Common transition actions among peers: None identified.")
    else:
         summary_points.append(f"- Common transition actions among peers: Data not available.")


    # Example: % of peers mentioning CCUS
    if 'CCUS' in peer_df.columns:
        # Assuming CCUS column is boolean or 0/1 after cleaning/integration
        ccus_peers = peer_df['CCUS'].fillna(0).astype(bool).sum() # Handle potential NaNs and ensure boolean sum
        summary_points.append(f"- Peers actively mentioning CCUS: {ccus_peers}/{num_peers} ({ccus_peers/num_peers:.1%})")
    else:
         summary_points.append(f"- Peers actively mentioning CCUS: Data not available.")


    return "\n".join(summary_points) if summary_points else "Basic peer statistics not available."


def generate_company_summary(company_row):
    """Generate a summary of a company's data for recommendations."""
    # Expects company_row to be a Pandas Series
    if not isinstance(company_row, pd.Series):
         logging.error("generate_company_summary expected a Pandas Series, got %s", type(company_row))
         return "Error: Invalid data format for company summary."

    # Select key columns to include in the summary
    cols_to_summarize = [
        'Name', 'Industry', 'Annual Revenue', 'Employee Size', 'Geographical Region',
        'Capital Expenditure', 'Emissions Reduction (% achieved)', 'Target Status',
        'Emission targets', 'Target Year', 'Scope coverage', 'Use of carbon credits',
        'Executive Summary', 'Strategic Priorities (Energy Transition)',
        'Financial Commitments (Energy Transition)', 'Identified Risks (Physical and Transition)',
        'Sustainability Milestones', 'Renewables', 'Energy Efficiency', 'Electrification',
        'Bioenergy', 'CCUS', 'Hydrogen Fuel', 'Behavioral Changes'
    ]

    summary_list = []
    for col in cols_to_summarize:
        # Use .get() for safe access on the Series
        value = company_row.get(col)

        # Handle NaN values gracefully
        if pd.isna(value):
             value_str = "Not Available"
        else:
             # Convert to string for consistent handling
             value_str = str(value)
             # Shorten potentially long text fields like summaries/risks
             if len(value_str) > 300:
                 value_str = value_str[:300] + "..."

        summary_list.append(f"- {col}: {value_str}")

    return "\n".join(summary_list)
