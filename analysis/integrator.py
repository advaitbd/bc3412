# analysis/integrator.py
import logging
import pandas as pd

def integrate_data(original_df, extracted_data_list):
    """Integrate the original data with the extracted data from reports."""
    if not extracted_data_list:
        logging.warning("No data extracted from reports. Returning original dataframe.")
        return original_df

    extracted_df = pd.DataFrame(extracted_data_list)

    # Ensure 'Company Name' is string type for merging in both dataframes
    original_df['Name'] = original_df['Name'].astype(str)
    extracted_df['Name'] = extracted_df['Name'].astype(str)

    # Merge the dataframes
    enhanced_df = pd.merge(original_df, extracted_df, on="Name", how="left")
    logging.info(f"Data integrated. Enhanced DataFrame shape: {enhanced_df.shape}")
    logging.info(f"Columns after integration: {enhanced_df.columns.tolist()}")  # Log columns
    return enhanced_df

def generate_peer_summary(company_name, df):
    """Generate a summary of peer companies for comparison."""
    peer_df = df[df['Name'] != company_name]
    num_peers = len(peer_df)
    if num_peers == 0:
        return "No peer data available."

    summary_points = []
    # Example summary points - customize as needed
    reduction_col = 'Interim_target_percentage_reduction'
    if reduction_col in peer_df.columns:
        # Convert to numeric, coercing errors to NaN, then calculate mean ignoring NaNs
        avg_reduction = pd.to_numeric(peer_df[reduction_col], errors='coerce').mean()
    else:
        logging.warning(f"Column '{reduction_col}' not found for peer summary. Setting avg_reduction to NaN.")
        avg_reduction = pd.NA

    if not pd.isna(avg_reduction):
        summary_points.append(f"- Average emissions reduction achieved by peers: {avg_reduction:.1f}%")

    # Common Strategic Priorities
    action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy",
                   "CCUS", "Hydrogen Fuel", "Behavioral Changes"]
    common_actions = peer_df[action_cols].sum().sort_values(ascending=False)
    top_actions = common_actions[common_actions > 0].index.tolist()
    if top_actions:
        summary_points.append(f"- Common transition actions among peers: {', '.join(top_actions[:3])}...")  # Show top 3

    # Example: % of peers mentioning CCUS
    ccus_peers = peer_df['CCUS'].sum()
    summary_points.append(f"- Peers actively mentioning CCUS: {ccus_peers}/{num_peers} ({ccus_peers/num_peers:.1%})")

    return "\n".join(summary_points) if summary_points else "Basic peer statistics not available."

def generate_company_summary(company_row):
    """Generate a summary of a company's data for recommendations."""
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
        if col in company_row.index:
            value = company_row[col]
            # Handle NaN values gracefully
            value_str = str(value) if not pd.isna(value) else "Not Available"
            # Shorten potentially long text fields like summaries/risks
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            summary_list.append(f"- {col}: {value_str}")

    return "\n".join(summary_list)
