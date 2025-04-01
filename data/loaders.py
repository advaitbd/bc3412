import os
import pandas as pd
import fitz  # PyMuPDF
import logging

def load_excel_data(filepath):
    """Load data from an Excel file."""
    try:
        df = pd.read_excel(filepath)
        logging.info(f"Successfully loaded data from {filepath}. Shape: {df.shape}")

        # Basic validation - Check for 'Company Name' column
        if 'Name' not in df.columns:
            logging.error(f"'Name' column not found in {filepath}. Please ensure it exists.")
            raise ValueError("Missing 'Name' column in Excel file.")

        return df
    except FileNotFoundError:
        logging.error(f"Error: Excel file not found at {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading Excel file {filepath}: {e}")
        raise

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file."""
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
        if len(text.strip()) < 100:  # Arbitrary threshold for potentially empty/corrupt PDFs
            logging.warning(f"Very little text extracted from {os.path.basename(pdf_path)}. Check PDF content.")

        return text
    except Exception as e:
        logging.error(f"Error reading PDF file {os.path.basename(pdf_path)}: {e}")
        return None
