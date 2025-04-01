import os
import pandas as pd
import fitz  # PyMuPDF
import google.generativeai as genai
import logging
import numpy as np
import re
from dotenv import load_dotenv
import argparse

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants ---
DEFAULT_EXCEL_PATH = "Pathfinder Data.xlsx"
DEFAULT_PDF_DIR = "annual_reports"
DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_OUTPUT_CSV = os.path.join(DEFAULT_OUTPUT_DIR, "enhanced_dataset.csv")
GEMINI_MODEL_NAME = "gemini-2.0-flash" # Or choose another appropriate Gemini model

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


# --- Core Functions ---

def load_config():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY not found in environment variables or .env file.")
        raise ValueError("API Key not configured.")
    logging.info("API Key loaded successfully.")
    return api_key

def configure_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        logging.info(f"Gemini client configured with model: {GEMINI_MODEL_NAME}")
        return model
    except Exception as e:
        logging.error(f"Failed to configure Gemini: {e}")
        raise

def load_excel_data(filepath=DEFAULT_EXCEL_PATH):
    try:
        df = pd.read_excel(filepath)
        logging.info(f"Successfully loaded data from {filepath}. Shape: {df.shape}")
        # Basic validation - Check for 'Company Name' column
        if 'Name' not in df.columns:
            logging.error(f"'Company Name' column not found in {filepath}. Please ensure it exists.")
            raise ValueError("Missing 'Company Name' column in Excel file.")
        return df
    except FileNotFoundError:
        logging.error(f"Error: Excel file not found at {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading Excel file {filepath}: {e}")
        raise

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        logging.warning(f"PDF file not found: {pdf_path}")
        return None
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        logging.info(f"Successfully extracted text from {os.path.basename(pdf_path)}.")
        # Basic check for extracted text length
        if len(text.strip()) < 100: # Arbitrary threshold for potentially empty/corrupt PDFs
             logging.warning(f"Very little text extracted from {os.path.basename(pdf_path)}. Check PDF content.")
        return text
    except Exception as e:
        logging.error(f"Error reading PDF file {os.path.basename(pdf_path)}: {e}")
        return None

