import os
import sys
import time
import pandas as pd
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv # To load .env for the API key
from data.loaders import load_excel_data, extract_text_from_pdf

# --- Load Environment Variables ---
load_dotenv() # Load .env file if it exists

# --- Add project root to Python path for imports ---
# This assumes backend_api.py is in the project root. Adjust if needed.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import project modules ---
from config.settings import (
    DEFAULT_EXCEL_PATH,
    DEFAULT_PDF_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_CSV,
    GEMINI_MODEL_NAME,
    # ACTION_CATEGORIES # Import if needed directly
)
from utils.logging_utils import setup_logging # Use your setup
from utils.file_utils import ensure_directory_exists # Use your util
from data.loaders import load_excel_data, extract_text_from_pdf
from data.savers import save_enhanced_data
from services.gemini_service import configure_gemini, get_gemini_response
from services.extraction import get_gemini_extraction # Use the specific function
from services.visualization import generate_pathway_visualization # For pathway generation
from analysis.integrator import integrate_data
# **Modify recommendations import slightly**
# We need the core logic, let's assume we refactor or access it
# from analysis.recommendations import get_recommendations # We'll call this
from analysis.recommendations import DETAILED_RECOMMENDATION_PROMPT # Import prompt if needed directly
from risk_eval.risk_evaluator import run_comprehensive_risk_assessment # Import risk assessment

# --- Configuration ---
# Use constants from settings where possible
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'annual_reports_uploads') # Separate upload dir
ALLOWED_EXTENSIONS = {'pdf'}
OUTPUT_DIR = DEFAULT_OUTPUT_DIR
ENHANCED_CSV_PATH = DEFAULT_OUTPUT_CSV
VISUALIZATIONS_DIR = os.path.join(OUTPUT_DIR, 'visualizations') # Standardized path
EXCEL_PATH = DEFAULT_EXCEL_PATH
PDF_ORIGINAL_DIR = DEFAULT_PDF_DIR # Keep track of the original dir too

# Create necessary directories
ensure_directory_exists(UPLOAD_FOLDER)
ensure_directory_exists(OUTPUT_DIR)
ensure_directory_exists(VISUALIZATIONS_DIR)

# Setup Logging (using your utility)
logger = setup_logging() # Set debug level based on environment or flag if needed

# --- Initialize Gemini Client ---
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY") # Match key name in your .env
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    gemini_client, gemini_model = configure_gemini(api_key=gemini_api_key)
    logger.info("Gemini client configured successfully.")
except Exception as e:
    logger.critical(f"Failed to configure Gemini: {e}", exc_info=True)
    # Exit or handle gracefully if Gemini is essential for all operations
    gemini_client, gemini_model = None, None # Indicate failure


# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS for requests from the Vite frontend

# --- Helper Functions (Integrated) ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_path(company_name):
    """Finds the PDF path, checking upload folder first, then original."""
    secure_name = secure_filename(f"{company_name}.pdf")
    upload_path = os.path.join(UPLOAD_FOLDER, secure_name)
    original_path = os.path.join(PDF_ORIGINAL_DIR, f"{company_name}.pdf") # Use original name format

    if os.path.exists(upload_path):
        return upload_path
    elif os.path.exists(original_path):
        return original_path
    else:
        return None

def get_company_status_from_excel_and_fs():
    """Reads the source Excel and checks filesystem for PDF and processing status."""
    logger.info("Reading company status...")
    try:
        # Load original company list
        df_excel = load_excel_data(EXCEL_PATH) # Uses your loader
        company_names = df_excel['Name'].unique().tolist()

        # Check for enhanced data
        processed_companies = set()
        if os.path.exists(ENHANCED_CSV_PATH):
            try:
                df_enhanced = pd.read_csv(ENHANCED_CSV_PATH)
                if 'Name' in df_enhanced.columns:
                    processed_companies = set(df_enhanced['Name'].astype(str).str.strip().unique())
            except Exception as e:
                 logger.warning(f"Could not read or parse enhanced CSV {ENHANCED_CSV_PATH}: {e}")

        status_list = []
        for name in company_names:
            clean_name = str(name).strip()
            pdf_exists = get_pdf_path(clean_name) is not None
            status_list.append({
                'name': clean_name,
                'pdf_exists': pdf_exists,
                'processed': clean_name in processed_companies
            })
        return status_list

    except FileNotFoundError:
        logger.error(f"Source Excel file not found: {EXCEL_PATH}")
        return [{"error": f"Source Excel file '{EXCEL_PATH}' not found."}]
    except ValueError as ve: # Catch specific error from loader
         logger.error(f"Error loading Excel: {ve}")
         return [{"error": str(ve)}]
    except Exception as e:
        logger.error(f"Error in get_company_status: {e}", exc_info=True)
        return [{"error": "Failed to retrieve company status. Check backend logs."}]

