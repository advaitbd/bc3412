import logging
import pandas as pd
import numpy as np
from config.settings import ENHANCED_EXTRACTION_PROMPT, ACTION_CATEGORIES
from services.gemini_service import get_gemini_response
from analysis.parser import parse_gemini_output
import os

def get_gemini_extraction(text, company_name, company_data, client, model):
    """Extract structured information from report text using Gemini with existing company context."""
    if not text:
        logging.warning(f"No text provided for Gemini extraction for {company_name}.")
        return parse_gemini_output("") # Return default structure

    if not client or not model:
         logging.error(f"Gemini client/model not available for extraction for {company_name}.")
         return parse_gemini_output("")

    # Convert company data to a formatted string to include in prompt
    company_context = ""
    if isinstance(company_data, pd.Series):
        # Format existing company data for the prompt
        for key, value in company_data.items():
            if pd.notna(value) and key != 'Name':  # Skip NaN values and Name (already included)
                company_context += f"{key}: {value}\n"

    # Prepare arguments for formatting
    format_args = {
        'company_name': company_name,
        'company_context': company_context,  # Add existing company data
        'text': text[:800000],  # Apply slicing here
        'action_categories_list': ', '.join(ACTION_CATEGORIES)  # Generate list string
    }

    try:
        # Update prompt template in config/settings.py to include company_context
        prompt = ENHANCED_EXTRACTION_PROMPT.format(**format_args)

        logging.info(f"Sending request to Gemini for {company_name}...")
        # Log only a snippet of the potentially huge prompt
        logging.debug(f"Gemini Prompt Snippet for {company_name}:\n{prompt[:500]}...")

        extracted_text = get_gemini_response(prompt, client, model)
        logging.info(f"Received response from Gemini for {company_name}.")

        if not extracted_text:
            logging.warning(f"Gemini returned no content for {company_name}.")
            return parse_gemini_output("")

        # Log snippet of raw response for debugging parsing issues
        logging.debug(f"Raw Gemini Response Snippet for {company_name}:\n{extracted_text[:500]}...")

        # Basic check can be removed if parser handles non-JSON well
        # expected_sections = ["Executive Summary", ...] # Maybe remove this check

        parsed_data = parse_gemini_output(extracted_text)
        # Add company name if parser doesn't
        if 'Name' not in parsed_data:
            parsed_data['Name'] = company_name
        return parsed_data

    except KeyError as e:
         # Catch formatting errors specifically
         logging.error(f"KeyError during prompt formatting for {company_name}: {e}. Check prompt string and arguments.")
         logging.error(f"Available format args: {list(format_args.keys())}")
         return parse_gemini_output("")
    except Exception as e:
        logging.error(f"Error during Gemini extraction or parsing for {company_name}: {e}", exc_info=True)
        return parse_gemini_output("") # Return default structure

def process_companies(df, pdf_dir, client, model):
    """Process each company's PDF report and extract structured data."""
    extracted_data_list = []
    total_companies = len(df)
    processed_count = 0

    for index, row in df.iterrows():
        company_name = row['Name']
        logging.info(f"Processing {company_name} ({processed_count + 1}/{total_companies})...")

        # Pass the entire row data to the extraction function
        company_data = row  # This contains all existing Excel data for this company

        # Construct PDF path based on exact company name
        pdf_filename = f"{company_name}.pdf"
        pdf_path = os.path.join(pdf_dir, pdf_filename)

        # Extract text
        from data.loaders import extract_text_from_pdf
        report_text = extract_text_from_pdf(pdf_path)

        if report_text is None:
            logging.warning(f"Skipping Gemini extraction for {company_name} due to PDF read error or missing file.")
            # Create a record with NaNs/False but keep company name for merging
            llm_results = parse_gemini_output("")
        else:
            # Get structured data from Gemini, passing the company data
            llm_results = get_gemini_extraction(report_text, company_name, company_data, client, model)

        # Add company name to the results for merging
        llm_results['Name'] = company_name
        extracted_data_list.append(llm_results)
        processed_count += 1

    logging.info(f"Finished processing {processed_count} companies.")
    return extracted_data_list