def parse_gemini_output(response_text):
    data = {
        "Executive Summary": np.nan,
        "Strategic Priorities (Energy Transition)": np.nan,
        "Financial Commitments (Energy Transition)": np.nan,
        "Identified Risks (Physical and Transition)": np.nan,
        "Sustainability Milestones": np.nan
    }
    # Use regex to find sections robustly, handling potential variations
    patterns = {
        "Executive Summary": r"^\s*1\.\s*Executive Summary:\s*(.*?)(?=^\s*2\.\s*Strategic Priorities|\Z)",
        "Strategic Priorities (Energy Transition)": r"^\s*2\.\s*Strategic Priorities \(Energy Transition\):\s*(.*?)(?=^\s*3\.\s*Financial Commitments|\Z)",
        "Financial Commitments (Energy Transition)": r"^\s*3\.\s*Financial Commitments \(Energy Transition\):\s*(.*?)(?=^\s*4\.\s*Identified Risks|\Z)",
        "Identified Risks (Physical and Transition)": r"^\s*4\.\s*Identified Risks \(Physical and Transition\):\s*(.*?)(?=^\s*5\.\s*Sustainability Milestones|\Z)",
        "Sustainability Milestones": r"^\s*5\.\s*Sustainability Milestones:\s*(.*?)(?=^\s*---|\Z)" # Assuming --- might mark end, or just end of text
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            extracted_value = match.group(1).strip()
            if "Not Mentioned" in extracted_value:
                 data[key] = np.nan # Store as NaN if Gemini explicitly states not mentioned
            else:
                 data[key] = extracted_value if extracted_value else np.nan
        else:
             logging.warning(f"Could not parse section '{key}' from Gemini response.")
             data[key] = np.nan # Store as NaN if parsing fails

    # Add specific columns for key transition actions based on 'Strategic Priorities'
    priorities_text = data.get("Strategic Priorities (Energy Transition)", "")
    if pd.isna(priorities_text):
         priorities_text = ""

    action_keywords = {
        "Renewables": ["renewable", "solar", "wind", "geothermal", "hydro"],
        "Energy Efficiency": ["efficiency", "demand management", "reduce consumption"],
        "Electrification": ["electrify", "electric vehicle", "EV", "heat pump"],
        "Bioenergy": ["biofuel", "biomass", "biogas"],
        "CCUS": ["carbon capture", "ccus", "ccs", "carbon storage", "carbon utilization"],
        "Hydrogen Fuel": ["hydrogen", "h2", "fuel cell"],
        "Behavioral Changes": ["behavioral", "behavioural", "awareness", "employee engagement"]
    }

    for action, keywords in action_keywords.items():
        # Simple keyword check (case-insensitive)
        found = any(keyword in priorities_text.lower() for keyword in keywords)
        data[action] = found # Store as True/False

    return data


def get_gemini_extraction(text, company_name, gemini_model):
    if not text:
        logging.warning(f"No text provided for Gemini extraction for {company_name}.")
        # Return dictionary with NaNs and False for actions
        parsed_data = parse_gemini_output("")
        return parsed_data

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(company_name=company_name, report_text=text[:800000]) # Limit context to avoid potential issues, adjust as needed

    try:
        logging.info(f"Sending request to Gemini for {company_name}...")
        response = gemini_model.generate_content(prompt)
        logging.info(f"Received response from Gemini for {company_name}.")

        # Handle potential safety blocks or empty responses
        if not response.parts:
             logging.warning(f"Gemini returned no content for {company_name}. Possible safety block or empty generation.")
             parsed_data = parse_gemini_output("") # Return empty structure
             return parsed_data

        extracted_text = response.text
        logging.debug(f"Raw Gemini Response for {company_name}:\n{extracted_text}") # Log the raw response for debugging
        # Basic check of response format
        if not all(s in extracted_text for s in ["Executive Summary:", "Strategic Priorities", "Financial Commitments", "Identified Risks", "Sustainability Milestones"]):
            logging.warning(f"Gemini response for {company_name} might be incomplete or wrongly formatted:\n{extracted_text[:500]}...") # Log beginning of potentially bad response


        parsed_data = parse_gemini_output(extracted_text)
        return parsed_data

    except Exception as e:
        logging.error(f"Error calling Gemini API for {company_name}: {e}")
        # Return dictionary with NaNs and False for actions in case of API error
        parsed_data = parse_gemini_output("")
        return parsed_data

def process_companies(df, pdf_dir, gemini_model):
    extracted_data_list = []
    total_companies = len(df)
    processed_count = 0

    for index, row in df.iterrows():
        company_name = row['Name']
        logging.info(f"Processing {company_name} ({processed_count + 1}/{total_companies})...")

        # Construct PDF path based on exact company name
        pdf_filename = f"{company_name}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        # Extract text
        report_text = extract_text_from_pdf(pdf_path)

        if report_text is None:
            logging.warning(f"Skipping Gemini extraction for {company_name} due to PDF read error or missing file.")
            # Create a record with NaNs/False but keep company name for merging
            llm_results = parse_gemini_output("")
        else:
            # Get structured data from Gemini
            llm_results = get_gemini_extraction(report_text, company_name, gemini_model)

        # Add company name to the results for merging
        llm_results['Name'] = company_name
        extracted_data_list.append(llm_results)
        processed_count += 1

    logging.info(f"Finished processing {processed_count} companies.")
    return extracted_data_list

def integrate_data(original_df, extracted_data_list):
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
    logging.info(f"Columns after integration: {enhanced_df.columns.tolist()}") # Log columns
    return enhanced_df

def classify_actions(df):
    logging.info("Classifying actions into broader categories...")
    # Define mapping from specific actions (columns) to broader buckets
    # A single action can potentially map to multiple buckets if applicable,
    # but for simplicity, let's do a primary mapping here.
    # Adjust logic as needed based on nuanced definitions.

    # Ensure action columns exist, default to False if missing after merge/extraction
    action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy", "CCUS", "Hydrogen Fuel", "Behavioral Changes"]
    for col in action_cols:
        if col not in df.columns:
            df[col] = False # Add column with False if it wasn't created during extraction
        else:
            df[col] = df[col].fillna(False) # Fill any potential NaNs with False


    # Initialize category columns
    df['Category: Operational Efficiency'] = False
    df['Category: Renewable Integration'] = False
    df['Category: Technology Investment'] = False
    df['Category: Policy & Compliance'] = False # This might need different logic, e.g., based on risk text or milestones? For now, placeholder.

    # Apply classification logic (Example - refine as needed)
    df.loc[df['Energy Efficiency'] | df['Behavioral Changes'], 'Category: Operational Efficiency'] = True
    df.loc[df['Renewables'] | df['Electrification'] | df['Bioenergy'], 'Category: Renewable Integration'] = True # Electrification often tied to renewables
    df.loc[df['CCUS'] | df['Hydrogen Fuel'], 'Category: Technology Investment'] = True
    # Note: Policy & Compliance is harder to map directly from these actions.
    # It might be inferred from 'Identified Risks' or 'Sustainability Milestones'.
    # Let's add a simple placeholder check in risks for now.

    # Ensure the risks column is string type and fill NaNs before using .str accessor
    risks_col = 'Identified Risks (Physical and Transition)'
    if risks_col not in df.columns:
        df[risks_col] = "" # Add empty string column if it doesn't exist
    else:
        # Ensure column is string type, replacing NaN with empty string
        df[risks_col] = df[risks_col].astype(str).fillna('')

    df['Category: Policy & Compliance'] = df[risks_col].str.contains('policy|regulation|compliance', case=False)


    logging.info("Action classification complete.")
    return df


def save_enhanced_data(df, output_path=DEFAULT_OUTPUT_CSV):
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Created output directory: {output_dir}")

        df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info(f"Enhanced dataset successfully saved to {output_path}")
    except Exception as e:
        logging.error(f"Error saving data to {output_path}: {e}")
        raise

def generate_peer_summary(company_name, df):
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
        avg_reduction = np.nan

    if not pd.isna(avg_reduction):
        summary_points.append(f"- Average emissions reduction achieved by peers: {avg_reduction:.1f}%")

    # Common Strategic Priorities
    action_cols = ["Renewables", "Energy Efficiency", "Electrification", "Bioenergy", "CCUS", "Hydrogen Fuel", "Behavioral Changes"]
    common_actions = peer_df[action_cols].sum().sort_values(ascending=False)
    top_actions = common_actions[common_actions > 0].index.tolist()
    if top_actions:
         summary_points.append(f"- Common transition actions among peers: {', '.join(top_actions[:3])}...") # Show top 3

    # Example: % of peers mentioning CCUS
    ccus_peers = peer_df['CCUS'].sum()
    summary_points.append(f"- Peers actively mentioning CCUS: {ccus_peers}/{num_peers} ({ccus_peers/num_peers:.1%})")

    return "\n".join(summary_points) if summary_points else "Basic peer statistics not available."


def generate_company_summary(company_row):
    # Select key columns to include in the summary
    # Adjust columns based on importance for recommendations
    cols_to_summarize = [
        'Company Name', 'Industry', 'Annual Revenue', 'Employee Size', 'Geographical Region',
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

def get_recommendations(company_name, enhanced_df, gemini_model):
    if company_name not in enhanced_df['Name'].values:
        logging.error(f"Company '{company_name}' not found in the enhanced dataset.")
        print(f"Error: Company '{company_name}' not found.")
        return

    company_row = enhanced_df[enhanced_df['Name'] == company_name].iloc[0]

    # Generate summaries
    peer_summary = generate_peer_summary(company_name, enhanced_df)
    company_summary = generate_company_summary(company_row)
    num_peers = len(enhanced_df) - 1

    # Format prompt
    prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
        num_peers=num_peers,
        peer_summary=peer_summary,
        company_name=company_name,
        company_summary=company_summary
    )

    # Call Gemini API
    try:
        logging.info(f"Sending recommendation request to Gemini for {company_name}...")
        response = gemini_model.generate_content(prompt)
        logging.info(f"Received recommendation from Gemini for {company_name}.")

        # Print the recommendation roadmap
        print("\n" + "="*50)
        print(f" Energy Transition Roadmap for: {company_name}")
        print("="*50 + "\n")
        # Check for content before printing
        if response.parts:
             print(response.text)
        else:
             print("Gemini did not return a recommendation. This might be due to safety settings or an issue.")
             logging.warning(f"Gemini returned no content for recommendation request for {company_name}.")

    except Exception as e:
        logging.error(f"Error getting recommendations for {company_name} from Gemini: {e}")
        print(f"Error: Could not generate recommendations for {company_name}.")

# --- Main Execution Logic ---

def main():
    """Main function to run the data pipeline."""
    logging.info("Starting the Energy Transition Data Pipeline MVP...")

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description='Energy Transition Data Pipeline MVP')
    parser.add_argument('-f', '--force-reprocess', action='store_true',
                        help='Force reprocessing of PDFs, ignoring existing enhanced_dataset.csv')
    parser.add_argument('-c', '--company', type=str, default=None,
                        help='Specify the company name for which to generate recommendations')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # --- Set Log Level ---
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug logging enabled.")

    try:
        # 1. Load Config and Configure Gemini
        api_key = load_config()
        gemini_model = configure_gemini(api_key)

        # 2. Load Initial Data
        original_df = load_excel_data(DEFAULT_EXCEL_PATH)

        # --- Check if enhanced data already exists ---
        enhanced_data_exists = os.path.exists(DEFAULT_OUTPUT_CSV)
        enhanced_df = None

        if enhanced_data_exists:
            # If not forcing reprocess and file exists, try loading it
            if not args.force_reprocess:
                logging.info(f"Loading existing enhanced data from {DEFAULT_OUTPUT_CSV}")
                try:
                    enhanced_df = pd.read_csv(DEFAULT_OUTPUT_CSV)
                    logging.info(f"Columns loaded from CSV: {enhanced_df.columns.tolist()}") # Log columns
                    # Basic check to ensure it looks like the right file
                    if 'Name' not in enhanced_df.columns or 'Executive Summary' not in enhanced_df.columns:
                        logging.warning("Existing CSV seems incomplete or incorrect. Re-processing.")
                        enhanced_df = None # Force re-processing
                    else:
                        logging.info("Successfully loaded existing enhanced data.")
                except Exception as e:
                    logging.error(f"Failed to load existing enhanced data: {e}. Re-processing.")
                    enhanced_df = None # Force re-processing
            # If forcing reprocess, log it
            elif args.force_reprocess:
                logging.info("User chose to re-process data.")
                enhanced_df = None # Ensure re-processing happens

        # --- Processing Steps (if not using existing data) ---
        if enhanced_df is None:
            # Check for PDF directory
            if not os.path.isdir(DEFAULT_PDF_DIR):
                logging.error(f"PDF directory not found: '{DEFAULT_PDF_DIR}'. Please create it and place PDF reports inside.")
                print(f"Error: Directory '{DEFAULT_PDF_DIR}' not found. Please create it.")
                return

            # 3. Process Companies (PDF Extraction + Gemini Analysis)
            extracted_results = process_companies(original_df, DEFAULT_PDF_DIR, gemini_model)

            # 4. Integrate Data
            enhanced_df = integrate_data(original_df, extracted_results)

            # 5. Classify Actions
            enhanced_df = classify_actions(enhanced_df)

            # 6. Save Enhanced Data
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)

        # --- Recommendation Step ---
        if enhanced_df is not None and not enhanced_df.empty:
            if args.company:
                logging.info(f"Attempting to generate recommendations for: {args.company}")
                get_recommendations(args.company, enhanced_df, gemini_model)
            else:
                logging.info("No company specified via --company argument. Skipping recommendations.")

        else:
            logging.error("Enhanced dataset is empty or could not be created. Cannot proceed to recommendations.")

        logging.info("Pipeline execution finished.")

    except (ValueError, FileNotFoundError) as e: # Catch configuration/setup errors
        logging.critical(f"Pipeline failed due to configuration or file error: {e}")
        print(f"Error: {e}. Please check your setup (API key, file paths) and try again.")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}", exc_info=True) # Log full traceback
        print(f"An unexpected error occurred. Check logs for details.")

if __name__ == "__main__":
    main()
