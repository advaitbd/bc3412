# main.py
import os
import argparse
import logging
import pandas as pd

# Import from our modules
from config.settings import DEFAULT_EXCEL_PATH, DEFAULT_PDF_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_CSV
from utils.logging_utils import setup_logging
from data.loaders import load_excel_data, extract_text_from_pdf
from data.savers import save_enhanced_data
from services.gemini_service import load_config, configure_gemini
from services.extraction import process_companies
from analysis.integrator import integrate_data
from analysis.recommendations import get_recommendations

def main():
    """Main function to run the data pipeline."""
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description='Energy Transition Data Pipeline MVP')
    parser.add_argument('-f', '--force-reprocess', action='store_true',
                      help='Force reprocessing of PDFs, ignoring existing enhanced_dataset.csv')
    parser.add_argument('-c', '--company', type=str, default=None,
                      help='Specify the company name for which to generate recommendations')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # --- Set Up Logging ---
    logger = setup_logging(args.debug)
    logger.info("Starting the Energy Transition Data Pipeline MVP...")

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
                logger.info(f"Loading existing enhanced data from {DEFAULT_OUTPUT_CSV}")
                try:
                    enhanced_df = pd.read_csv(DEFAULT_OUTPUT_CSV)
                    logger.info(f"Columns loaded from CSV: {enhanced_df.columns.tolist()}")  # Log columns
                    # Basic check to ensure it looks like the right file
                    if 'Name' not in enhanced_df.columns or 'Executive Summary' not in enhanced_df.columns:
                        logger.warning("Existing CSV seems incomplete or incorrect. Re-processing.")
                        enhanced_df = None  # Force re-processing
                    else:
                        logger.info("Successfully loaded existing enhanced data.")
                except Exception as e:
                    logger.error(f"Failed to load existing enhanced data: {e}. Re-processing.")
                    enhanced_df = None  # Force re-processing
            # If forcing reprocess, log it
            elif args.force_reprocess:
                logger.info("User chose to re-process data.")
                enhanced_df = None  # Ensure re-processing happens

        # --- Processing Steps (if not using existing data) ---
        if enhanced_df is None:
            # Check for PDF directory
            if not os.path.isdir(DEFAULT_PDF_DIR):
                logger.error(f"PDF directory not found: '{DEFAULT_PDF_DIR}'. Please create it and place PDF reports inside.")
                print(f"Error: Directory '{DEFAULT_PDF_DIR}' not found. Please create it.")
                return

            # 3. Process Companies (PDF Extraction + Gemini Analysis)
            extracted_results = process_companies(original_df, DEFAULT_PDF_DIR, gemini_model)

            # 4. Integrate Data
            enhanced_df = integrate_data(original_df, extracted_results)

            logger.info(f"Action classifications obtained directly from Gemini LLM.")

            # 5. Save Enhanced Data
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)

        # --- Recommendation Step ---
        if enhanced_df is not None and not enhanced_df.empty:
            if args.company:
                logger.info(f"Attempting to generate recommendations for: {args.company}")
                get_recommendations(args.company, enhanced_df, gemini_model)
            else:
                # No specific company provided, generate for all companies in the dataset
                all_companies = enhanced_df['Name'].unique()
                logger.info(f"No company specified via --company arg. Generating recommendations for all {len(all_companies)} companies found.")
                for company_name in all_companies:
                    logger.info(f"--- Generating recommendations for: {company_name} ---")
                    get_recommendations(company_name, enhanced_df, gemini_model)
                    logger.info(f"--- Finished recommendations for: {company_name} ---")

        else:
            logger.error("Enhanced dataset is empty or could not be created. Cannot proceed to recommendations.")

        logger.info("Pipeline execution finished.")

    except (ValueError, FileNotFoundError) as e:  # Catch configuration/setup errors
        logger.critical(f"Pipeline failed due to configuration or file error: {e}")
        print(f"Error: {e}. Please check your setup (API key, file paths) and try again.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)  # Log full traceback
        print(f"An unexpected error occurred. Check logs for details.")


if __name__ == "__main__":
    main()