def run_processing_for_company(company_name):
    """
    Runs the actual data extraction and integration for a single company.
    Updates the enhanced CSV.
    """
    logger.info(f"Starting processing for: {company_name}")
    if not gemini_client:
        logger.error("Gemini client not initialized. Cannot process.")
        return False, "Gemini client not available."

    pdf_path = get_pdf_path(company_name)
    if not pdf_path:
        logger.warning(f"No PDF found for {company_name}. Cannot process.")
        return False, f"PDF report for '{company_name}' not found."

    try:
        # 1. Load original company data
        original_df = load_excel_data(EXCEL_PATH)
        original_df['Name'] = original_df['Name'].astype(str).str.strip()

        # Find the specific company data
        company_data = original_df[original_df['Name'] == company_name]
        if company_data.empty:
            logger.error(f"Company '{company_name}' not found in original Excel.")
            return False, f"Company '{company_name}' not found in source data."

        # Get the company row as a Series
        company_row = company_data.iloc[0]

        # 2. Extract Text
        logger.info(f"Extracting text from {pdf_path}...")
        report_text = extract_text_from_pdf(pdf_path)
        if report_text is None:
            logger.error(f"Failed to extract text from PDF for {company_name}.")
            return False, "Failed to extract text from PDF."
        if len(report_text) < 100:
             logger.warning(f"Very little text extracted for {company_name}. Processing might yield poor results.")

        # 3. Get LLM Extraction - Pass company data to extraction function
        logger.info(f"Sending extraction request to Gemini for {company_name} with company context...")
        llm_results = get_gemini_extraction(report_text, company_name, company_row, gemini_client, gemini_model)
        if not llm_results: # Check if extraction returned an empty dict or None
            logger.error(f"Gemini extraction failed or returned empty for {company_name}.")
            return False, "Data extraction via AI failed."
        logger.info(f"Received structured data from Gemini for {company_name}.")

        # 3. Integrate Data
        logger.info(f"Integrating data for {company_name}...")
        # Load original data
        original_df = load_excel_data(EXCEL_PATH)
        original_df['Name'] = original_df['Name'].astype(str).str.strip()

        # Load existing enhanced data OR create new if not exists
        if os.path.exists(ENHANCED_CSV_PATH):
            try:
                enhanced_df = pd.read_csv(ENHANCED_CSV_PATH)
                enhanced_df['Name'] = enhanced_df['Name'].astype(str).str.strip()
                # Remove existing entry for this company to avoid duplicates on re-processing
                enhanced_df = enhanced_df[enhanced_df['Name'] != company_name]
            except Exception as e:
                logger.error(f"Error loading existing enhanced CSV {ENHANCED_CSV_PATH}, starting fresh: {e}")
                enhanced_df = pd.DataFrame() # Start fresh
        else:
            enhanced_df = pd.DataFrame() # Create new if file doesn't exist

        # Prepare the single result for integration (needs to be DataFrame-like)
        # We'll merge the original company data with the new LLM results first
        company_original_data = original_df[original_df['Name'] == company_name]
        if company_original_data.empty:
             logger.error(f"Company '{company_name}' not found in original Excel '{EXCEL_PATH}'. Cannot integrate.")
             return False, f"Company '{company_name}' missing from source Excel."

        # Create a DataFrame from the single LLM result dict
        llm_df = pd.DataFrame([llm_results])
        llm_df['Name'] = llm_df['Name'].astype(str).str.strip()

        # Merge the original data for the company with its LLM results
        # Use outer join to keep all columns, handle potential conflicts if needed
        new_company_enhanced_data = pd.merge(
            company_original_data,
            llm_df,
            on="Name",
            how="left" # Keep original data even if LLM extraction failed partially
            # Add suffixes if there are overlapping columns other than 'Name'
            # suffixes=('_orig', '_llm')
        )

        # Append the newly processed company data to the potentially existing enhanced_df
        updated_enhanced_df = pd.concat([enhanced_df, new_company_enhanced_data], ignore_index=True)

        # 4. Save Updated Data
        save_success = save_enhanced_data(updated_enhanced_df, ENHANCED_CSV_PATH) # Uses your saver
        if not save_success:
             # save_enhanced_data logs the error, but we should signal failure
             return False, "Failed to save updated enhanced data."

        logger.info(f"Processing successful for {company_name}. Enhanced data saved.")
        return True, "Processing successful."

    except Exception as e:
        logger.error(f"Error during processing for {company_name}: {e}", exc_info=True)
        return False, f"An unexpected error occurred during processing: {e}"


