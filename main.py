import os
import argparse
import logging
import pandas as pd
import inquirer
from config.settings import DEFAULT_EXCEL_PATH, DEFAULT_PDF_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_OUTPUT_CSV
from utils.logging_utils import setup_logging
from data.loaders import load_excel_data, extract_text_from_pdf
from data.savers import save_enhanced_data
from services.gemini_service import configure_gemini
from services.extraction import process_companies
from analysis.integrator import integrate_data
from analysis.recommendations import get_recommendations

def main():
    """Main function to run the data pipeline."""
    parser = argparse.ArgumentParser(description='Energy Transition Data Pipeline with Risk Assessment')
    parser.add_argument('-f', '--force-reprocess', action='store_true',
                        help='Force reprocessing of PDFs, ignoring existing enhanced_dataset.csv')
    parser.add_argument('-c', '--company', type=str, default=None,
                        help='Specify the company name for which to generate recommendations')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--skip-risk', action='store_true', help='Skip risk assessment in recommendations')
    args = parser.parse_args()

    logger = setup_logging(args.debug)
    logger.info("Starting the Energy Transition Data Pipeline...")

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not set in environment.")
            raise ValueError("Missing GEMINI_API_KEY in environment.")
        client, model = configure_gemini(api_key)

        # Determine whether to use existing enhanced dataset
        enhanced_data_exists = os.path.exists(DEFAULT_OUTPUT_CSV)
        enhanced_df = None

        # Interactive CLI flow
        if not args.force_reprocess and enhanced_data_exists:
            questions = [
                inquirer.List('action',
                    message="Enhanced dataset already exists. What would you like to do?",
                    choices=[
                        ('Use existing enhanced dataset', 'use_existing'),
                        ('Regenerate enhanced dataset', 'regenerate'),
                    ],
                ),
            ]
            answers = inquirer.prompt(questions)
            use_existing = (answers['action'] == 'use_existing')
        else:
            use_existing = False

        # Load the original Excel data
        original_df = load_excel_data(DEFAULT_EXCEL_PATH)

        # Process based on user choice
        if enhanced_data_exists and use_existing:
            logger.info(f"Loading existing enhanced data from {DEFAULT_OUTPUT_CSV}")
            try:
                enhanced_df = pd.read_csv(DEFAULT_OUTPUT_CSV)
                if 'Name' not in enhanced_df.columns:
                    logger.warning("Existing CSV seems incomplete. Missing 'Name' column. Re-processing.")
                    enhanced_df = None
                else:
                    logger.info("Successfully loaded existing enhanced data.")
            except Exception as e:
                logger.error(f"Failed to load existing enhanced data: {e}. Re-processing.")
                enhanced_df = None

        # Generate enhanced dataset if needed
        if enhanced_df is None:
            if not os.path.isdir(DEFAULT_PDF_DIR):
                logger.error(f"PDF directory not found: '{DEFAULT_PDF_DIR}'. Please create it.")
                print(f"\nError: Directory '{DEFAULT_PDF_DIR}' not found.")
                return

            print("\nProcessing company reports. This may take some time...")
            extracted_results = process_companies(original_df, DEFAULT_PDF_DIR, client, model)
            enhanced_df = integrate_data(original_df, extracted_results)
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)
            print(f"\nEnhanced dataset created and saved to: {DEFAULT_OUTPUT_CSV}")

        # Generate recommendations
        if args.company:
            logger.info(f"Generating recommendations for: {args.company}")
            if args.company not in enhanced_df['Name'].values:
                print(f"\nError: Company '{args.company}' not found in the dataset.")
                print("Available companies:")
                for name in sorted(enhanced_df['Name'].unique()):
                    print(f"  - {name}")
                return

            get_recommendations(args.company, enhanced_df, client, model)
            # Save the updated enhanced dataset with any new country information
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)

        else:
            # Prompt user to select a company if none specified
            companies = sorted(enhanced_df['Name'].unique())
            questions = [
                inquirer.List('company',
                    message="Select a company to generate recommendations for:",
                    choices=companies,
                ),
            ]
            answers = inquirer.prompt(questions)
            selected_company = answers['company']

            logger.info(f"Generating recommendations for: {selected_company}")
            get_recommendations(selected_company, enhanced_df, client, model)
            # Save the updated enhanced dataset with any new country information
            save_enhanced_data(enhanced_df, DEFAULT_OUTPUT_CSV)

        logger.info("Pipeline execution finished.")

    except (ValueError, FileNotFoundError) as e:
        logger.critical(f"Pipeline failed due to configuration or file error: {e}")
        print(f"\nError: {e}. Please check your setup (API key, file paths) and try again.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        print("\nAn unexpected error occurred. Check logs for details.")

if __name__ == "__main__":
    main()
