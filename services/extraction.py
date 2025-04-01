# services/extraction.py
import logging
import pandas as pd
import numpy as np
from config.settings import ENHANCED_EXTRACTION_PROMPT
from services.gemini_service import get_gemini_response
from analysis.parser import parse_gemini_output

def get_gemini_extraction(text, company_name, gemini_model):
    """Extract structured information from report text using Gemini."""
    if not text:
        logging.warning(f"No text provided for Gemini extraction for {company_name}.")
        # Return dictionary with NaNs and False for actions
        parsed_data = parse_gemini_output("")
        return parsed_data

    # Fill the prompt template with company name and text
    prompt = ENHANCED_EXTRACTION_PROMPT.format(company_name=company_name, text=text[:800000])

    try:
        logging.info(f"Sending request to Gemini for {company_name}...")
        extracted_text = get_gemini_response(prompt, gemini_model)
        logging.info(f"Received response from Gemini for {company_name}.")

        if not extracted_text:
            logging.warning(f"Gemini returned no content for {company_name}.")
            parsed_data = parse_gemini_output("")  # Return empty structure
            return parsed_data

        logging.debug(f"Raw Gemini Response for {company_name}:\n{extracted_text}")  # Log the raw response for debugging

        # Basic check of response format
        expected_sections = ["Executive Summary:", "Strategic Priorities", "Financial Commitments",
                            "Identified Risks", "Sustainability Milestones", "Action Classifications"]

        if not all(s in extracted_text for s in expected_sections):
            logging.warning(f"Gemini response for {company_name} might be incomplete or wrongly formatted:\n{extracted_text[:500]}...")

        parsed_data = parse_gemini_output(extracted_text)
        return parsed_data

    except Exception as e:
        logging.error(f"Error calling Gemini API for {company_name}: {e}")
        # Return dictionary with NaNs and False for actions in case of API error
        parsed_data = parse_gemini_output("")
        return parsed_data

def process_companies(df, pdf_dir, gemini_model):
    """Process each company's PDF report and extract structured data."""
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
        from data.loaders import extract_text_from_pdf
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