# --- Modification required in analysis/recommendations.py ---
# We need `get_recommendations` (or a wrapper) to return the HTML path.
# Let's create a wrapper here for simplicity, assuming the original
# `get_recommendations` saves the file but doesn't return the path.

def generate_recommendations_and_get_path(company_name):
    """
    Wrapper for get_recommendations that ensures the HTML path is returned.
    """
    logger.info(f"Starting recommendation generation for: {company_name}")
    if not gemini_client:
        logger.error("Gemini client not initialized. Cannot generate recommendations.")
        raise RuntimeError("Gemini client not available.") # Raise specific error

    if not os.path.exists(ENHANCED_CSV_PATH):
        logger.error(f"Enhanced dataset '{ENHANCED_CSV_PATH}' not found. Cannot generate recommendations.")
        raise FileNotFoundError(f"Enhanced dataset not found. Process '{company_name}' first.")

    try:
        enhanced_df = pd.read_csv(ENHANCED_CSV_PATH)
        enhanced_df['Name'] = enhanced_df['Name'].astype(str).str.strip()

        # Check if company exists after loading
        if company_name not in enhanced_df['Name'].values:
             logger.error(f"Company '{company_name}' not found in the processed dataset.")
             raise ValueError(f"Company '{company_name}' not found in processed data.")

        # --- Call the original get_recommendations ---
        # This function should internally call generate_pathway_visualization
        # We *assume* it saves the file correctly to the VISUALIZATIONS_DIR
        # based on the logic shown in the provided `recommendations.py`
        from analysis.recommendations import get_recommendations # Import here to avoid circular deps if any
        get_recommendations(company_name, enhanced_df, gemini_client, gemini_model)

        # --- Determine the path where the file *should have been* saved ---
        # Construct the expected filename based on visualization.py logic
        # Sanitize company name for filename if necessary (check if get_recommendations does this)
        safe_company_name = secure_filename(company_name).replace('_', ' ') # Basic sanitization example
        html_filename = f"{safe_company_name}_pathway.html"
        expected_html_path = os.path.join(VISUALIZATIONS_DIR, html_filename)

        if not os.path.exists(expected_html_path):
            logger.error(f"Recommendation generated, but expected HTML file not found at: {expected_html_path}")
            # Maybe check for slight variations in filename?
            # Fallback: search the dir?
            raise FileNotFoundError("Generated HTML visualization file was not found.")

        logger.info(f"Recommendations generated successfully for {company_name}. HTML at: {expected_html_path}")

        # Return the RELATIVE path for the /static endpoint
        relative_path = os.path.join('visualizations', html_filename)
        return relative_path.replace(os.sep, '/') # Ensure forward slashes for URL

    except Exception as e:
        logger.error(f"Error during recommendation generation for {company_name}: {e}", exc_info=True)
        # Re-raise the exception to be caught by the API endpoint handler
        raise e


# --- API Endpoints (Integrated) ---

@app.route('/api/companies', methods=['GET'])
def list_companies():
    """Returns the list of companies and their status."""
    status_list = get_company_status_from_excel_and_fs()
    if status_list and isinstance(status_list[0], dict) and "error" in status_list[0]:
         return jsonify({"error": status_list[0]["error"]}), 500
    return jsonify(status_list)


@app.route('/api/companies/<path:company_name>/upload', methods=['POST'])
def upload_report(company_name):
    """Handles PDF report upload for a specific company."""
    # Decode URL-encoded company name if necessary (e.g., spaces become %20)
    # company_name = unquote(company_name) # from urllib.parse
    logger.info(f"Upload request for company: {company_name}")

    if 'file' not in request.files:
        logger.warning("Upload attempt failed: No file part in request.")
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        logger.warning(f"Upload attempt failed for {company_name}: No selected file.")
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        # Use secure_filename on the *original* filename, but save with company name
        # filename_secure = secure_filename(file.filename) # Get original extension safely
        save_filename = f"{secure_filename(company_name)}.pdf" # Standardized name
        filepath = os.path.join(UPLOAD_FOLDER, save_filename)
        try:
            file.save(filepath)
            logger.info(f"File uploaded successfully for {company_name} to {filepath}")
            # Get updated status to return pdf_exists: true
            updated_status_list = get_company_status_from_excel_and_fs()
            company_updated_status = next((item for item in updated_status_list if item['name'] == company_name), None)
            return jsonify({
                 "message": f"File for {company_name} uploaded successfully.",
                 "company_status": company_updated_status
                 }), 200
        except Exception as e:
            logger.error(f"Failed to save uploaded file for {company_name}: {e}")
            return jsonify({"error": f"Could not save file: {e}"}), 500
    else:
        logger.warning(f"Upload attempt failed for {company_name}: File type not allowed ({file.filename})")
        return jsonify({"error": "File type not allowed (only .pdf)"}), 400


@app.route('/api/companies/<path:company_name>/process', methods=['POST'])
def process_company_report(company_name):
    """Triggers the processing pipeline for a specific company."""
    logger.info(f"Processing request received for: {company_name}")
    try:
        success, message = run_processing_for_company(company_name)
        if success:
            # Fetch updated status after successful processing
            updated_status_list = get_company_status_from_excel_and_fs()
            company_updated_status = next((item for item in updated_status_list if item['name'] == company_name), None)
            return jsonify({
                "message": message, # "Processing successful."
                "company_status": company_updated_status
                }), 200
        else:
            # Processing failed, return the specific message from the function
            return jsonify({"error": message}), 500 # Use 500 for server-side processing errors
    except Exception as e:
        # Catch-all for unexpected errors in the endpoint handler itself
        logger.error(f"Processing endpoint failed unexpectedly for {company_name}: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500


@app.route('/api/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Provides data from the enhanced dataset for the dashboard."""
    logger.info("Dashboard data requested.")
    if not os.path.exists(ENHANCED_CSV_PATH):
        logger.warning(f"Dashboard data requested but file not found: {ENHANCED_CSV_PATH}")
        return jsonify({"error": "Enhanced dataset not found. Process companies first."}), 404

    try:
        df = pd.read_csv(ENHANCED_CSV_PATH)
        # Clean column names (replace spaces, %, etc.) if needed for easier JS access
        # df.columns = df.columns.str.replace(' ', '_', regex=False).str.replace('[^A-Za-z0-9_]+', '', regex=True)

        relevant_cols = [
            'Name', 'Industry', 'Annual Revenue', 'Employee Size', 'Geographical Region',
            'Target Status',
            # --- Include NEW Target Columns ---
            'Emission targets',
            'Target Year',
            'Scope coverage',
            'Base Year',       # Add if you want to display it
            'Interim Targets', # Add if you want to display it
            # --- End New Target Columns ---
            'Emissions Reduction (% achieved)', # Check exact name from your original Excel/integration
            'Renewables', 'Energy Efficiency', 'Electrification', 'Bioenergy',
            'CCUS', 'Hydrogen Fuel', 'Behavioral Changes'
        ]
        existing_cols = [col for col in relevant_cols if col in df.columns]
        if not existing_cols:
             logger.error("No relevant columns found in the enhanced dataset for the dashboard.")
             return jsonify({"error": "Dashboard data format error: No relevant columns found."}), 500

        dashboard_df = df[existing_cols]

        # Convert NaN to null for JSON compatibility (or 'N/A' if preferred)
        dashboard_df = dashboard_df.where(pd.notnull(dashboard_df), None)

        # Convert boolean-like columns (might be True/False, 'TRUE'/'FALSE', 1/0)
        bool_cols = ['Renewables', 'Energy Efficiency', 'Electrification', 'Bioenergy', 'CCUS', 'Hydrogen Fuel', 'Behavioral Changes']
        for col in bool_cols:
            if col in dashboard_df.columns:
                # Example conversion: map various forms to true/false/null
                def map_bool(val):
                    if pd.isna(val) or val is None: return None
                    if isinstance(val, bool): return val
                    if isinstance(val, (int, float)): return val != 0
                    if isinstance(val, str):
                        val_lower = val.strip().lower()
                        if val_lower == 'true': return True
                        if val_lower == 'false': return False
                        if val_lower == 'yes': return True
                        if val_lower == 'no': return False
                        if val_lower == '1': return True
                        if val_lower == '0': return False
                    return None # Or keep original if unsure
                dashboard_df[col] = dashboard_df[col].apply(map_bool)

        dashboard_json = dashboard_df.to_dict('records')
        logger.info(f"Returning {len(dashboard_json)} records for dashboard.")
        return jsonify(dashboard_json)
    except Exception as e:
        logger.error(f"Failed to load or process dashboard data: {e}", exc_info=True)
        return jsonify({"error": f"Failed to prepare dashboard data: {str(e)}"}), 500


# backend_api.py (Relevant parts modified)
import os
import sys
import time
import pandas as pd
import logging
from flask import Flask, request, jsonify, send_from_directory
# ... other imports remain the same ...
from werkzeug.utils import secure_filename
# ... other imports ...
from analysis.recommendations import get_recommendations # Import the core function

# --- Constants and Setup remain the same ---
# ... UPLOAD_FOLDER, ALLOWED_EXTENSIONS, OUTPUT_DIR, ENHANCED_CSV_PATH, VISUALIZATIONS_DIR, EXCEL_PATH, PDF_ORIGINAL_DIR ...
# ... Directory creation ...
# ... Logging setup ...
# ... Gemini client init ...
# ... Flask App setup (app = Flask(...), CORS(app)) ...
# ... Helper functions (allowed_file, get_pdf_path, get_company_status_from_excel_and_fs, run_processing_for_company) remain the same ...


# --- MODIFIED Recommendation Helper ---
def generate_recommendations_and_get_path(company_name):
    """
    Checks if pathway HTML exists. If yes, returns its path.
    If not, generates recommendations, saves HTML, and returns its path.
    Raises errors if generation fails or required data is missing.
    """
    logger.info(f"Requesting pathway for: {company_name}")
    if not gemini_client:
        logger.error("Gemini client not initialized. Cannot generate recommendations.")
        raise RuntimeError("Gemini client not available.")

    # --- Check if HTML file already exists ---
    # Construct the expected filename based on visualization.py logic
    # Use secure_filename for basic safety, assuming get_recommendations uses a similar logic for saving
    # safe_company_name_for_file = secure_filename(company_name) # Use secure name for file path check
    html_filename = f"{company_name}_pathway.html"
    expected_html_path = os.path.join(VISUALIZATIONS_DIR, html_filename)
    relative_path = os.path.join('visualizations', html_filename).replace(os.sep, '/') # For API response

    if os.path.exists(expected_html_path):
        logger.info(f"Pathway HTML already exists for {company_name} at {expected_html_path}. Returning existing path.")
        return relative_path # Return path to existing file

    # --- File doesn't exist, proceed with generation ---
    logger.info(f"Pathway HTML not found for {company_name}. Proceeding with generation.")

    if not os.path.exists(ENHANCED_CSV_PATH):
        logger.error(f"Enhanced dataset '{ENHANCED_CSV_PATH}' not found. Cannot generate recommendations for {company_name}.")
        raise FileNotFoundError(f"Enhanced dataset not found. Process '{company_name}' first.")

    try:
        enhanced_df = pd.read_csv(ENHANCED_CSV_PATH)
        # Ensure consistent cleaning for matching
        enhanced_df['Name'] = enhanced_df['Name'].astype(str).str.strip()
        company_name_clean = str(company_name).strip()

        if company_name_clean not in enhanced_df['Name'].values:
             logger.error(f"Company '{company_name_clean}' not found in the processed dataset.")
             raise ValueError(f"Company '{company_name_clean}' not found in processed data.")

        # --- Call the original get_recommendations ---
        # This function needs access to the Gemini client and model.
        # It should internally handle risk assessment and call generate_pathway_visualization,
        # saving the file to VISUALIZATIONS_DIR with the expected name format.
        logger.info(f"Calling core recommendation generation logic for {company_name_clean}...")
        get_recommendations(company_name_clean, enhanced_df, gemini_client, gemini_model)
        logger.info(f"Core recommendation generation finished for {company_name_clean}.")

        # --- Verify the file was created ---
        if not os.path.exists(expected_html_path):
            logger.error(f"Recommendation generated, but expected HTML file still not found at: {expected_html_path}")
            # Possible causes: filename mismatch in generation step, saving error, incorrect VISUALIZATIONS_DIR used by get_recommendations
            raise FileNotFoundError(f"Generated HTML visualization file was not found after processing. Expected at: {html_filename}")

        logger.info(f"Recommendations generated successfully for {company_name}. HTML saved to: {expected_html_path}")
        return relative_path # Return the relative path

    except (FileNotFoundError, ValueError, RuntimeError) as specific_error:
         # Re-raise errors we specifically check for
         raise specific_error
    except Exception as e:
        logger.error(f"Unexpected error during recommendation generation for {company_name}: {e}", exc_info=True)
        # Wrap unexpected errors
        raise RuntimeError(f"An unexpected error occurred during pathway generation: {e}") from e


# --- MODIFIED API Endpoint ---
@app.route('/api/companies/<path:company_name>/generate-pathway', methods=['POST'])
def generate_pathway(company_name):
    """
    Checks for existing pathway, generates if needed, returns URL path.
    Handles potential errors during the process.
    """
    logger.info(f"'/generate-pathway' endpoint called for: {company_name}")
    if not gemini_client:
         return jsonify({"error": "Cannot generate pathway: Gemini client not available."}), 503

    try:
        # This function now handles the check and generation internally
        relative_html_path = generate_recommendations_and_get_path(company_name)
        api_path = f"/static/{relative_html_path}" # Construct URL path

        logger.info(f"Pathway URL path for {company_name}: {api_path}")
        return jsonify({"pathway_url": api_path}), 200

    except FileNotFoundError as e:
         logger.warning(f"Pathway generation prerequisite failed for {company_name}: {e}")
         # If enhanced dataset is missing, it's more of a client error (needs processing first)
         if "Enhanced dataset not found" in str(e):
             return jsonify({"error": str(e)}), 400 # Bad Request - needs processing
         else:
              return jsonify({"error": str(e)}), 404 # Not Found - HTML file missing after generation attempt?
    except ValueError as e: # Catch value errors (e.g., company not found in data)
         logger.warning(f"Pathway generation input error for {company_name}: {e}")
         return jsonify({"error": str(e)}), 404 # Treat as Not Found or Bad Request
    except RuntimeError as e: # Catch specific runtime errors (Gemini client, unexpected gen error)
         logger.error(f"Pathway generation runtime error for {company_name}: {e}")
         return jsonify({"error": str(e)}), 503 # Service Unavailable or Internal Error
    except Exception as e:
        # Catch-all for truly unexpected errors
        logger.error(f"Pathway generation endpoint failed unexpectedly for {company_name}: {e}", exc_info=True)
        return jsonify({"error": f"Pathway generation failed unexpectedly: {str(e)}"}), 500


# Serve the generated static HTML files from the 'outputs/visualizations' directory
@app.route('/static/visualizations/<path:filename>')
def serve_static_html(filename):
    """Serves the generated HTML pathway visualizations."""
    # VISUALIZATIONS_DIR should be the absolute path
    abs_visualizations_dir = os.path.abspath(VISUALIZATIONS_DIR)
    logger.debug(f"Attempting to serve static file: {filename} from {abs_visualizations_dir}")
    # Check if file exists to prevent directory traversal issues, though send_from_directory is generally safe
    safe_path = os.path.abspath(os.path.join(abs_visualizations_dir, filename))
    if not safe_path.startswith(abs_visualizations_dir) or not os.path.isfile(safe_path):
        logger.warning(f"Static file not found or invalid path: {filename}")
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(abs_visualizations_dir, filename)


# --- Main Execution ---
if __name__ == '__main__':
    if not gemini_client:
        logger.warning("Flask server starting, but Gemini client failed to initialize.")
        # Decide if the app should run without Gemini or exit
        # sys.exit("Exiting: Gemini client initialization failed.")

    port = int(os.environ.get("PORT", 5001))
    logger.info(f"Starting Flask server on http://localhost:{port}")
    # Set threaded=False if you encounter issues with shared resources,
    # but generally True is fine for development. Be careful with production.
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
